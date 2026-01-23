import asyncio
import httpx
import uuid
import os
import json
import subprocess
import socket
import base64
import threading
import psutil
import time
from typing import Optional, Dict, List
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509.oid import NameOID

from dotenv import load_dotenv

load_dotenv()

AGENT_URL = os.getenv("AGENT_URL", "https://localhost:8001")
API_KEY_NAME = "X-API-KEY"
API_KEY = os.getenv("API_KEY", "master-secret-key")
JOIN_TOKEN = os.getenv("JOIN_TOKEN") 
NODE_ID = f"node-{uuid.uuid4().hex[:8]}"
ROOT_CA_PATH = os.getenv("ROOT_CA_PATH", "c:/Development/Repos/master_of_puppets/ca/certs/root_ca.crt")
CERT_FILE = f"secrets/{NODE_ID}.crt"
KEY_FILE = f"secrets/{NODE_ID}.key"

# Verify SSL?
VERIFY_SSL = str(ROOT_CA_PATH) if ROOT_CA_PATH and os.path.exists(ROOT_CA_PATH) else False

def heartbeat_loop():
    """
    Background thread to send telemetry to Agent.
    """
    print(f"[{NODE_ID}] 💓 Heartbeat Thread Started")
    # Separate client for thread safety
    # Wait for certs to exist (Node init does this)
    while not os.path.exists(CERT_FILE):
        time.sleep(1)
        
    with httpx.Client(
        verify=VERIFY_SSL, 
        cert=(CERT_FILE, KEY_FILE)
    ) as client:
        while True:
            try:
                stats = {
                    "cpu": psutil.cpu_percent(interval=None),
                    "ram": psutil.virtual_memory().percent
                }
                # Use X-Node-ID header if we have one, or just let server use IP
                # We send NODE_ID to allow detailed tracking
                client.post(
                    f"{AGENT_URL}/heartbeat", 
                    json=stats, 
                    headers={"X-Node-ID": NODE_ID, API_KEY_NAME: API_KEY},
                    timeout=5.0
                )
            except Exception as e:
                print(f"[Heartbeat] Failed: {e}")
            
            time.sleep(30)

class Node:
    def __init__(self, agent_url: str, node_id: str):
        self.agent_url = agent_url
        self.node_id = node_id
        self.join_token = JOIN_TOKEN
        self.cert_file = CERT_FILE
        self.key_file = KEY_FILE
        self.verify_key_path = "secrets/verification.key"
        os.makedirs("secrets", exist_ok=True)
        
        # Self-Bootstrap Trust from Token (Container-Native)
        self.bootstrap_trust()
        
        # Ensure we have a valid identity (Key + Cert)
        self.ensure_identity()
        
    def bootstrap_trust(self):
        """
        Parses JOIN_TOKEN. If it's an Enhanced Token (JSON), extracts the CA
        and saves it to disk, bypassing the need for host-to-container mounts.
        """
        try:
            # Sanitize token string (remove whitespace/newlines that might creep in via env/yaml)
            top_token = self.join_token.strip()
            print(f"[{self.node_id}] Debug: Checking Token: {top_token[:20]}...")
            
            # Check if it looks like Base64 (Enhanced Token)
            decoded_bytes = base64.b64decode(top_token)
            decoded_str = decoded_bytes.decode('utf-8')
            # strict=False allows control characters like newlines inside strings if they appear
            payload = json.loads(decoded_str, strict=False)
            
            if "t" in payload and "ca" in payload:
                print(f"[{self.node_id}] 📜 Detected Enhanced Token. Bootstrapping Trust...")
                
                # 1. Extract and Save CA
                ca_content = payload["ca"]
                # Ensure it ends with newline
                if not ca_content.endswith("\n"):
                    ca_content += "\n"
                    
                root_ca_dest = "secrets/root_ca.crt"
                with open(root_ca_dest, "w") as f:
                    f.write(ca_content)
                
                # Update Globals/Members
                global ROOT_CA_PATH, VERIFY_SSL
                ROOT_CA_PATH = os.path.abspath(root_ca_dest)
                
                # STRICT mTLS: Always verify against Bootstrap CA
                VERIFY_SSL = ROOT_CA_PATH
                print(f"[{self.node_id}] 🔒 Strict mTLS Active. CA: {ROOT_CA_PATH}")
                
                # 2. Extract Real Token
                self.join_token = payload["t"]
                
                print(f"[{self.node_id}] ✅ Trust Bootstrapped to {ROOT_CA_PATH}")
            else:
                 print(f"[{self.node_id}] Token payload missing 't' or 'ca'")
                 
            # 3. Fetch Verification Key (Public Key) for Code Signing
            self.fetch_verification_key()
                 
        except Exception as e:
            # Not an enhanced token or parsing failed. safely ignore.
            print(f"[{self.node_id}] DEBUG: Token parse failed, assuming legacy/simple token: {e}")
            pass
            
    def fetch_verification_key(self):
        """Fetches the Public Verification Key from the Server."""
        try:
            # We can use the generic client (trusting Root CA)
            with httpx.Client(verify=VERIFY_SSL) as client:
                resp = client.get(f"{self.agent_url}/api/verification-key", timeout=10)
                if resp.status_code == 200:
                    with open(self.verify_key_path, "wb") as f:
                        f.write(resp.content)
                    print(f"[{self.node_id}] 🔑 Verification Key updated.")
                else:
                    print(f"[{self.node_id}] ⚠️ Failed to fetch Verification Key: {resp.status_code}")
        except Exception as e:
             print(f"[{self.node_id}] ⚠️ Error fetching Verification Key: {e}")
        
    def ensure_identity(self):
        """Checks for Client Cert/Key. If missing, registers with Server via CSR."""
        if os.path.exists(self.cert_file) and os.path.exists(self.key_file):
            print(f"[{self.node_id}] Identity loaded: {self.cert_file}")
            return

        print(f"[{self.node_id}] No identity found. Enrolling with Server...")
        
        # 1. Generate Private Key (RSA 2048)
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        
        # 2. Generate CSR
        csr = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, self.node_id),
        ])).sign(key, hashes.SHA256())
        
        csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode()
        
        # 3. Register with Server (Exchange Token + CSR for Cert)
        try:
             # Use a generic client for registration (Verification CA trusted)
             with httpx.Client(verify=VERIFY_SSL) as client:
                 payload = {
                     "client_secret": self.join_token,
                     "hostname": self.node_id,
                     "csr_pem": csr_pem
                 }
                 resp = client.post(f"{self.agent_url}/auth/register", json=payload)
                 resp.raise_for_status()
                 data = resp.json()
                 
                 client_cert_pem = data["client_cert_pem"]
                 
                 # 4. Save to Disk
                 with open(self.key_file, "wb") as f:
                     f.write(key.private_bytes(
                         encoding=serialization.Encoding.PEM,
                         format=serialization.PrivateFormat.TraditionalOpenSSL,
                         encryption_algorithm=serialization.NoEncryption()
                     ))
                 with open(self.cert_file, "w") as f:
                     f.write(client_cert_pem)
                     
                 print(f"[{self.node_id}] ✅ Enrollment Successful! Certificate Saved.")
                 
        except Exception as e:
            print(f"[{self.node_id}] ❌ Enrollment Failed: {e}")
            raise e

    async def poll_for_work(self) -> Optional[Dict]:
        try:
            # mTLS Client
            async with httpx.AsyncClient(
                verify=VERIFY_SSL, 
                cert=(self.cert_file, self.key_file)
            ) as client:
                headers = {API_KEY_NAME: API_KEY}
                resp = await client.post(f"{self.agent_url}/work/pull", headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        return data 
                elif resp.status_code != 200:
                     # Only log errors
                     pass
        except Exception as e:
            print(f"[{self.node_id}] Error polling Agent: {e}")
        return None

    def run_python_script(self, guid: str, script_content: str, secrets: Dict = {}) -> Dict:
        temp_filename = f"_temp_job_{guid}.py"
        try:
            with open(temp_filename, "w") as f:
                f.write(script_content)
                
            env_vars = os.environ.copy()
            env_vars.update(secrets)
            
            print(f"[{self.node_id}] Spawning subprocess for job {guid}...")
            result = subprocess.run(
                ["python", temp_filename],
                env=env_vars,
                capture_output=True,
                text=True,
                timeout=30 
            )
            
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out"}
        except Exception as e:
            return {"error": f"Execution failed: {e}"}
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    async def execute_task(self, job: Dict):
        guid = job["guid"]
        task_type = job.get("task_type", "web_task")
        payload = job["payload"]
        
        print(f"[{self.node_id}] Executing Job {guid} [{task_type}]")
        
        result_data = {}
        success = False

        if task_type == "python_script":
            script = payload.get("script_content")
            secrets = payload.get("secrets", {})
            signature = payload.get("signature")

            if not script:
                 result_data = {"error": "No script_content provided"}
            elif not signature:
                 if INSECURE_NODE:
                     print(f"[{self.node_id}] ⚠️ Unsigned Job Allowed (Insecure Mode)")
                 else:
                     print(f"[{self.node_id}] ❌ CRITICAL: Unsigned Job Rejected. Signature is MANDATORY.")
                     await self.report_result(guid, False, {"error": "Security Check Failed: Signature Missing (Mandatory)"})
                     return
            else:
                 # Check Signature
                 if signature:
                     if not os.path.exists(self.verify_key_path):
                         print(f"[{self.node_id}] ❌ CRITICAL: Verification Key missing. Cannot verify signature.")
                         await self.report_result(guid, False, {"error": "Security Check Failed: Verification Key missing"})
                         return
                         
                     try:
                         with open(self.verify_key_path, "rb") as f:
                             public_key_bytes = f.read()
                             public_key = serialization.load_pem_public_key(public_key_bytes)
                             
                         sig_bytes = base64.b64decode(signature)
                         public_key.verify(sig_bytes, script.encode('utf-8'))
                         print(f"[{self.node_id}] ✅ Signature Verified for Job {guid}")
                     except Exception as e:
                         print(f"[{self.node_id}] ❌ Signature Verification FAILED: {e}")
                         await self.report_result(guid, False, {"error": "Signature Verification Failed"})
                         return
                 
                 exec_result = self.run_python_script(guid, script, secrets)
                 result_data = exec_result
                 success = (exec_result.get("exit_code") == 0)
                
        else:
            print(f"[{self.node_id}] Simulating Web Task")
            await asyncio.sleep(2)
            success = True
            result_data = {"processed": True}
        
        await self.report_result(guid, success, result_data)

    async def report_result(self, guid: str, success: bool, result: Dict):
        try:
            async with httpx.AsyncClient(
                verify=VERIFY_SSL,
                cert=(self.cert_file, self.key_file)
            ) as client:
                await client.post(
                    f"{self.agent_url}/work/{guid}/result",
                    json={"success": success, "result": result},
                    headers={API_KEY_NAME: API_KEY}
                )
            print(f"[{self.node_id}] Reported result for {guid}")
        except Exception as e:
            print(f"[{self.node_id}] Failed to report result: {e}")

    async def start(self):
        print(f"[{self.node_id}] Starting Work Loop...")
        while True:
            job = await self.poll_for_work()
            if job:
                await self.execute_task(job)
            else:
                await asyncio.sleep(5)

def main():
    print(f"🚀 Environment Node Started ({os.getpid()})")
    
    if not VERIFY_SSL:
        print("⚠️  WARNING: Running with SSL Verification DISABLED")
    else:
        print(f"🔒 Secure Mode Active. Trust Root: {VERIFY_SSL}")

    # Debug: Print Active Mounts
    mounts = [k for k in os.environ.keys() if k.startswith("MOUNT_")]
    if mounts:
        print(f"📁 Active System Mounts: {', '.join(mounts)}")
    else:
        print("📁 No System Mounts detected.")

    node = Node(AGENT_URL, NODE_ID)

    # Start Heartbeat Thread (After Node init ensures certs)
    hb_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    hb_thread.start()

    try:
        asyncio.run(node.start())
    except KeyboardInterrupt:
        print("Node stopping...")

if __name__ == "__main__":
    main()

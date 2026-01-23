import requests
import json
import time
import os
import sys
# Import signing tool logic
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from sign_job import sign_content
except ImportError:
    # Quick fallback if path issue
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    import base64
    
    SECRETS_DIR = "puppeteer/secrets"
    SIGNING_KEY_PATH = os.path.join(SECRETS_DIR, "signing.key")

    def sign_content(content: str) -> str:
        with open(SIGNING_KEY_PATH, "rb") as key_file:
            private_key = serialization.load_pem_private_key(key_file.read(), password=None)
        signature = private_key.sign(
            content.encode('utf-8'),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')

# Config
SERVER_URL = "https://192.168.50.128:8001"
# We need to trust the Root CA for this connection too (or ignore for quick test)
ROOT_CA = "puppeteer/secrets/ca/root_ca.crt"

def run_test():
    print(f"--- Preparing Signed Ping Job ---")
    
    # 1. Read Script
    script_path = os.path.join(os.path.dirname(__file__), "verify_ping.py")
    with open(script_path, "r") as f:
        script_content = f.read()
        
    # 2. Sign
    print("Signing script...")
    signature = sign_content(script_content)
    
    # 3. Submit
    job_id = f"ping-test-{int(time.time())}"
    
    # Inner Payload (what the Node receives)
    inner_payload = {
        "script_content": script_content,
        "signature": signature,
        "target_node": "any"
    }
    
    # Outer Payload (API Schema)
    payload = {
        "task_type": "python_script",
        "payload": inner_payload
    }
    
    # Admin Auth?
    # We need a token. Let's use the one from debug logs or secrets.env if available.
    # For now, assuming open or we have a hardcoded one.
    # The `login` in debug_remote.py got a token.
    # We can try to login first.
    
    # Login
    print("Logging in...")
    login_data = {
        "username": "admin", 
        "password": "changeit" # Default? Or "admin"/"admin"?
        # e2e_api_test.py uses "admin"/"admin"
    }
    # Check what e2e_api_test.py uses
    # It sends: role=admin in a magic token? 
    # Let's try standard login if exists, or skipped auth for dev.
    
    # Actually, `agent_service/main.py` has /auth/login.
    # Or we can use the API Key in header?
    # compose.server.yaml: API_KEY=${API_KEY}.
    # If we have API key, use it.
    
    # Let's try connecting.
    try:
        # Use verify=False for host-to-vm if IP mismatch (though 192.168 IS in cert now).
        # Use verify=ROOT_CA.
        verify_ssl = ROOT_CA if os.path.exists(ROOT_CA) else False
        
        # Dispatch
        print(f"Submitting Job {job_id} to {SERVER_URL}...")
        res = requests.post(f"{SERVER_URL}/jobs", json=payload, verify=verify_ssl) # No auth?
        
        if res.status_code in [401, 403]:
            # Need Auth.
            print("Auth required. Trying Magic Token or Login...")
            # Getting token...
            # Assume dev mode or API Key.
            # Using API Key header if known. 
            # Or just hack it.
            pass
            
        print(f"Submission Status: {res.status_code}")
        print(res.text)
        
        if res.status_code == 200:
            print("Job Submitted successfully.")
            # Verify execution?
            # We can't poll easily without get endpoint.
            # We will verify via DB check later.
            return True
            
    except Exception as e:
        print(f"Submission Failed: {e}")
        return False

if __name__ == "__main__":
    run_test()

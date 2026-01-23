import os
import subprocess
import time
import httpx
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Configuration
SERVER_URL = "https://localhost:8001"
USERNAME = "admin"
PASSWORD = "admin"

def generate_keys():
    print("Generating Ed25519 Keys...")
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Serialize Public Key to PEM for distribution
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open("verification.key", "wb") as f:
        f.write(pem_public)
        
    return private_key

def distribute_keys():
    print("Distributing verification.key to nodes...")
    # Get node container names
    cmd = ["podman", "ps", "-q", "--filter", "name=node"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    container_ids = result.stdout.strip().splitlines()
    
    if not container_ids:
        print("ERROR: No node containers found!")
        exit(1)

    for cid in container_ids:
        print(f"  -> Copying to {cid}")
        # Copy to /app/secrets/verification.key inside container
        subprocess.run(["podman", "cp", "verification.key", f"{cid}:/app/secrets/verification.key"], check=True)

def sign_payload(private_key, script_content):
    signature = private_key.sign(script_content.encode('utf-8'))
    return base64.b64encode(signature).decode('utf-8')

def main():
    # 1. Setup Keys
    private_key = generate_keys()
    distribute_keys()
    
    # 2. Login
    print("Authenticating to Server...")
    try:
        client = httpx.Client(verify=False) # Bypass SSL for test
        resp = client.post(f"{SERVER_URL}/auth/login", data={"username": USERNAME, "password": PASSWORD})
        resp.raise_for_status()
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
    except Exception as e:
        print(f"Login Failed: {e}")
        exit(1)
    
    # 3. Submit Valid Job (Safe)
    print("\n--- TEST CASE 1: Valid Signed Job (create test.md) ---")
    script_valid = "with open('test.md', 'w') as f: f.write('success')"
    signature_valid = sign_payload(private_key, script_valid)
    
    payload_valid = {
        "task_type": "python_script",
        "payload": {
            "script_content": script_valid,
            "signature": signature_valid
        }
    }
    
    resp = client.post(f"{SERVER_URL}/jobs", json=payload_valid, headers=headers)
    print(f"Job 1 Submitted: {resp.status_code}")
    
    # 4. Submit Invalid Job (Unsigned/Bad Sig)
    print("\n--- TEST CASE 2: Invalid Signature Job (create test2.md) ---")
    script_invalid = "with open('test2.md', 'w') as f: f.write('fail')"
    # Create a signature for DIFFERENT content, so it's a valid sig format but invalid for this content
    fake_sig = sign_payload(private_key, "malicious content") 
    
    payload_invalid = {
        "task_type": "python_script",
        "payload": {
            "script_content": script_invalid,
            "signature": fake_sig
        }
    }
    
    resp = client.post(f"{SERVER_URL}/jobs", json=payload_invalid, headers=headers)
    print(f"Job 2 Submitted: {resp.status_code}")

    # 5. Wait for execution
    print("\nWaiting 20s for job propagation and execution...")
    time.sleep(20)
    
    # 6. Verify Results
    print("\n--- VALIDATION ---")
    
    # Get CIDs again
    cmd = ["podman", "ps", "-q", "--filter", "name=node"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    container_ids = result.stdout.strip().splitlines()

    success_count_valid = 0
    failure_count_invalid = 0

    for cid in container_ids:
        print(f"Checking Node Container {cid}...")
        
        # Check test.md (Valid Job)
        res_valid = subprocess.run(["podman", "exec", cid, "ls", "test.md"], capture_output=True, text=True)
        if res_valid.returncode == 0:
            print(f"  [INFO] test.md found (Job Correctly Executed on this node)")
            success_count_valid += 1
        else:
            print(f"  [INFO] test.md NOT found (Job likely executed on other node)")

        # Check test2.md (Invalid Job)
        res_invalid = subprocess.run(["podman", "exec", cid, "ls", "test2.md"], capture_output=True, text=True)
        if res_invalid.returncode != 0:
            print(f"  [PASS] test2.md NOT found (Invalid Job Rejected)")
        else:
            print(f"  [FAIL] test2.md FOUND! (Security Bypass Detected!)")
            failure_count_invalid += 1

    # Final Verdict
    print(f"\nSummary: Valid Jobs Executed: {success_count_valid}/{len(container_ids)} (Expected >= 1)")
    print(f"Summary: Invalid Jobs Executed: {failure_count_invalid}/{len(container_ids)} (Expected 0)")
    
    if success_count_valid >= 1 and failure_count_invalid == 0:
        print("\n[ALL TESTS PASSED] RCE Signature Verification is Active.")
    else:
        print("\n[TESTS FAILED] Security Regression Persists or Job System Failed.")

if __name__ == "__main__":
    main()

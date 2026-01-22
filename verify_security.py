import os
import requests
import json
import base64
import subprocess
import time
import shutil

# Config
SERVER_URL = "https://localhost:8001"
SECRETS_DIR = "secrets"
VERIFY_KEY_PATH = "secrets/verification.key"

def read_secrets():
    secrets = {}
    with open("secrets.env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                secrets[k] = v
    return secrets

def test_key_distribution():
    print("--- Testing Key Distribution ---")
    
    # Simulate installer fetching key
    try:
        if os.path.exists("test_verification.key"):
            os.remove("test_verification.key")
            
        print(f"Fetching key from {SERVER_URL}/api/verification-key...")
        # curl -k because we are testing the endpoint, normally we use CA
        resp = requests.get(f"{SERVER_URL}/api/verification-key", verify=False)
        
        if resp.status_code == 200:
             content = resp.text
             print(f"Received Key ({len(content)} bytes)")
             if "PUBLIC KEY" in content:
                 print("✅ Valid Public Key Format")
                 with open("test_verification.key", "w") as f:
                     f.write(content)
             else:
                 print("❌ Invalid Key Content")
        else:
             print(f"❌ Failed to fetch key: {resp.status_code}")
             
    except Exception as e:
        print(f"❌ Error: {e}")

def get_node_status():
    # Helper to check if node.py would run
    # Since we can't easily unit test the running container from here without complex setup,
    # we will rely on key distribution test + manual code review valid.
    # But we CAN try to run a simulation of the verification logic if we import it.
    pass

def main():
    print("🔒 Security Verification Suite")
    test_key_distribution()
    
    # Cleanup
    if os.path.exists("test_verification.key"):
        os.remove("test_verification.key")

if __name__ == "__main__":
    main()

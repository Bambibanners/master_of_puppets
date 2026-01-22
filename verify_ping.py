import os
import requests
import json

# Determined from environment or hardcoded for test
AGENT_URL = os.environ.get("AGENT_URL", "https://172.28.240.1:8001")
NODE_ID = os.environ.get("NODE_ID", "unknown-node")

# Endpoint
PING_URL = f"{AGENT_URL}/api/test/ping"

print(f"[{NODE_ID}] Pinging {PING_URL}...")

payload = {
    "node_id": NODE_ID,
    "message": "Strict mTLS Verification Successful!"
}

try:
    # Use the same SSL context as the node process (if Python trusted system store)
    # The Node environment sets REQUESTS_CA_BUNDLE to point to the root CA if needed?
    # Or we explicitly rely on 'verify=False' being FORBIDDEN by user requirements?
    # User said: "containers to talk to the main server via Mtls at all times"
    # But this is inside the python script job. 
    # The job inherits the container environment.
    # The container wraps the node process.
    # The USER SCRIPT runs in the same container.
    # We should use the Root CA at /app/secrets/root_ca.crt
    
    ca_path = "/app/secrets/root_ca.crt"
    if not os.path.exists(ca_path):
        print("WAARNING: Root CA not found at expected path. Using default stores.")
        verify = True
    else:
        verify = ca_path

    res = requests.post(PING_URL, json=payload, verify=verify, timeout=10)
    print(f"Ping Status: {res.status_code}")
    print(f"Response: {res.text}")
    
except Exception as e:
    print(f"Ping Failed: {e}")
    raise e

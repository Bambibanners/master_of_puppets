import requests
import time
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Use IP from args or hardcode E2E IP
BASE_URL = "https://192.168.50.128:8001"
LOGIN_URL = f"{BASE_URL}/auth/login"
JOBS_URL = f"{BASE_URL}/jobs"
NODES_URL = f"{BASE_URL}/nodes"

def get_token():
    payload = {"username": "admin", "password": "admin"}
    try:
        res = requests.post(LOGIN_URL, data=payload, verify=False, timeout=5)
        if res.status_code == 200:
            return res.json()["access_token"]
        else:
            print(f"Login Failed: {res.text}")
            return None
    except Exception as e:
        print(f"Login Exception: {e}")
        return None

def get_nodes(token):
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(NODES_URL, headers=headers, verify=False)
    if res.status_code == 200:
        return res.json()
    return []

def submit_job(token, node_id=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    script_content = f"""
import time
import datetime
import os
LOG_FILE = "/tmp/hello_world_test.md"
with open(LOG_FILE, "a") as f:
    f.write(f"Hello World via API (Node {node_id}) - {{datetime.datetime.now()}}\\n")
"""
    script_payload = {
        "script_content": script_content
    }
    
    data = {
        "task_type": "python_script",
        "payload": script_payload
    }
    if node_id:
        data["node_id"] = node_id
    
    print(f"Submitting Job to {node_id or 'Any'}...")
    res = requests.post(JOBS_URL, json=data, headers=headers, verify=False)
    if res.status_code == 200:
        print(f"Job Submitted: {res.json().get('guid')}")
        return res.json().get("guid")
    else:
        print(f"Job Submission Failed: {res.text}")
        return None

def submit_gui_sim_job(token):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Simulate a job that writes to hello_world_gui.md
    script_content = """
import os
os.system('echo Hello World via GUI >> /tmp/hello_world_gui.md')
"""
    data = {
        "task_type": "python_script",
        "payload": {"script_content": script_content}
    }
    requests.post(JOBS_URL, json=data, headers=headers, verify=False)

if __name__ == "__main__":
    token = get_token()
    if token:
        print("Broadcasting 8 jobs blindly to ensure coverage...")
        for i in range(8):
            submit_job(token)
            time.sleep(0.2)
            
        print("Submitting Simulated GUI Jobs...")
        for i in range(4):
            submit_gui_sim_job(token)
            time.sleep(0.2)

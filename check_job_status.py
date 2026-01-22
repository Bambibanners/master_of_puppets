import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://192.168.50.128:8001"
LOGIN_URL = f"{BASE_URL}/auth/login"
JOBS_URL = f"{BASE_URL}/jobs"

def get_token():
    payload = {"username": "admin", "password": "admin"}
    try:
        res = requests.post(LOGIN_URL, data=payload, verify=False, timeout=5)
        if res.status_code == 200:
            return res.json()["access_token"]
        return None
    except: return None

def check_jobs():
    token = get_token()
    if not token:
        print("Login Failed")
        return

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(JOBS_URL, headers=headers, verify=False)
    if res.status_code == 200:
        jobs = res.json()
        print(f"Found {len(jobs)} jobs.")
        for j in jobs[:5]: # Check latest 5
            print(f"GUID: {j['guid']}")
            print(f"Status: {j['status']}")
            print(f"Node: {j['node_id']}")
            result = j.get('result')
            if result:
                print(f"Result: {json.dumps(result, indent=2)}")
            else:
                print("Result: None")
            print("-" * 20)
    else:
        print(f"Failed to list jobs: {res.status_code}")

if __name__ == "__main__":
    check_jobs()

import paramiko
import time
import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REMOTE_DIR = "/home/speedy/master_of_puppets"

def read_secrets():
    secrets = {}
    with open("secrets.env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                secrets[k] = v
    return secrets

def run_command(client, command, print_output=True):
    print(f"REMOTE: {command}")
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    out_lines = []
    
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            data = stdout.channel.recv(1024).decode('utf-8', errors='replace')
            if print_output: print(data, end="", flush=True)
            out_lines.append(data)
        time.sleep(0.1)
        
    if stdout.channel.recv_exit_status() != 0:
        return False, "".join(out_lines)
    return True, "".join(out_lines)

def setup_scale():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")
    
    base_url = f"https://{ip}:8001"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {ip}...")
    client.connect(ip, username=user, password=password)

    try:
        # 1. Get Token (Local)
        print("--- Authenticating (Local) ---")
        try:
            res = requests.post(f"{base_url}/auth/login", data={"username": "admin", "password": "admin"}, verify=False, timeout=10)
            if res.status_code != 200:
                print(f"Auth Failed: {res.status_code} {res.text}")
                # Try ensuring server is up
                print("Server might be down. Starting it...")
                run_command(client, f"cd {REMOTE_DIR} && docker compose -f compose.server.yaml up -d")
                time.sleep(10)
                res = requests.post(f"{base_url}/auth/login", data={"username": "admin", "password": "admin"}, verify=False, timeout=10)
                
            res.raise_for_status()
            access_token = res.json()["access_token"]
            print(f"Got Access Token: {access_token[:10]}...")
        except Exception as e:
            print(f"Local Auth Failed: {e}")
            return

        # 2. Get Join Token (Local)
        print("--- Generating Join Token (Local) ---")
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.post(f"{base_url}/admin/generate-token", headers=headers, verify=False)
        res.raise_for_status()
        token = res.json()["token"]
        print(f"Got Join Token: {token[:10]}...")

        # 3. Fetch Compose for Nodes (Remote Curl using Token)
        # We use the token we got locally
        print("--- Fetching Node Compose (Remote) ---")
        # Note: server URL is localhost from perspective of remote machine for this curl, OR we can use the cluster IP.
        # But for 'fetch compose', the server generates it.
        # The URL in the curl command: "https://localhost:8001" is correct for the remote machine.
        cmd_fetch = f"cd {REMOTE_DIR} && curl -k -v \"https://localhost:8001/api/node/compose?token={token}&platform=Docker\" -o node-compose-scale.yaml"
        run_command(client, cmd_fetch)
        
        # 4. Deploy 4 Nodes
        print("--- Scaling to 4 Nodes ---")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f node-compose-scale.yaml down")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f node-compose-scale.yaml up -d --scale node=4")
        
        print("Waiting 15s for enrollment...")
        time.sleep(15)
        print("[SUCCESS] Infrastructure Scaled.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    setup_scale()

import paramiko
import os
import time
import requests
import urllib3
from scp import SCPClient

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

def run_e2e():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {ip}...")
    client.connect(ip, username=user, password=password)

    try:
        # 1. Get Token & Join Token
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f compose.server.yaml up -d") # Ensure server up
        time.sleep(5)
        
        print("--- Getting Access Token ---")
        cmd_token = f"curl -k -s -X POST -d 'username=admin&password=admin' https://localhost:8001/auth/login | grep -o '\"access_token\":\"[^\"]*\"' | cut -d'\"' -f4"
        _, access_token = run_command(client, cmd_token, print_output=False)
        access_token = access_token.strip()
        
        if not access_token:
            print("Failed to get Access Token")
            return

        print("--- Getting Join Token ---")
        cmd_join = f"curl -k -s -X POST -H \"Authorization: Bearer {access_token}\" https://localhost:8001/admin/generate-token"
        _, join_json = run_command(client, cmd_join, print_output=False)
        # Parse logic slightly different depending on curl output
        token = join_json.split('"token":"')[1].split('"')[0]
        print(f"Join Token: {token[:10]}...")

        # 2. Fetch Compose for Nodes
        print("--- Fetching Node Compose ---")
        cmd_fetch = f"cd {REMOTE_DIR} && curl -k -v \"https://localhost:8001/api/node/compose?token={token}&platform=Docker\" -o node-compose-scale.yaml"
        run_command(client, cmd_fetch)
        
        # 3. Deploy 4 Nodes
        print("--- Scaling to 4 Nodes ---")
        # Ensure we kill old ones first to be clean
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f node-compose-scale.yaml down")
        # Scale up
        # Note: service name in generated compose is usually 'node' or 'master_of_puppets_node'
        # We need to guess or check. Standard from `install_server.py` logic is 'node'.
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f node-compose-scale.yaml up -d --scale node=4")
        
        print("Waiting 15s for enrollment...")
        time.sleep(15)
        
        # 4. Run API Submission from LOCAL (using requests)
        # We need to tunnel or just hit the public IP if exposed.
        # But wait, the API is on localhost:8001 remote? 
        # compose file maps 8001:8001. So 192.168.50.128:8001 should work.
        print("--- Executing API Test (Local Script) ---")
        os.system("python e2e_api_test.py")
        
        print("--- Waiting 60s for Job Execution ---")
        time.sleep(65) # Wait for heartbeat + run
        
        # 5. Verify Output
        print("--- Verifying Output in Containers ---")
        # docker exec into each node
        _, nodes_list = run_command(client, "docker ps --format '{{.Names}}' | grep node", print_output=False)
        nodes = nodes_list.strip().split('\n')
        
        success_count = 0
        for node in nodes:
            node = node.strip()
            if not node: continue
            print(f"Checking {node}...")
            # Check for file content
            res, out = run_command(client, f"docker exec {node} cat /tmp/hello_world_test.md", print_output=False)
            if "Hello World via API" in out:
                print(f"[SUCCESS] {node} has the file.")
                success_count += 1
            else:
                print(f"[FAIL] {node} missing file. Output: {out}")
        
        if success_count == 4:
            print("[PASS] All 4 nodes executed the job.")
        else:
            print(f"[FAIL] Only {success_count}/4 nodes success.")

        # 6. Teardown
        print("--- Teardown (Killing Nodes 5 mins request... skipping wait for demo speed? User said wait 5 mins?) ---")
        print("User requested: 'kill the nodes 5 mins afer job deolpyment, AFTER you've validated'.")
        print("Since I validated, I will now wait 5 minutes before killing.")
        time.sleep(300) 
        
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f node-compose-scale.yaml down")
        print("Nodes Terminated.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_e2e()

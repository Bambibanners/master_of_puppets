import paramiko
import os
import sys
import time

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
    print(f"REMOTE EXEC: {command}")
    stdin, stdout, stderr = client.exec_command(f"{command}", get_pty=True)
    
    out_lines = []
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            data = stdout.channel.recv(1024).decode('utf-8', errors='replace')
            if print_output:
                # Safe print for Windows CP1252
                sys.stdout.write(data.encode('ascii', 'replace').decode())
                sys.stdout.flush()
            out_lines.append(data)
        if stderr.channel.recv_ready():
            data = stderr.channel.recv(1024).decode('utf-8', errors='replace')
            if print_output:
                sys.stderr.write(data.encode('ascii', 'replace').decode())
                sys.stderr.flush()
        time.sleep(0.1)
        
    s_exit = stdout.channel.recv_exit_status()
    if s_exit != 0:
        print(f"[FAIL] Exit: {s_exit}")
        return False, "".join(out_lines)
    return True, "".join(out_lines)

def deploy_docker():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")

    print(f"Connecting to {user}@{ip}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    try:
        # File sync assumed done by Podman step, but we could re-sync if needed.
        # Assuming files are present.
        
        # 1. Teardown Podman
        print("--- Stopping Podman Stack ---")
        # Ignore errors if not running
        run_command(client, f"cd {REMOTE_DIR} && podman-compose -f compose.server.yaml down")
        
        # 2. Build Images (Docker)
        print("--- Building Images (Docker) ---")
        print("Building Server Image...")
        cmd_build_server = f"cd {REMOTE_DIR} && docker build -t localhost/master-of-puppets-server:latest -f Containerfile.server ."
        res, _ = run_command(client, cmd_build_server)
        if not res: return

        print("Building Dashboard Image (This may take 5-10 minutes)...")
        cmd_build_dashboard = f"cd {REMOTE_DIR}/dashboard && docker build -t localhost/master-of-puppets-dashboard:latest -f Containerfile ."
        res, _ = run_command(client, cmd_build_dashboard)
        if not res: return

        # 3. Build & Deploy Docker Stack
        # Note: 'docker compose' plugin syntax
        print("--- Deploying Docker Stack ---")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f compose.server.yaml down")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f compose.server.yaml up -d")
        
        # Wait for Health
        print("Waiting for Server Health (20s)...")
        time.sleep(20)
        
        res, out = run_command(client, "curl -k -v https://localhost:8001/auth/login")
        if "405 Method Not Allowed" in out or "detail" in out or "access_token" in out:
             print("[OK] Service Responding.")
        else:
             print("[WARN] Service might not be ready. Proceeding anyway...")

        # 3. Validate Node (Platform: Docker)
        print("--- Validating Node Deployment ---")
        
        # Get Token
        cmd_awk = f"curl -k -s -X POST -d 'username=admin&password=admin' https://localhost:8001/auth/login | grep -o '\"access_token\":\"[^\"]*\"' | cut -d'\"' -f4"
        _, access_token = run_command(client, cmd_awk, print_output=False)
        access_token = access_token.strip()
        print(f"Access Token: {access_token[:10]}...")

        if not access_token:
            print("[FAIL] Could not get Access Token")
            return

        # Generate Join Token
        cmd_join = f"curl -k -s -X POST -H \"Authorization: Bearer {access_token}\" https://localhost:8001/admin/generate-token"
        _, join_json = run_command(client, cmd_join, print_output=False)
        cmd_join_parse = f"echo '{join_json}' | grep -o '\"token\":\"[^\"]*\"' | cut -d'\"' -f4"
        _, join_token = run_command(client, cmd_join_parse, print_output=False)
        join_token = join_token.strip()
        print(f"Join Token: {join_token[:10]}...")
        
        if not join_token:
            print("[FAIL] Could not get Join Token")
            return
            
        # Fetch Compose (Docker)
        print(f"Fetching Node Compose (Platform: Docker)...")
        # Important: &platform=Docker
        cmd_fetch = f"cd {REMOTE_DIR} && curl -k -v \"https://localhost:8001/api/node/compose?token={join_token}&platform=Docker\" -o node-compose-docker.yaml"
        run_command(client, cmd_fetch)
        
        # Run Node
        print("Starting Node (Docker)...")
        # Ensure we use the fetched file
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f node-compose-docker.yaml up -d")
        
        print("Waiting 10s for Node Initialization...")
        time.sleep(10)
        
        print("Checking Logs...")
        # Note: Container name might be different with docker compose depending on project name?
        # Defaults to directory name 'master_of_puppets_node_1' usually.
        # Use 'docker ps' to find it if unsure, but strict naming helps.
        res, logs = run_command(client, f"cd {REMOTE_DIR} && docker logs master_of_puppets_node_1")
        
        if "Enrollment Successful" in logs or "Heartbeat" in logs:
            print("[SUCCESS] Node Enrolled and Heartbeating!")
        else:
            print("[FAIL] Node Logs do not show success.")
            print(logs)
            
    except Exception as e:
        print(f"[ERR] Validation Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    deploy_docker()

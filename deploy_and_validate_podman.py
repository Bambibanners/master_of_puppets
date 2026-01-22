import paramiko
import os
import sys
import time

LOCAL_DIR = os.getcwd()
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
    stdin, stdout, stderr = client.exec_command(f"{command}", get_pty=True) # PTY for buffering output better
    
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
        # Capture remaining output
        return False, "".join(out_lines)
    return True, "".join(out_lines)

def upload_files(client, sftp):
    print(f"Uploading files to {REMOTE_DIR}...")
    run_command(client, f"mkdir -p {REMOTE_DIR}")
    
    excludes = [".git", "venv", "__pycache__", ".idea", "node_modules", "dist", "coverage", ".DS_Store", "jobs.db", "master-of-puppets.db"]
    
    for root, dirs, files in os.walk(LOCAL_DIR):
        # Filter exclusions
        dirs[:] = [d for d in dirs if d not in excludes]
        
        rel_path = os.path.relpath(root, LOCAL_DIR)
        remote_path = os.path.join(REMOTE_DIR, rel_path).replace("\\", "/")
        
        # Create remote dir
        if rel_path != ".":
            try:
                sftp.mkdir(remote_path)
            except IOError:
                pass # Already exists
        
        for file in files:
            if any(file.endswith(ext) for ext in ['.pyc', '.log']): continue
            if file in excludes: continue
            
            local_file = os.path.join(root, file)
            remote_file = os.path.join(remote_path, file).replace("\\", "/")
            
            # Simple timestamp check or just overwrite? Overwrite for safety.
            # print(f"Up: {file}")
            sftp.put(local_file, remote_file)
            
    print("[OK] Upload Complete.")

def deploy_podman():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")

    print(f"Connecting to {user}@{ip}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    sftp = client.open_sftp()
    
    try:
        # 1. Upload
        upload_files(client, sftp)
        
        # 2. Build Images
        print("--- Building Images ---")
        cmd_build_server = f"cd {REMOTE_DIR} && podman build -t localhost/master-of-puppets-server:latest -f Containerfile.server ."
        res, _ = run_command(client, cmd_build_server)
        if not res: return

        # cmd_build_dash = f"cd {REMOTE_DIR} && podman build -t localhost/master-of-puppets-dashboard:latest -f dashboard/Containerfile dashboard/"
        # res, _ = run_command(client, cmd_build_dash)
        # if not res: return
        
        # 3. Deploy Stack
        print("--- Deploying Server Stack ---")
        run_command(client, f"cd {REMOTE_DIR} && podman-compose -f compose.server.yaml down")
        res, _ = run_command(client, f"cd {REMOTE_DIR} && podman-compose -f compose.server.yaml up -d")
        if not res: return
        
        # Wait for Health
        print("Waiting for Server Health (15s)...")
        time.sleep(15)
        # Verify via curl on remote
        res, out = run_command(client, "curl -k -v https://localhost:8001/auth/login")
        if "405 Method Not Allowed" in out or "detail" in out or "access_token" in out or "msg" in out:
             print("[OK] Service Responding.")
        else:
             print("[WARN] Service might not be ready. Proceeding anyway...")
             
        # 4. Validate Node
        print("--- Validating Node Deployment ---")
        
        # Get Token
        cmd_token = f"curl -k -s -X POST -d 'username=admin&password=admin' https://localhost:8001/auth/login"
        _, json_out = run_command(client, cmd_token, print_output=False)
        # Parse token via python one-liner on remote lol or just regex?
        # Let's do it cleaner: extract token using python on remote
        cmd_extract = f"cd {REMOTE_DIR} && python3 -c \"import requests; r = requests.post('https://localhost:8001/auth/login', data={{'username':'admin','password':'admin'}}, verify=False); print(r.json()['access_token'])\""
        # Remote might not have requests installed? 
        # Server image has it, but host? 
        # Let's try simple string slicing with grep/sed/awk if python fails.
        # "access_token":"..."
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
        # Parse join token
        # { "token": "..." }
        cmd_join_parse = f"echo '{join_json}' | grep -o '\"token\":\"[^\"]*\"' | cut -d'\"' -f4"
        _, join_token = run_command(client, cmd_join_parse, print_output=False)
        join_token = join_token.strip()
        print(f"Join Token: {join_token[:10]}...")
        
        # Fetch Compose
        print(f"Fetching Node Compose (Platform: Podman)...")
        cmd_fetch = f"cd {REMOTE_DIR} && curl -k -v \"https://localhost:8001/api/node/compose?token={join_token}&platform=Podman\" -o node-compose.yaml"
        run_command(client, cmd_fetch)
        
        # Run Node
        print("Starting Node...")
        run_command(client, f"cd {REMOTE_DIR} && podman-compose -f node-compose.yaml up -d")
        
        print("Waiting 10s for Node Initialization...")
        time.sleep(10)
        
        print("Checking Logs...")
        res, logs = run_command(client, f"cd {REMOTE_DIR} && podman logs master_of_puppets_node_1")
        
        if "Enrollment Successful" in logs or "Heartbeat" in logs:
            print("[SUCCESS] Node Enrolled and Heartbeating!")
        else:
            print("[FAIL] Node Logs do not show success.")
            print(logs)
            
    except Exception as e:
        print(f"[ERR] Validation Failed: {e}")
    finally:
        sftp.close()
        client.close()

if __name__ == "__main__":
    deploy_podman()

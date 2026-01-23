import paramiko
import os
import sys
import time
from scp import SCPClient

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

def sync_files(client):
    print("--- Syncing Files ---")
    with SCPClient(client.get_transport()) as scp:
        # Sync specific directories/files to avoid syncing .git or node_modules
        # We need: agent_service, model_service, environment_service, dashboard, installer, *.py, *.yaml
        
        # Helper to walk and upload
        def recursive_upload_dir(local_path, remote_base):
             for root, dirs, files in os.walk(local_path):
                if 'node_modules' in root or '.git' in root or '__pycache__' in root or 'dist' in root:
                    continue
                    
                rel_path = os.path.relpath(root, local_path)
                remote_path = os.path.join(remote_base, rel_path).replace("\\", "/")
                
                # Make remote dir (lazy way, might fail if exists but okay)
                # client.exec_command(f"mkdir -p {remote_path}") 
                # SCPClient put supports recursive=True for dirs, but we want to exclude node_modules
                
                for f in files:
                    # Filter
                    if f.endswith(".pyc") or f.endswith(".log"): continue
                    
                    local_file = os.path.join(root, f)
                    remote_file = os.path.join(remote_path, f).replace("\\", "/")
                    
                    # print(f"Uploading {local_file} -> {remote_file}")
                    # scp.put(local_file, remote_file)
        
        # The SCP library is a bit basic. A better approach for this context might be simpler:
        # Just Zip locally, upload, unzip remotely.
        pass

def deploy_docker_synced():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")

    print(f"Connecting to {user}@{ip}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    try:
        # 1. Archive local files
        print("--- Archiving Local Files ---")
        import shutil
        import zipfile
        
        excludes = ['node_modules', '.git', '__pycache__', 'dist', 'coverage', '.env', 'secrets.env']
        
        zip_name = "deploy_package.zip"
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk("."):
                # Prune dirs
                dirs[:] = [d for d in dirs if d not in excludes]
                
                for file in files:
                    if file == zip_name: continue
                    if file.endswith(".log"): continue
                    # Add to zip
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, ".")
                    zipf.write(file_path, arc_name)
                    
        print(f"Created {zip_name}")
        
        # 2. Upload
        print("--- Uploading Archive ---")
        with SCPClient(client.get_transport()) as scp:
            scp.put(zip_name, f"/home/{user}/{zip_name}")
            
        # 3. Unzip Remote
        print("--- Extracting Remote ---")
        run_command(client, f"mkdir -p {REMOTE_DIR}")
        run_command(client, f"unzip -o /home/{user}/{zip_name} -d {REMOTE_DIR}")
        
        # 4. Clean up local
        os.remove(zip_name)
        
        # 5. Run Cleanup & Build
        print("--- Stopping Docker Stack ---")
        run_command(client, f"cd {REMOTE_DIR}/puppeteer && docker compose -f compose.server.yaml down")

        print("--- Pruning Old Images ---")
        # Optional: Prune to free space and ensure no cache collision
        # run_command(client, "docker system prune -f")

        print("--- Building Dashboard Image ---")
        # Build Dashboard specifically since we changed it massively
        res, _ = run_command(client, f"cd {REMOTE_DIR}/puppeteer/dashboard && docker build -t localhost/master-of-puppets-dashboard:latest -f Containerfile .")
        if not res: return 

        print("--- Building Server Image ---")
        res, _ = run_command(client, f"cd {REMOTE_DIR}/puppeteer && docker build -t localhost/master-of-puppets-server:latest -f Containerfile.server .")
        if not res: return

        print("--- Starting Stack ---")
        run_command(client, f"cd {REMOTE_DIR}/puppeteer && docker compose -f compose.server.yaml up -d")

        print("Waiting for health (20s)...")
        time.sleep(20)
        run_command(client, "curl -k -v https://localhost:8001/auth/login")
        
        print("[SUCCESS] Deployment Complete via Docker.")

    except Exception as e:
        print(f"[ERR] Validation Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    deploy_docker_synced()

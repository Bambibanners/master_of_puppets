import paramiko
import os
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
    print(f"REMOTE: {command}")
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    out_lines = []
    while True:
        if stdout.channel.recv_ready():
            try:
                data = stdout.channel.recv(4096).decode('utf-8', errors='replace')
                if print_output: print(data, end="")
                out_lines.append(data)
            except: pass
        if stdout.channel.exit_status_ready():
            break
        time.sleep(0.1)
    return "".join(out_lines)

def deploy_server():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {ip}...")
    client.connect(ip, username=user, password=password)

    try:
        sftp = client.open_sftp()
        
        # 1. Upload Code (Agent Service)
        print("--- Uploading Agent Service Code ---")
        local_main = "agent_service/main.py"
        remote_main = f"{REMOTE_DIR}/agent_service/main.py"
        sftp.put(local_main, remote_main)
        
        # Upload DB schema too just in case
        local_db = "agent_service/db.py"
        remote_db = f"{REMOTE_DIR}/agent_service/db.py"
        sftp.put(local_db, remote_db)

        # 2. Upload Secrets (Certs)
        print("--- Uploading New Certificates ---")
        # Ensure remote secrets dir exists
        run_command(client, f"mkdir -p {REMOTE_DIR}/secrets/ca")
        
        # List of secrets to upload
        secrets_files = [
            "secrets/server.crt",
            "secrets/server.key",
            "secrets/cert.pem",
            "secrets/key.pem",
            "secrets/verification.key",
            "secrets/root_ca.crt", # Legacy path if used?
            "secrets/ca/root_ca.crt",
            "secrets/ca/root_ca.key"
        ]
        
        for secret in secrets_files:
            if os.path.exists(secret):
                remote_path = f"{REMOTE_DIR}/{secret}"
                # ensure dir
                # sftp.put won't create dirs, but we made secrets/ca above
                print(f"Uploading {secret}...")
                sftp.put(secret, remote_path)

        sftp.close()

        # 3. Restart Agent Service
        print("--- Restarting Server Stack ---")
        # Just restart the agent container to pick up code and certs
        # (Assuming mapped volumes for secrets? or needs rebuild?)
        # Inspecting previous diagnostics, secrets seem to be mounted or copied?
        # If copied in build, we need to rebuild server.
        # Generally server is built via docker build .
        
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f compose.server.yaml build agent")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f compose.server.yaml up -d agent --force-recreate")
        
        print("Waiting 10s for Server Startup...")
        time.sleep(10)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    deploy_server()

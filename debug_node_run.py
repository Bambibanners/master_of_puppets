import paramiko
import time
import requests
import urllib3
import json
import sys

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

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
    
    while True:
        if stdout.channel.recv_ready():
            try:
                data = stdout.channel.recv(4096).decode('utf-8', errors='replace')
                if print_output: print(data, end="")
                out_lines.append(data)
            except: pass
        if stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                 try:
                    data = stdout.channel.recv(4096).decode('utf-8', errors='replace')
                    if print_output: print(data, end="")
                    out_lines.append(data)
                 except: pass
            break
        time.sleep(0.1)
        
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        return False, "".join(out_lines)
    return True, "".join(out_lines)

def debug_run():
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
        # Reuse if possible or get new.
        res = requests.post(f"{base_url}/auth/login", data={"username": "admin", "password": "admin"}, verify=False, timeout=10)
        res.raise_for_status()
        access_token = res.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.post(f"{base_url}/admin/generate-token", headers=headers, verify=False)
        res.raise_for_status()
        join_token = res.json()["token"]
        
        print(f"--- Updated Debug Run ---")
        # Run in foreground, RM after
        cmd = (
            f"docker run --rm "
            f"--network master_of_puppets_default "
            f"--add-host host.docker.internal:host-gateway "
            f"-e AGENT_URL=https://host.docker.internal:8001 "
            f"-e JOIN_TOKEN='{join_token}' "
            f"-e ROOT_CA_PATH=/app/secrets/root_ca.crt "
            f"-e PYTHONUNBUFFERED=1 "
            f"localhost/master-of-puppets-node:latest"
        )
        
        run_command(client, cmd)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    debug_run()

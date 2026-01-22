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

def deploy_compose_fix():
    print("--- Deploying Fixed Compose File ---")
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
        local_path = "compose.server.yaml"
        remote_path = f"{REMOTE_DIR}/compose.server.yaml"
        sftp.put(local_path, remote_path)
        sftp.close()
        
        # We need to restart everything to pick up new volumes?
        # Actually, just recreating containers should do it.
        # docker compose up -d will see changed config.
        
        print("--- Restarting Server ---")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f compose.server.yaml up -d --force-recreate")
        
        print("Waiting 15s...")
        time.sleep(15)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    deploy_compose_fix()

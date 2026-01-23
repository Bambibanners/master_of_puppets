import paramiko
import time
import sys

# Encoding fix
sys.stdout.reconfigure(encoding='utf-8')

REMOTE_DIR = "/home/speedy/master_of_puppets"

def read_secrets():
    secrets = {}
    with open("secrets.env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                secrets[k] = v
    return secrets

def run_command(client, command):
    print(f"REMOTE: {command}")
    stdin, stdout, stderr = client.exec_command(command)
    
    # Read stdout/stderr
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    
    print("--- STDOUT ---")
    print(out)
    print("--- STDERR ---")
    print(err)
    
    return client.exec_command("echo done")[1].channel.recv_exit_status()

def debug_startup():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {ip}...")
    client.connect(ip, username=user, password=password)

    try:
        print("--- Debugging Docker Compose Up ---")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f node-compose-scale.yaml up -d --scale node=4")
        
        # Also check images
        print("--- Check Images ---")
        run_command(client, "docker images | grep node")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    debug_startup()

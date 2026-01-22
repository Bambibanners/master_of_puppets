import paramiko
import time
import sys

# Force UTF-8 encoding for stdout
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

def run_command(client, command, print_output=True):
    print(f"REMOTE: {command}")
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    out_lines = []
    
    while True:
        if stdout.channel.recv_ready():
            # decode with replace to avoid crash
            data = stdout.channel.recv(4096).decode('utf-8', errors='replace')
            if print_output: 
                try: 
                    print(data, end="")
                except: 
                    pass # Ignore print errors
            out_lines.append(data)
        
        if stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(4096).decode('utf-8', errors='replace')
                if print_output:
                     try: print(data, end="")
                     except: pass
                out_lines.append(data)
            break
        time.sleep(0.1)
        
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        return False, "".join(out_lines)
    return True, "".join(out_lines)

def fix_node():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {ip}...")
    client.connect(ip, username=user, password=password)

    try:
        print("--- Building Node Image ---")
        run_command(client, f"cd {REMOTE_DIR} && docker build -t localhost/master-of-puppets-node:latest -f Containerfile.node .")
        
        print("--- Redeploying Nodes ---")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f node-compose-scale.yaml up -d --scale node=4")
        
        print("Waiting 15s...")
        time.sleep(15)
        
        print("--- Verify ---")
        run_command(client, "docker ps")
        
        print("--- Check Images ---")
        run_command(client, "docker images")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    fix_node()

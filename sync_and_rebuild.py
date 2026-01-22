import paramiko
import time

REMOTE_DIR = "/home/speedy/master_of_puppets"
LOCAL_PATH = "environment_service/node.py"

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

def sync_and_rebuild():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {ip}...")
    client.connect(ip, username=user, password=password)

    try:
        print("--- Uploading Patched node.py ---")
        sftp = client.open_sftp()
        # Upload using same relative path
        sftp.put(LOCAL_PATH, f"{REMOTE_DIR}/environment_service/node.py")
        sftp.close()
        
        print("--- Overwriting Remote Compose Config ---")
        
        # Generator Join Token dynamically
        import json
        import base64
        
        with open("secrets/ca/root_ca.crt", "r") as f:
            ca_pem = f.read()
            
        # Token "t" value - reusing the one we had or a known valid one
        # Ideally we fetch from DB or use a known one. 
        # The hardcoded one "ac4230444722477ba162e5be959f3898" might be in DB?
        # Let's trust it works since the node logs showed "Debug: Checking Token..." and proceeded to Trust Bootstrap.
        # The signature failure happened during SSL handshake, not Token Auth.
        token_val = "ac4230444722477ba162e5be959f3898" 
        
        token_payload = {
            "t": token_val,
            "ca": ca_pem
        }
        token_b64 = base64.b64encode(json.dumps(token_payload).encode()).decode()
        
        # Define fresh template to avoid corruption
        NODES_COUNT = 4
        
        compose_content = 'version: "3"\nservices:\n'
        for i in range(1, NODES_COUNT + 1):
             compose_content += f"""
  node-{i}:
    image: localhost/master-of-puppets-node:latest
    environment:
      - AGENT_URL=https://host.docker.internal:8001
      - JOIN_TOKEN={token_b64}
      - ROOT_CA_PATH=/app/secrets/root_ca.crt
      - PYTHONUNBUFFERED=1

    extra_hosts:
      - "host.docker.internal:host-gateway"

    restart: always

"""
        
        # Write back
        sftp = client.open_sftp()
        with sftp.file(f"{REMOTE_DIR}/node-compose-scale.yaml", "w") as f:
            f.write(compose_content)
        sftp.close()
        
        print("--- Rebuilding Node Image ---")
        run_command(client, f"cd {REMOTE_DIR} && docker build --no-cache -t localhost/master-of-puppets-node:latest -f Containerfile.node .")
        
        print("--- Redeploying ---")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f node-compose-scale.yaml up -d --force-recreate")
        
        print("Waiting 15s...")
        time.sleep(15)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    sync_and_rebuild()

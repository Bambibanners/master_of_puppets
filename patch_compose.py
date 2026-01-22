import paramiko
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
            data = stdout.channel.recv(4096).decode('utf-8', errors='replace')
            if print_output: print(data, end="")
            out_lines.append(data)
        if stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                 data = stdout.channel.recv(4096).decode('utf-8', errors='replace')
                 if print_output: print(data, end="")
                 out_lines.append(data)
            break
        time.sleep(0.1)
        
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        return False, "".join(out_lines)
    return True, "".join(out_lines)

def patch_compose():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {ip}...")
    client.connect(ip, username=user, password=password)

    try:
        print("--- Reading Compose ---")
        _, yaml_content = run_command(client, f"cat {REMOTE_DIR}/node-compose-scale.yaml", print_output=False)
        
        if "extra_hosts" in yaml_content:
            print("Compose already patched.")
        else:
            print("--- Patching Compose ---")
            # Simple string replacement relative to restart or indent
            # We look for "restart: always" and append "extra_hosts..."
            new_content = yaml_content.replace(
                "restart: always", 
                "restart: always\n    extra_hosts:\n      - \"host.docker.internal:host-gateway\""
            )
            
            # Escape for echo
            # Actually easier to use sftp to overwrite
            sftp = client.open_sftp()
            with sftp.file(f"{REMOTE_DIR}/node-compose-scale.yaml", "w") as f:
                f.write(new_content)
            sftp.close()
            print("Uploaded patched compose.")

        print("--- Redeploying Nodes ---")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f node-compose-scale.yaml up -d --scale node=4")
        
        print("Waiting 20s for enrollment...")
        time.sleep(20)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    patch_compose()

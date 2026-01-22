import paramiko
import time
import sys

def read_secrets():
    secrets = {}
    with open("secrets.env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                secrets[k] = v
    return secrets

def run_sudo_command(client, command, password):
    print(f"Running (Sudo): {command}")
    # Use -S to read password from stdin
    stdin, stdout, stderr = client.exec_command(f"sudo -S -p '' {command}", get_pty=True)
    stdin.write(f"{password}\n")
    stdin.flush()
    
    # Read output loop
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            data = stdout.channel.recv(1024).decode()
            sys.stdout.write(data)
            sys.stdout.flush()
        if stderr.channel.recv_ready():
            data = stderr.channel.recv(1024).decode()
            sys.stderr.write(data)
            sys.stderr.flush()
        time.sleep(0.1)
        
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"[FAIL] Exit Code: {exit_status}")
        return False
    else:
        print(f"[OK]")
        return True

def setup_remote():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")

    print(f"Connecting to {user}@{ip}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(ip, username=user, password=password, timeout=10)
        print("[OK] Connected.")

        # 1. Update Apt
        print("--- Updating Apt ---")
        run_sudo_command(client, "apt-get update", password)

        # 2. Install Podman
        print("--- Installing Podman ---")
        run_sudo_command(client, "apt-get install -y podman podman-compose", password)
        
        # 3. Install Docker
        print("--- Installing Docker ---")
        # Check if installed
        stdin, stdout, _ = client.exec_command("docker --version")
        if stdout.channel.recv_exit_status() != 0:
             print("Downloading/Running Docker Script...")
             # Since it's sudo, we can just run the script with sudo
             cmd = "curl -fsSL https://get.docker.com | sh"
             run_sudo_command(client, cmd, password)
             run_sudo_command(client, f"usermod -aG docker {user}", password)
        else:
             print("Docker already installed.")
             
        print("[OK] Setup Complete.")
            
    except Exception as e:
        print(f"[ERR] Setup Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    setup_remote()

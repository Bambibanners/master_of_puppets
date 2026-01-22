import paramiko
import os

def read_secrets():
    secrets = {}
    with open("secrets.env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                secrets[k] = v
    return secrets

def verify_remote():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")

    print(f"Connecting to {user}@{ip} via Paramiko...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(ip, username=user, password=password, timeout=10)
        print("[OK] SSH Connection Successful!")
        
        # Check OS
        stdin, stdout, stderr = client.exec_command("uname -a")
        print(f"OS: {stdout.read().decode().strip()}")
        
        # Check Container Engines
        stdin, stdout, stderr = client.exec_command("docker --version")
        docker_ver = stdout.read().decode().strip()
        if docker_ver:
            print(f"[OK] Docker found: {docker_ver}")
        else:
            print("[FAIL] Docker NOT found.")

        stdin, stdout, stderr = client.exec_command("podman --version")
        podman_ver = stdout.read().decode().strip()
        if podman_ver:
            print(f"[OK] Podman found: {podman_ver}")
        else:
            print("[FAIL] Podman NOT found.")
            
    except Exception as e:
        print(f"[ERR] Connection Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    verify_remote()

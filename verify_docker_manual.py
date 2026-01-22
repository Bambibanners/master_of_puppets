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

def verify_docker_manual():
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
        
        # Restart Stack (Docker)
        print("--- Restarting Stack (Docker) ---")
        client.exec_command("cd master_of_puppets && docker compose -f compose.server.yaml down")
        stdin, stdout, stderr = client.exec_command("cd master_of_puppets && docker compose -f compose.server.yaml up -d")
        print(stdout.read().decode('utf-8', errors='replace'))
        print(stderr.read().decode('utf-8', errors='replace'))
        
        print("Waiting 20s...")
        time.sleep(20)
        
        # Check Token
        print("--- Fetching Token (Raw) ---")
        cmd = "curl -k -v -X POST -d 'username=admin&password=admin' https://localhost:8001/auth/login"
        stdin, stdout, stderr = client.exec_command(cmd)
        
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        
        print("STDOUT:", out)
        print("STDERR:", err)

    except Exception as e:
        print(f"[ERR] Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    verify_docker_manual()

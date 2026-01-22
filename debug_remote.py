import paramiko

def read_secrets():
    secrets = {}
    with open("secrets.env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                secrets[k] = v
    return secrets

def debug_remote():
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
        
        print("--- Agent Logs (Tail 50) ---")
        stdin, stdout, stderr = client.exec_command("podman logs --tail 50 master_of_puppets_agent_1")
        print(stdout.read().decode('utf-8', errors='replace'))
        print(stderr.read().decode('utf-8', errors='replace'))

        print("--- DB Logs (Tail 20) ---")
        stdin, stdout, stderr = client.exec_command("podman logs --tail 20 master_of_puppets_db_1")
        print(stdout.read().decode('utf-8', errors='replace'))
        print(stderr.read().decode('utf-8', errors='replace'))
        
        print("--- Manual Token Request ---")
        cmd = "curl -k -v -X POST -d 'username=admin&password=admin' https://localhost:8001/auth/login"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace'))
        print(stderr.read().decode('utf-8', errors='replace'))

    except Exception as e:
        print(f"[ERR] Debug Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    debug_remote()

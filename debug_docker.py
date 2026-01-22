import paramiko

def read_secrets():
    secrets = {}
    with open("secrets.env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                secrets[k] = v
    return secrets

def debug_docker():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")

    print(f"Connecting to {user}@{ip}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(ip, username=user, password=password, timeout=10)
        
        # Check permissions
        print("--- Docker Info ---")
        stdin, stdout, stderr = client.exec_command("docker info")
        print(stdout.read().decode('utf-8', errors='replace'))
        print(stderr.read().decode('utf-8', errors='replace'))

        # Check Compose Config
        print("--- Compose Config ---")
        stdin, stdout, stderr = client.exec_command("cd master_of_puppets && docker compose -f compose.server.yaml config")
        print(stdout.read().decode('utf-8', errors='replace'))
        print(stderr.read().decode('utf-8', errors='replace'))
        
        # Try Build Verbose
        print("--- Build Verbose ---")
        # Ensure we have strict permissions or use sudo if needed (hoping not)
        cmd = "cd master_of_puppets && docker compose -f compose.server.yaml build --no-cache --progress=plain"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace'))
        print(stderr.read().decode('utf-8', errors='replace'))

    except Exception as e:
        print(f"[ERR] Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    debug_docker()

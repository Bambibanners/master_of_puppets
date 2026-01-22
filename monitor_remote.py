import paramiko
import sys

def read_secrets():
    secrets = {}
    with open("secrets.env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                secrets[k] = v
    return secrets

def monitor():
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
        
        cmds = [
            "uptime",
            "free -m",
            "pgrep -af npm",
            "du -sh master_of_puppets/dashboard/node_modules || echo 'No node_modules yet'",
            "tail -n 5 master_of_puppets/dashboard/node_modules/.package-lock.json || echo 'No lockfile'"
        ]
        
        for cmd in cmds:
            print(f"--- {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode('utf-8', errors='replace').strip()
            err = stderr.read().decode('utf-8', errors='replace').strip()
            if out: print(out)
            if err: print(f"ERR: {err}")
            print("")
            
    except Exception as e:
        print(f"[ERR] Monitor Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    monitor()

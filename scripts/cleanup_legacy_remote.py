import paramiko
import os
from dotenv import load_dotenv

# Load secrets

def read_secrets():
    secrets = {}
    if os.path.exists("secrets.env"):
        with open("secrets.env", "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    secrets[k] = v
    return secrets

def cleanup_legacy():
    creds = read_secrets()
    HOST = creds.get("speedy_mini_ip", "192.168.50.128")
    USER = creds.get("speedy_mini_username", "thomas")
    PASSWORD = creds.get("speedy_mini_password")

    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if PASSWORD:
            client.connect(HOST, username=USER, password=PASSWORD)
        else:
            # Fallback to key if defined elsewhere or default agent
            client.connect(HOST, username=USER)
        
        print("Stopping and removing legacy 'master_of_puppets' containers...")
        # Stop and remove containers mimicking the old naming convention
        cmd = "docker ps -a --format '{{.Names}}' | grep master_of_puppets | xargs -r docker rm -f"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err:
            print(f"stderr: {err}")
            
        print("Starting new 'puppeteer' stack...")
        cmd = "cd master_of_puppets/puppeteer && docker compose -f compose.server.yaml up -d --force-recreate --remove-orphans"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err:
            print(f"stderr: {err}")
            
        print("Cleanup and Restart Complete.")
        
    except Exception as e:
        print(f"Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    cleanup_legacy()

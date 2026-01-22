import paramiko
import os

def read_secrets():
    secrets = {}
    if os.path.exists("secrets.env"):
        with open("secrets.env", "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    secrets[k] = v
    return secrets

def check():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")
    
    print(f"Connecting to {ip}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password)
    
    print("--- Docker PS ---")
    stdin, stdout, stderr = client.exec_command("docker ps | grep dashboard")
    print(stdout.read().decode())
    
    print("--- Curl Dashboard ---")
    stdin, stdout, stderr = client.exec_command("curl -I http://localhost:5173")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    check()

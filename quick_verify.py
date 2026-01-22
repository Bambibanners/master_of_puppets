import paramiko
import os
import sys

def read_secrets():
    secrets = {}
    with open("secrets.env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                secrets[k] = v
    return secrets

def verify():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")

    print(f"Connecting to {user}@{ip}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)

    try:
        # Check token
        print("--- Token Request ---")
        cmd = 'curl -k -s -X POST -d "username=admin&password=admin" https://localhost:8001/auth/login'
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        print(out)

        # Check dashboard
        print("--- Dashboard Check ---")
        stdin, stdout, stderr = client.exec_command("curl -s http://localhost:5173/ | head -5")
        out = stdout.read().decode()
        print(out if out else "[No output - Dashboard may not be running]")

        # Check docker ps for dashboard
        print("--- Running Containers ---")
        stdin, stdout, stderr = client.exec_command("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
        out = stdout.read().decode()
        print(out)

    finally:
        client.close()

if __name__ == "__main__":
    verify()

import os
import paramiko
import sys
from dotenv import dotenv_values

def log(msg):
    # Strip non-ascii just in case
    msg = msg.encode('ascii', 'ignore').decode('ascii')
    print(msg)
    sys.stdout.flush()

def run_cmd(ssh, command):
    log(f"Executing: {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    return exit_status, out, err

def diag():
    secrets = dotenv_values("secrets.env")
    host = secrets.get("speedy_mini_ip")
    user = secrets.get("speedy_mini_username")
    password = secrets.get("speedy_mini_password")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    
    log("Checking System Resources:")
    run_cmd(ssh, "free -m")
    run_cmd(ssh, "df -h")
    
    log("Checking Dashboard Build individually:")
    # Try building with legacy peer deps or just see more logs
    actual_code_path = "/home/speedy/puppeteer_stack/puppeteer/dashboard"
    status, out, err = run_cmd(ssh, f"cd {actual_code_path} && podman build -t dashboard-test -f Containerfile .")
    log(f"Build Result: {status}")
    log(f"STDOUT:\n{out}")
    log(f"STDERR:\n{err}")
    
    ssh.close()

if __name__ == "__main__":
    diag()

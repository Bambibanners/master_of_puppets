import os
import paramiko
import sys
from dotenv import dotenv_values

def log(msg):
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
    
    log("Container Status:")
    status, out, err = run_cmd(ssh, "podman ps -a")
    # Clean output of problematic chars for printing
    log(out.encode('ascii', 'ignore').decode('ascii'))
    
    log("Loader Logs (last 50 lines):")
    status, out, err = run_cmd(ssh, "podman logs puppeteer-loader-run | tail -n 50")
    log(out.encode('ascii', 'ignore').decode('ascii'))
    
    ssh.close()

if __name__ == "__main__":
    diag()

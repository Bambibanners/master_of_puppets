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

def fix_socket():
    secrets = dotenv_values("secrets.env")
    host = secrets.get("speedy_mini_ip")
    user = secrets.get("speedy_mini_username")
    password = secrets.get("speedy_mini_password")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    
    log("Enabling linger for user...")
    run_cmd(ssh, f"echo {password} | sudo -S loginctl enable-linger {user}")
    
    log("Starting podman socket service...")
    run_cmd(ssh, "systemctl --user enable --now podman.socket")
    
    log("Verifying socket...")
    status, out, err = run_cmd(ssh, "ls -la /run/user/1000/podman/podman.sock")
    log(f"Socket: {out} {err}")
    
    ssh.close()

if __name__ == "__main__":
    fix_socket()

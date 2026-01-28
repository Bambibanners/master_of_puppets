import os
import paramiko
import sys
import zipfile
import time
from scp import SCPClient
from dotenv import dotenv_values

def log(msg):
    print(msg)
    sys.stdout.flush()

def run_cmd(ssh, command, stream_output=False):
    log(f"Executing: {command}")
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    
    output = []
    if stream_output:
        while True:
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(4096).decode('utf-8', errors='replace')
                print(data, end="")
                sys.stdout.flush()
                output.append(data)
            if stdout.channel.exit_status_ready():
                break
            time.sleep(0.1)
    
    exit_status = stdout.channel.recv_exit_status()
    out_text = "".join(output) if stream_output else stdout.read().decode('utf-8', errors='replace')
    err_text = stderr.read().decode('utf-8', errors='replace')
    
    return exit_status, out_text, err_text

def deploy():
    secrets = dotenv_values("secrets.env")
    host = secrets.get("speedy_mini_ip")
    user = secrets.get("speedy_mini_username")
    password = secrets.get("speedy_mini_password")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)

    remote_path = "/home/speedy/puppeteer_stack"
    actual_code_path = f"{remote_path}/puppeteer"

    log("Checking Loader Internal Files...")
    # Run the loader but just to check files
    launch_cmd = f"cd {actual_code_path} && podman run --privileged --rm puppeteer-loader ls -R /etc/containers"
    status, out, err = run_cmd(ssh, launch_cmd, stream_output=True)
    
    log(f"Final Status: {status}")
    
    ssh.close()

if __name__ == "__main__":
    deploy()

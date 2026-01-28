import paramiko
from dotenv import dotenv_values

def diag():
    secrets = dotenv_values("secrets.env")
    host = secrets.get("speedy_mini_ip")
    user = secrets.get("speedy_mini_username")
    password = secrets.get("speedy_mini_password")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    
    print("--- FINAL CONTAINER STATUS ---")
    stdin, stdout, stderr = ssh.exec_command("podman ps -a")
    print(stdout.read().decode())
    
    print("--- LOADER FINAL LOGS ---")
    stdin, stdout, stderr = ssh.exec_command("podman logs puppeteer-loader-run | tail -n 20")
    print(stdout.read().decode('utf-8', errors='replace').encode('ascii', 'ignore').decode('ascii'))
    
    ssh.close()

if __name__ == "__main__":
    diag()

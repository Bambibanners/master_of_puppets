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
    
    print("--- REMOTE ENTRYPOINT CHECK ---")
    stdin, stdout, stderr = ssh.exec_command("podman exec app_cert-manager_1 cat /bin/entrypoint.sh")
    print(stdout.read().decode())
    
    print("--- STOPPING CURRENT STACK ---")
    # We'll use the loader's compose file
    ssh.exec_command("cd /home/speedy/puppeteer_stack/puppeteer && podman-compose -f compose.server.yaml down")
    
    ssh.close()

if __name__ == "__main__":
    diag()

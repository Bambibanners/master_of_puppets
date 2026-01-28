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
    
    print("--- CADDY LOGS ---")
    stdin, stdout, stderr = ssh.exec_command("podman logs app_cert-manager_1")
    print(stdout.read().decode('utf-8', errors='replace').encode('ascii', 'ignore').decode('ascii'))
    
    print("--- DASHBOARD CONTENT CHECK ---")
    stdin, stdout, stderr = ssh.exec_command("podman exec app_dashboard_1 ls -R /usr/share/nginx/html")
    print(stdout.read().decode())
    
    print("--- DASHBOARD INDEX SNIPPET ---")
    stdin, stdout, stderr = ssh.exec_command("podman exec app_dashboard_1 head -n 20 /usr/share/nginx/html/index.html")
    print(stdout.read().decode())

    ssh.close()

if __name__ == "__main__":
    diag()

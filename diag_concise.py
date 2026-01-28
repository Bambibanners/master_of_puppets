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
    
    print("--- BUILD LOG (LAST 50 LINES) ---")
    actual_code_path = "/home/speedy/puppeteer_stack/puppeteer/dashboard"
    stdin, stdout, stderr = ssh.exec_command(f"tail -n 50 {actual_code_path}/build_debug.log")
    # Clean output of problematic chars for printing
    print(stdout.read().decode('utf-8', errors='replace').encode('ascii', 'ignore').decode('ascii'))
    
    ssh.close()

if __name__ == "__main__":
    diag()

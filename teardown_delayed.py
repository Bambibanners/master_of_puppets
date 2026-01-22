import paramiko
import time

REMOTE_DIR = "/home/speedy/master_of_puppets"

def read_secrets():
    secrets = {}
    with open("secrets.env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                secrets[k] = v
    return secrets

def run_command(client, command, print_output=True):
    print(f"REMOTE: {command}")
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    while True:
        if stdout.channel.recv_ready():
            try: stdout.channel.recv(4096)
            except: pass
        if stdout.channel.exit_status_ready(): break
        time.sleep(0.1)

def teardown():
    print("Waiting 5 minutes (300s) before teardown...")
    time.sleep(300)
    
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password)

    try:
        print("--- Teardown ---")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f node-compose-scale.yaml down")
        print("Nodes Terminated.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    teardown()

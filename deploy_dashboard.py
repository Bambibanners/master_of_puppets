import paramiko
import os
import time
import zipfile
import shutil

REMOTE_DIR = "/home/speedy/master_of_puppets"

def read_secrets():
    secrets = {}
    if os.path.exists("secrets.env"):
        with open("secrets.env", "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    secrets[k] = v
    return secrets

def run_command(client, command, print_output=True):
    print(f"REMOTE: {command}")
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    out_lines = []
    while True:
        if stdout.channel.recv_ready():
            try:
                data = stdout.channel.recv(4096).decode('utf-8', errors='replace')
                if print_output: print(data, end="")
                out_lines.append(data)
            except: pass
        if stdout.channel.exit_status_ready():
            break
        time.sleep(0.1)
    return "".join(out_lines)

def zip_dashboard():
    print("Zipping dashboard (skipping node_modules)...")
    output_filename = "dashboard-deploy.zip"
    if os.path.exists(output_filename):
        os.remove(output_filename)
        
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("dashboard"):
            if "node_modules" in dirs:
                dirs.remove("node_modules")
            if "dist" in dirs:
                dirs.remove("dist")
            
            for file in files:
                file_path = os.path.join(root, file)
                # Archive name should be relative to "dashboard" folder
                # e.g. dashboard/src/App.tsx -> src/App.tsx
                arcname = os.path.relpath(file_path, "dashboard")
                zipf.write(file_path, arcname)
    return output_filename

def deploy():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")
    
    if not ip:
        print("Error: secrets.env missing or incomplete.")
        return

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {ip}...")
    client.connect(ip, username=user, password=password)

    try:
        # Zip
        zip_file = zip_dashboard()
        
        # Upload
        sftp = client.open_sftp()
        print(f"Uploading {zip_file}...")
        remote_zip = f"{REMOTE_DIR}/{zip_file}"
        sftp.put(zip_file, remote_zip)
        
        # Upload Compose File too
        print("Uploading compose.server.yaml...")
        sftp.put("compose.server.yaml", f"{REMOTE_DIR}/compose.server.yaml")
        
        sftp.close()
        
        # Unzip
        print("Unzipping remote...")
        # Ensure dashboard dir exists (it should from git checkout or previous runs)
        run_command(client, f"mkdir -p {REMOTE_DIR}/dashboard")
        # Install unzip if missing? Alpine usually needs apk add unzip.
        # But speedy_mini is Linux (Ubuntu/Debian?). Paramiko defaults to shell.
        # Assuming unzip exists. If not, we might fail.
        # Check if unzip exists
        check = run_command(client, "which unzip", print_output=False)
        if not check.strip():
            print("Installing unzip...")
            # Try apt or apk?
            # Likely Ubuntu/Debian based on username 'speedy'
            # run_command(client, "sudo apt-get install -y unzip") # requires sudo pass?
            # Or use python to unzip remotely?
            # Let's try python unzip one-liner
            cmd_unzip = f"python3 -c \"import zipfile; zipfile.ZipFile('{remote_zip}', 'r').extractall('{REMOTE_DIR}/dashboard')\""
            run_command(client, cmd_unzip)
        else:
            run_command(client, f"unzip -o {remote_zip} -d {REMOTE_DIR}/dashboard")
            
        # Build & Restart
        print("--- Rebuilding Dashboard ---")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f compose.server.yaml build dashboard")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f compose.server.yaml up -d dashboard --force-recreate")
        
        print("Deployment Complete.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()
        if os.path.exists("dashboard-deploy.zip"):
            os.remove("dashboard-deploy.zip")

if __name__ == "__main__":
    deploy()

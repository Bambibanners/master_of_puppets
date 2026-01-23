import paramiko
import os
import sys
import time

def read_secrets():
    secrets = {}
    try:
        with open("secrets.env", "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    secrets[k] = v
    except FileNotFoundError:
        print("secrets.env not found.")
        sys.exit(1)
    return secrets

def run_command(client, command, print_output=True):
    print(f"REMOTE EXEC: {command}")
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    
    out_lines = []
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            data = stdout.channel.recv(1024).decode('utf-8', errors='replace')
            if print_output:
                sys.stdout.write(data.encode('ascii', 'replace').decode())
                sys.stdout.flush()
            out_lines.append(data)
        if stderr.channel.recv_ready():
            data = stderr.channel.recv(1024).decode('utf-8', errors='replace')
            if print_output:
                sys.stderr.write(data.encode('ascii', 'replace').decode())
                sys.stderr.flush()
        time.sleep(0.1)
        
    s_exit = stdout.channel.recv_exit_status()
    if s_exit != 0:
        print(f"[FAIL] Exit: {s_exit}")
        return False, "".join(out_lines)
    return True, "".join(out_lines)

def run_sudo_command(client, command, password, print_output=True):
    print(f"REMOTE EXEC (SUDO): {command}")
    stdin, stdout, stderr = client.exec_command(f"sudo -S -p '' {command}", get_pty=True)
    stdin.write(f"{password}\n")
    stdin.flush()
    
    out_lines = []
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            data = stdout.channel.recv(1024).decode('utf-8', errors='replace')
            if print_output:
                # Filter out the password prompt if it leaks (rare with -S -p '')
                sys.stdout.write(data.encode('ascii', 'replace').decode())
                sys.stdout.flush()
            out_lines.append(data)
        if stderr.channel.recv_ready():
            data = stderr.channel.recv(1024).decode('utf-8', errors='replace')
            if print_output:
                sys.stderr.write(data.encode('ascii', 'replace').decode())
                sys.stderr.flush()
        time.sleep(0.1)
        
    s_exit = stdout.channel.recv_exit_status()
    if s_exit != 0:
        print(f"[FAIL] Exit: {s_exit}")
        return False, "".join(out_lines)
    return True, "".join(out_lines)

def setup_swap():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")

    if not all([ip, user, password]):
        print("Missing credentials in secrets.env")
        return

    print(f"Connecting to {user}@{ip}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)

    try:
        # 1. Check existing swap
        print("--- Checking Existing Swap ---")
        _, out = run_command(client, "free -h")
        if "Swap:" in out:
             swap_line = [l for l in out.splitlines() if "Swap:" in l][0]
             parts = swap_line.split()
             # parts[1] is total. If it's not 0B, we have swap.
             # Typical output: Swap:          2.0Gi          0B       2.0Gi
             print(f"Current Swap: {swap_line}")
             if parts[1] != "0B" and parts[1] != "0":
                 print("[OK] Swap already exists. Skipping creation.")
                 return

        # 2. Create Swap File (2GB)
        print("--- Creating 2GB Swap File ---")
        # specific command: dd if=/dev/zero of=/swapfile bs=1M count=2048
        # We need sudo for this.
        cmd_create = "dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress"
        res, _ = run_sudo_command(client, cmd_create, password)
        if not res: return

        # 3. Secure Permissions
        print("--- Setting Permissions ---")
        run_sudo_command(client, "chmod 600 /swapfile", password)

        # 4. Make Swap
        print("--- Formatting Swap ---")
        run_sudo_command(client, "mkswap /swapfile", password)

        # 5. Enable Swap
        print("--- Enabling Swap ---")
        run_sudo_command(client, "swapon /swapfile", password)

        # 6. Verify
        print("--- Verifying ---")
        run_command(client, "free -h")

        # 7. Persistence (Optional)
        # We can append to fstab if not there.
        print("--- Adding to fstab (Persistence) ---")
        check_fstab = "grep '/swapfile' /etc/fstab"
        res, out = run_command(client, check_fstab, print_output=False)
        if not res or "/swapfile" not in out:
            run_sudo_command(client, "sh -c 'echo \"/swapfile none swap sw 0 0\" >> /etc/fstab'", password)
            print("Added to /etc/fstab")
        else:
            print("Already in /etc/fstab")

    except Exception as e:
        print(f"[ERR] Swap Setup Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    setup_swap()

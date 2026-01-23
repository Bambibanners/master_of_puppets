import paramiko
import time
import datetime

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
    out_lines = []
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            data = stdout.channel.recv(1024).decode('utf-8', errors='replace')
            if print_output: print(data, end="", flush=True)
            out_lines.append(data)
        time.sleep(0.1)
    if stdout.channel.recv_exit_status() != 0:
        return False, "".join(out_lines)
    return True, "".join(out_lines)

def verify_teardown():
    creds = read_secrets()
    ip = creds.get("speedy_mini_ip")
    user = creds.get("speedy_mini_username")
    password = creds.get("speedy_mini_password")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {ip}...")
    client.connect(ip, username=user, password=password)

    try:
        print("--- Verifying Output in Containers ---")
        _, nodes_list = run_command(client, "docker ps --format '{{.Names}}' | grep node", print_output=False)
        nodes = nodes_list.strip().split('\n')
        
        api_success_count = 0
        gui_success_count = 0
        total_nodes = 0
        
        for node in nodes:
            node = node.strip()
            if not node: continue
            total_nodes += 1
            print(f"Checking {node}...")
            
            # Check API File
            res_api, out_api = run_command(client, f"docker exec {node} cat /tmp/hello_world_test.md", print_output=False)
            if "Hello World" in out_api:
                print(f"  [OK] API Job File found.")
                api_success_count += 1
            else:
                print(f"  [FAIL] API Job File missing.")

            # Check GUI File
            res_gui, out_gui = run_command(client, f"docker exec {node} cat /tmp/hello_world_gui.md", print_output=False)
            if "Hello World" in out_gui:
                print(f"  [OK] GUI Job File found.")
                gui_success_count += 1
            else:
                print(f"  [INFO] GUI Job File missing (Expected on ~1 node).")

        print("--- Verification Results ---")
        print(f"API Job Coverage: {api_success_count}/{total_nodes} nodes.")
        print(f"GUI Job Coverage: {gui_success_count}/{total_nodes} nodes.")

        if api_success_count == total_nodes:
            print("[PASS] API Job ran on all nodes.")
        else:
            print("[FAIL] API Job did not run on all nodes.")

        if gui_success_count >= 1:
            print("[PASS] GUI Job ran on at least one node.")
        else:
            print("[FAIL] GUI Job did not run on any node.")

        print(f"--- Waiting 5 minutes as requested (Started at {datetime.datetime.now().time()}) ---")
        time.sleep(300)
        
        print("--- Teardown ---")
        run_command(client, f"cd {REMOTE_DIR} && docker compose -f node-compose-scale.yaml down")
        print("Nodes Terminated.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    verify_teardown()

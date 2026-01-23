import paramiko
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

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
    # Quiet run
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    out_lines = []
    while True:
        if stdout.channel.recv_ready():
            try: out_lines.append(stdout.channel.recv(4096).decode('utf-8', errors='replace'))
            except: pass
        if stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                try: out_lines.append(stdout.channel.recv(4096).decode('utf-8', errors='replace'))
                except: pass
            break
        time.sleep(0.1)
    return "".join(out_lines)

def validate():
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
        nodes_out = run_command(client, "docker ps --format '{{.Names}}' | grep node", print_output=False)
        nodes = [n.strip() for n in nodes_out.split('\n') if n.strip()]
        
        print(f"Checking {len(nodes)} nodes...")
        
        api_success_count = 0
        gui_success_count = 0
        
        for node in nodes:
            print(f"[{node}]", end=" ", flush=True)
            # Check API File
            out_api = run_command(client, f"docker exec {node} cat /tmp/hello_world_test.md", print_output=False)
            if "Hello World" in out_api:
                print(f"| API: OK", end=" ")
                api_success_count += 1
            else:
                print(f"| API: MISSING", end=" ")

            # Check GUI File
            out_gui = run_command(client, f"docker exec {node} cat /tmp/hello_world_gui.md", print_output=False)
            if "Hello World" in out_gui:
                print(f"| GUI: OK", end=" ")
                gui_success_count += 1
            else:
                print(f"| GUI: MISSING", end=" ")
            
            print("")

        print("\n--- Summary ---")
        print(f"Nodes: {len(nodes)}")
        print(f"API Coverage: {api_success_count}/{len(nodes)}")
        print(f"GUI Coverage: {gui_success_count}/{len(nodes)}")
        
        if api_success_count > 0:
            print("FINAL_RESULT: PASS (API jobs detected)")
        else:
            print("FINAL_RESULT: FAIL (No API jobs ran)")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    validate()

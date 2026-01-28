import os
import subprocess
import sys

SECRETS_FILE = "secrets.env"

def log(msg):
    print(f"[Loader] {msg}")
    sys.stdout.flush()

def check_secrets():
    """Detects or Prompts for Secrets."""
    if os.path.exists(SECRETS_FILE):
        log(f"Found secrets file: {SECRETS_FILE}")
        return

    log("Secrets file not found. Starting Interactive Setup...")
    
    try:
        duck_token = input("Enter DuckDNS Token: ").strip()
        duck_domain = input("Enter DuckDNS Domain (e.g. app.duckdns.org): ").strip()
        email = input("Enter Admin Email: ").strip()
    except EOFError:
        log("Error: No input allowed (Non-interactive mode?). Please mount secrets.env.")
        sys.exit(1)

    content = f"""
DUCKDNS_TOKEN={duck_token}
DUCKDNS_DOMAIN={duck_domain}
ACME_EMAIL={email}
"""
    with open(SECRETS_FILE, "w") as f:
        f.write(content.strip())
    
    log("Created secrets.env")

def launch_stack():
    """Runs podman-compose up."""
    log("Launching Stack on Host (via Socket)...")
    
    # Verify we can talk to the socket
    try:
        subprocess.check_call(["podman", "info"])
    except:
        log("Error: Cannot talk to Host Podman Socket.")
        sys.exit(1)

    build_cmds = [
        # Build Cert Manager (Small)
        ["podman", "build", "-t", "localhost/app_cert-manager:v3", "-f", "cert-manager/Dockerfile", "cert-manager"],
        ["podman", "system", "prune", "-f"], # Clean up layers
        
        # Build Server (Medium)
        ["podman", "build", "-t", "localhost/master-of-puppets-server:v3", "-f", "Containerfile.server", "."],
        ["podman", "system", "prune", "-f"],

        # Build Dashboard (Heavy - do last)
        ["podman", "build", "-t", "localhost/master-of-puppets-dashboard:v3", "-f", "dashboard/Containerfile", "dashboard"],
        ["podman", "system", "prune", "-f"],
    ]

    for b_cmd in build_cmds:
        log(f"Executing Build Step: {' '.join(b_cmd)}")
        try:
            subprocess.check_call(b_cmd)
        except subprocess.CalledProcessError as e:
            log(f"Build failed: {e}")
            sys.exit(1)

    cmd = [
        "podman-compose", 
        "-f", "compose.server.yaml", 
        "--env-file", SECRETS_FILE, 
        "up", "-d" # No --build, we just built them manually
    ]
    
    try:
        # Use Popen to stream output
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(f"[Compose] {line.strip()}")
            sys.stdout.flush()
        
        exit_code = process.wait()
        if exit_code == 0:
            log("Stack Deployed Successfully!")
        else:
            log(f"Deployment Failed with exit code {exit_code}.")
            sys.exit(1)
    except Exception as e:
        log(f"Error during deployment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    log("Initializing Puppeteer Loader...")
    check_secrets()
    launch_stack()

import os
import sys
import shutil

# Ensure we can import from puppeteer directory
sys.path.append(os.path.join(os.getcwd(), 'puppeteer'))

from agent_service import pki

# Valid SANs for Server
SANS = [
    "localhost",
    "127.0.0.1",
    "host.docker.internal",
    "host.containers.internal", # Podman
    "192.168.50.128" # Speedy Mini LAN IP
]

def regenerate():
    print(f"Regenerating Server Certs with SANs: {SANS}")
    
    # Paths
    secrets_dir = os.path.join("puppeteer", "secrets")
    ca_dir = os.path.join(secrets_dir, "ca")
    server_key = os.path.join(secrets_dir, "server.key")
    server_cert = os.path.join(secrets_dir, "server.crt")
    
    # Remove existing to force regen
    if os.path.exists(server_key):
        os.remove(server_key)
    if os.path.exists(server_cert):
        os.remove(server_cert)
        
    # Init CA (loads existing Root if present)
    ca = pki.CertificateAuthority(ca_dir=ca_dir)
    ca.ensure_root_ca()
    
    # Issue Server Cert
    ca.issue_server_cert(server_key, server_cert, SANS)
    
    # Also create legacy PEM names
    shutil.copy(server_cert, os.path.join(secrets_dir, "cert.pem"))
    shutil.copy(server_key, os.path.join(secrets_dir, "key.pem"))
    
    print("[OK] Server Certs Regenerated.")

if __name__ == "__main__":
    regenerate()

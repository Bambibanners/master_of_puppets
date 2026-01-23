import os
import sys
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

def sign_content(content: str, key_path: str = None) -> str:
    if key_path is None:
        # Default to relative path from this script if not provided
        # Assuming this script is in /scripts and secrets are in /puppeteer/secrets
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        key_path = os.path.join(base_dir, "puppeteer", "secrets", "signing.key")
    
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Signing key not found at: {key_path}")

    with open(key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)

    signature = private_key.sign(
        content.encode('utf-8'),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sign_job.py <file_to_sign> [key_path]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    key_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    with open(file_path, "r") as f:
        content = f.read()
    
    try:
        sig = sign_content(content, key_path)
        print(sig)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

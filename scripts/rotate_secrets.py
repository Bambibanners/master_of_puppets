import secrets
import string
import os
import shutil
from cryptography.fernet import Fernet

def generate_secure_token(length=32):
    return secrets.token_hex(length // 2)

def generate_password(length=20):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def main():
    print("🔒 Rotating Secrets & Generating Secure Configuration")
    
    # 1. Generate Keys
    new_api_key = generate_secure_token(64)
    new_db_password = generate_password(24)
    new_encryption_key = Fernet.generate_key().decode()
    
    # 2. Backup existing .env
    if os.path.exists(".env"):
        shutil.copy(".env", ".env.bak")
        print("✅ Backed up .env to .env.bak")
        
        # Read existing to preserve other values (like URLs)
        env_lines = []
        with open(".env", "r") as f:
            env_lines = f.readlines()
    else:
        env_lines = []
        
    # 3. Update/Inject Values
    config = {
        "API_KEY": new_api_key,
        "POSTGRES_PASSWORD": new_db_password,
        "ENCRYPTION_KEY": new_encryption_key,
        "POSTGRES_USER": "puppet",
        "POSTGRES_DB": "puppet_db"
    }
    
    new_lines = []
    keys_written = set()
    
    for line in env_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            new_lines.append(line)
            continue
            
        key = line.split("=")[0]
        if key in config:
            new_lines.append(f"{key}={config[key]}")
            keys_written.add(key)
        else:
            new_lines.append(line)
            
    # Append missing
    for k, v in config.items():
        if k not in keys_written:
            new_lines.append(f"{k}={v}")
            
    # 4. Write new .env
    with open(".env", "w") as f:
        f.write("\n".join(new_lines) + "\n")
        
    print(f"✅ Secure keys written to .env")
    print(f"   API_KEY: {new_api_key[:10]}...")
    print(f"   POSTGRES_PASSWORD: {new_db_password[:5]}...")
    print("\n⚠️  ACTION REQUIRED: Restart the stack for changes to take effect.")
    print("   docker compose -f compose.server.yaml up -d")
    
    # Optional: Update secrets.env if it exists? 
    # secrets.env is for SSH currently.

if __name__ == "__main__":
    main()

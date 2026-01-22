from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os

def generate_keys():
    secrets_dir = "secrets"
    if not os.path.exists(secrets_dir):
        os.makedirs(secrets_dir)
        
    print("Generating Signing Key...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Save Private Key (signing.key)
    with open(os.path.join(secrets_dir, "signing.key"), "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
        
    # Save Public Key (verification.key)
    public_key = private_key.public_key()
    with open(os.path.join(secrets_dir, "verification.key"), "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
        
    print("Keys Generated in /secrets.")

if __name__ == "__main__":
    generate_keys()

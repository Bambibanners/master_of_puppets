from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base64
import json

def generate_identity():
    print("Generating Ed25519 Keypair...")
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    
    print("\n----- PUBLIC KEY (Copy this) -----")
    print(pem_public)
    
    return private_key, pem_public

def sign_script(private_key, script_content):
    print(f"\nSigning Script: {script_content[:20]}...")
    sig = private_key.sign(script_content.encode('utf-8'))
    b64_sig = base64.b64encode(sig).decode()
    
    print("\n----- SIGNATURE (Copy this) -----")
    print(b64_sig)
    return b64_sig

if __name__ == "__main__":
    priv, pub = generate_identity()
    
    script = "print('Hello from Scheduled Job!')"
    print(f"\nScript Content: {script}")
    
    sign_script(priv, script)

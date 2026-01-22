import shutil
import os
import sys

def reset_pki():
    pki_path = "secrets"
    if os.path.exists(pki_path):
        print(f"Removing {pki_path}...")
        try:
            shutil.rmtree(pki_path)
        except Exception as e:
            print(f"Error removing secrets: {e}")
            # Try plain rm shell? No, python is fine usually.
            
    print("Regenerating PKI...")
    # Import regenerate logic from existing script?
    # Or just run it.
    ret = os.system("python regenerate_certs.py")
    if ret != 0:
        print("Regeneration failed.")
        sys.exit(1)
        
    print("Verifying Chain...")
    ret = os.system("python verify_chain_local.py")
    if ret != 0:
        print("Chain Verification Failed.")
        sys.exit(1)
        
    print("PKI Reset Complete. Ready to Deploy.")

if __name__ == "__main__":
    reset_pki()

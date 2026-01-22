from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding

def verify_chain():
    try:
        # Load Root CA
        with open("secrets/ca/root_ca.crt", "rb") as f:
            root_pem = f.read()
            root_cert = x509.load_pem_x509_certificate(root_pem, default_backend())
            
        # Load Server Cert
        with open("secrets/server.crt", "rb") as f:
            server_pem = f.read()
            server_cert = x509.load_pem_x509_certificate(server_pem, default_backend())
            
        print(f"Root Subject: {root_cert.subject}")
        print(f"Server Issuer: {server_cert.issuer}")
        
        # Verify Signature
        public_key = root_cert.public_key()
        try:
            public_key.verify(
                server_cert.signature,
                server_cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                server_cert.signature_hash_algorithm,
            )
            print("SUCCESS: Root CA signatures verifies Server Cert.")
        except Exception as e:
            print(f"FAILURE: Signature verification failed: {e}")
            
    except Exception as e:
        print(f"Error loading certs: {e}")

if __name__ == "__main__":
    verify_chain()

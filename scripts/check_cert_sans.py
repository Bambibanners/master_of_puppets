from cryptography import x509
from cryptography.hazmat.backends import default_backend
import ipaddress

def check_cert():
    cert_path = "secrets/server.crt"
    try:
        with open(cert_path, "rb") as f:
            cert_data = f.read()
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            
            print(f"Subject: {cert.subject}")
            
            try:
                san = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                print("SANs:")
                for name in san.value:
                    print(f" - {name}")
            except x509.ExtensionNotFound:
                print("No SANs found!")
                
    except Exception as e:
        print(f"Error reading cert: {e}")

if __name__ == "__main__":
    check_cert()

import os
import datetime
from datetime import UTC
import ipaddress
import socket
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives import asymmetric
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519

class CertificateAuthority:
    """Internal Certificate Authority for Node mTLS."""
    
    def __init__(self, ca_dir: str = "ca"):
        self.ca_dir = ca_dir
        self.key_path = os.path.join(ca_dir, "root.key")
        self.cert_path = os.path.join(ca_dir, "root.crt")
        
    def ensure_root_ca(self):
        """Generates Root CA if not exists."""
        if os.path.exists(self.key_path) and os.path.exists(self.cert_path):
            return
            
        if not os.path.exists(self.ca_dir):
            os.makedirs(self.ca_dir)
            
        print("🎫 Generating Internal Root CA...")
        # Key
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        with open(self.key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        # Self-Signed Cert
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"Master of Puppets Root CA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Bambibanners"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(UTC)
        ).not_valid_after(
            datetime.datetime.now(UTC) + datetime.timedelta(days=3650) # 10 Years
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True
        ).sign(private_key, hashes.SHA256())
        
        with open(self.cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

    def get_root_cert_pem(self) -> str:
        self.ensure_root_ca()
        with open(self.cert_path, "r") as f:
            return f.read()

    def generate_crl(self, revoked_serials: list) -> bytes:
        """Generates a signed X.509 CRL from a list of revoked certificate serial numbers."""
        self.ensure_root_ca()
        with open(self.key_path, "rb") as f:
            ca_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(self.cert_path, "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())
        now = datetime.datetime.now(UTC)
        builder = x509.CertificateRevocationListBuilder()
        builder = builder.issuer_name(ca_cert.subject)
        builder = builder.last_update(now)
        builder = builder.next_update(now + datetime.timedelta(days=7))
        for serial in revoked_serials:
            revoked = (
                x509.RevokedCertificateBuilder()
                .serial_number(int(serial))
                .revocation_date(now)
                .build()
            )
            builder = builder.add_revoked_certificate(revoked)
        crl = builder.sign(ca_key, hashes.SHA256())
        return crl.public_bytes(serialization.Encoding.PEM)

    def ensure_signing_key(self, secrets_dir: str):
         """Ensures a key exists for CSR signing requests (Node keys)."""
         if not os.path.exists(secrets_dir):
             os.makedirs(secrets_dir)
             
         signing_key_path = os.path.join(secrets_dir, "signing.key")
         verification_key_path = os.path.join(secrets_dir, "verification.key")
         
         if not os.path.exists(signing_key_path):
             private_key = ed25519.Ed25519PrivateKey.generate()
             with open(signing_key_path, "wb") as f:
                 f.write(private_key.private_bytes(
                     encoding=serialization.Encoding.PEM,
                     format=serialization.PrivateFormat.PKCS8,
                     encryption_algorithm=serialization.NoEncryption()
                 ))
             
             with open(verification_key_path, "wb") as f:
                 f.write(private_key.public_key().public_bytes(
                     encoding=serialization.Encoding.PEM,
                     format=serialization.PublicFormat.SubjectPublicKeyInfo
                 ))

    def sign_csr(self, csr_pem: str, hostname: str) -> str:
        """Signs a CSR and returns a PEM Certificate."""
        self.ensure_root_ca()
        
        with open(self.key_path, "rb") as f:
            ca_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(self.cert_path, "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())
            
        csr = x509.load_pem_x509_csr(csr_pem.encode())
        
        cert = x509.CertificateBuilder().subject_name(
            csr.subject
        ).issuer_name(
            ca_cert.subject
        ).public_key(
            csr.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(UTC)
        ).not_valid_after(
            datetime.datetime.now(UTC) + datetime.timedelta(days=825)
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None), critical=True
        ).sign(ca_key, hashes.SHA256())
        
        return cert.public_bytes(serialization.Encoding.PEM).decode()

    def issue_server_cert(self, key_out: str, cert_out: str, sans: list):
        """Issues a Server Certificate signed by the Root CA for HTTPS/mTLS."""
        self.ensure_root_ca()
        
        # 1. Load CA
        with open(self.key_path, "rb") as f:
            ca_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(self.cert_path, "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())
            
        # 2. Generate Server Key
        server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with open(key_out, "wb") as f:
            f.write(server_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        # 3. Build Cert
        cn = sans[0] if sans else "localhost"
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, cn),
        ])
        
        alt_names = []
        for name in sans:
            try:
                ipaddress.ip_address(name)
                alt_names.append(x509.IPAddress(ipaddress.ip_address(name)))
            except ValueError:
                alt_names.append(x509.DNSName(name))
                
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            ca_cert.subject
        ).public_key(
            server_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(UTC)
        ).not_valid_after(
            datetime.datetime.now(UTC) + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName(alt_names), critical=False
        ).sign(ca_key, hashes.SHA256())
        
        with open(cert_out, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

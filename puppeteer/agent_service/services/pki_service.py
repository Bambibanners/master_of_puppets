import logging
import os
from .. import pki

logger = logging.getLogger(__name__)

class PKIService:
    def __init__(self, ca_dir: str = "secrets/ca"):
        self.ca_authority = pki.CertificateAuthority(ca_dir=ca_dir)

    def get_root_cert_pem(self) -> str:
        """Returns the Root CA certificate in PEM format."""
        return self.ca_authority.get_root_cert_pem()

    def sign_csr(self, csr_pem: str, hostname: str) -> str:
        """Signs a CSR and returns the issued certificate."""
        return self.ca_authority.sign_csr(csr_pem, hostname)

# Global Instance
pki_service = PKIService()

"""Generate a D: loopback-only development certificate; never install a trust root."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
root=Path(__file__).resolve().parents[1]
if root.drive.lower()!='d:':raise SystemExit('Local staging files must stay on D:.')
out=root/'.local/final-integration/tls';out.mkdir(parents=True,exist_ok=True)
if not (out/'cert.pem').exists():
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'CampusPulse local staging')])
    cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(datetime.now(timezone.utc)-timedelta(minutes=5)).not_valid_after(datetime.now(timezone.utc)+timedelta(days=3))
          .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'),x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False).sign(key,hashes.SHA256()))
    (out/'key.pem').write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    (out/'cert.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
print('Prepared loopback staging certificate on D:. No Windows/browser trust settings were changed.')

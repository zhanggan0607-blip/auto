from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime, ipaddress

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, 'CN'),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, 'Shanghai'),
    x509.NameAttribute(NameOID.LOCALITY_NAME, 'Shanghai'),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'BidAuto'),
    x509.NameAttribute(NameOID.COMMON_NAME, 'tbjl.sstcp.top'),
])
san = x509.SubjectAlternativeName([
    x509.DNSName('tbjl.sstcp.top'),
    x509.DNSName('www.tbjl.sstcp.top'),
    x509.IPAddress(ipaddress.IPv4Address('8.153.93.123')),
])
cert = (x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
    .add_extension(san, critical=False)
    .sign(key, hashes.SHA256()))

key_path = r'D:\共享文件\AUTO\docker\nginx\server.key'
crt_path = r'D:\共享文件\AUTO\docker\nginx\server.crt'
with open(key_path, 'wb') as f:
    f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
with open(crt_path, 'wb') as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))
print('OK: server.crt + server.key generated (10yr self-signed)')

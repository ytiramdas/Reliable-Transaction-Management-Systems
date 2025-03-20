import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generate_keys(directory, entity_name):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # Save the private key
    with open(os.path.join(directory, "private_key.pem"), "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Save the public key
    with open(os.path.join(directory, "public_key.pem"), "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

def main():
    # Generate keys for servers
    for i in range(1, 8):
        generate_keys(f"keys/servers/server{i}", f"server{i}")

    # Generate keys for clients
    for i in range(1, 11):
        generate_keys(f"keys/clients/client{i}", f"client{i}")

if __name__ == "__main__":
    main()
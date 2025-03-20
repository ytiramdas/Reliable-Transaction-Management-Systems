import grpc
import pbft_pb2
import pbft_pb2_grpc
import time

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

class Client:
    def __init__(self, client_id, servers_keys):
        self.client_id = client_id
        self.servers_keys = servers_keys
        self.private_key = self.load_private_key(f"keys/clients/client{self.client_id}/private_key.pem")
        self.public_key = self.load_public_key(f"keys/clients/client{self.client_id}/public_key.pem")
        self.view_number = 0

    def load_private_key(self, path):
        with open(path, "rb") as key_file:
            return serialization.load_pem_private_key(
                key_file.read(),
                password=None,
            )

    def load_public_key(self, path):
        with open(path, "rb") as key_file:
            return serialization.load_pem_public_key(
                key_file.read()
            )

    def sign_message(self, message):
        return self.private_key.sign(
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

    def run_transaction(self, sender, receiver, amount):
        # Connect to the gRPC server
        with grpc.insecure_channel("localhost:50051") as channel:
            stub = pbft_pb2_grpc.PBFTServiceStub(channel)

            # Create a transaction request
            timestamp = int(time.time() * 1000)
            message = f"{sender}{receiver}{amount}{timestamp}"
            signature = self.sign_message(message)
            transaction = pbft_pb2.Transaction(
                client_id=self.client_id, 
                sender=sender, 
                receiver=receiver,
                amount=amount, 
                signature=signature,
                timestamp=timestamp
            )
            
            # Send transaction to the server
            response = stub.SendTransaction(transaction)

            # Update the view number
            self.view_number = response.view_number

            # Display the server's response
            print(f"Transaction Status: {response.message}, Success: {response.success}")

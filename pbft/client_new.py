import grpc
import pbft_pb2
import pbft_pb2_grpc
import time
import json
import sys
from concurrent import futures

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

class ClientService(pbft_pb2_grpc.ClientServiceServicer):
    def __init__(self, client_id, servers_keys, config_file="config.json"):
        self.client_id = client_id
        self.servers_keys = servers_keys
        self.private_key = self.load_private_key(f"keys/clients/client{self.client_id}/private_key.pem")
        self.public_key = self.load_public_key(f"keys/clients/client{self.client_id}/public_key.pem")
        self.view_number = 0
        self.servers = self.load_config(config_file)['servers']

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
    
    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            return json.load(file)

    def get_primary_server(self):
        primary_id = self.view_number % len(self.servers)
        return self.servers[primary_id]

    def run_transaction(self, sender, receiver, amount):
        primary_server = self.get_primary_server()
        server_address = f"localhost:{primary_server['port']}"

        # Connect to the gRPC server
        with grpc.insecure_channel(server_address) as channel:
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

    def SendTransaction(self, request, context):
        self.run_transaction(request.sender, request.receiver, request.amount)
        return pbft_pb2.TransactionStatus(message="Transaction processed", success=True, view_number=self.view_number)

def serve(client_id, config, servers_keys):
    client_config = next(client for client in config['clients'] if client['id'] == client_id)
    port = client_config['port']

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pbft_pb2_grpc.add_ClientServiceServicer_to_server(ClientService(client_id, servers_keys), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f'Client {client_id} running on port {port}')
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python client.py <client_id>")
    else:
        client_id = int(sys.argv[1])
        with open('config.json', 'r') as f:
            config = json.load(f)
        with open('keys.json', 'r') as f:
            keys_config = json.load(f)

        servers_keys = {}
        for server in keys_config['servers']:
            server_public_key_path = server['public_key']
            with open(server_public_key_path, "rb") as key_file:
                servers_keys[server['id']] = serialization.load_pem_public_key(key_file.read())

        serve(client_id, config, servers_keys)
import grpc
from concurrent import futures
import time
import json
import sys
import hashlib
import asyncio

import pbft_pb2
import pbft_pb2_grpc

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

# Import threshold signature library
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, pair
from charm.schemes.pksig.pksig_bls import BLS

class PBFTService(pbft_pb2_grpc.PBFTServiceServicer):
    def __init__(self, server_id, server_name, other_servers, clients_keys, servers_keys):
        self.server_id = server_id
        self.server_name = server_name
        self.other_servers = other_servers
        self.clients_keys = clients_keys
        self.servers_keys = servers_keys
        self.is_active = False
        self.is_byzantine = False
        self.view = 0
        self.sequence_number = 0
        self.log = []
        
        self.group = PairingGroup('SS512')
        self.bls = BLS(self.group)

        self.balances = {
            "A": 10, 
            "B": 10, 
            "C": 10, 
            "D": 10,
            "E": 10,
            "F": 10,
            "G": 10,
            "H": 10,
            "I": 10,
            "J": 10
            }
        
        self.private_key = self.load_private_key(f"keys/servers/server{self.server_id}/private_key.pem")
        self.public_key = self.load_public_key(f"keys/servers/server{self.server_id}/public_key.pem")

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
    
    def verify_signature(self, message, signature, public_key):
        try:
            public_key.verify(
                signature,
                message.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except:
            return False
    
    def digest_message(self, message):
        return hashlib.sha256(message.encode()).hexdigest()
    
    async def pbft_protocol(self, transaction):
        # Create a digest of the transaction
        digest = self.digest_message(str(transaction))

        # Create a PRE-PREPARE message
        pre_prepare_message = pbft_pb2.PrePrepareMessage(
            view=self.view,
            sequence_number=self.sequence_number,
            digest=digest,
            signature=self.sign_message(f"{self.view}{self.sequence_number}{digest}"),
            transaction=transaction,
            request_type=pbft_pb2.PREPREPARE
        )

        # Send the PRE-PREPARE message to all other nodes asynchronously
        async def send_pre_prepare(server_address):
            async with grpc.aio.insecure_channel(server_address) as channel:
                stub = pbft_pb2_grpc.PBFTServiceStub(channel)
                response = await stub.PrePrepare(pre_prepare_message)
                print(f"Pre-prepare response from {server_address}: {response.message}")

        self.log.append(pre_prepare_message)
        await asyncio.gather(*(send_pre_prepare(server_address) for server_address in self.other_servers))

        # Increment the sequence number
        self.sequence_number += 1
    
    def SendTransaction(self, request, context):
        if not self.is_active:
            return pbft_pb2.TransactionStatus(message="Server is not active", success=False, view_number=self.view)
        
        print(f"Received transaction: {request.sender} -> {request.receiver} : {request.amount}, timestamp: {request.timestamp} from client {request.client_id}")
        client_id = request.client_id
        sender = request.sender
        receiver = request.receiver
        amount = request.amount
        signature = request.signature
        timestamp = request.timestamp

        client_public_key = self.clients_keys[client_id]

        # Verify the signature
        if not self.verify_signature(f"{sender}{receiver}{amount}{timestamp}", signature, client_public_key):
            return pbft_pb2.TransactionStatus(message="Invalid signature", success=False, view_number=self.view)
        
        print(f"Start PBFT protocol for transaction {sender} -> {receiver} : {amount}")
        asyncio.run(self.pbft_protocol(request))

        # Simple logic for transaction processing (without consensus)
        if sender in self.balances and receiver in self.balances and self.balances[sender] >= amount:
            self.balances[sender] -= amount
            self.balances[receiver] += amount
            message = f"Transaction processed: {sender} -> {receiver} : {amount}"
            success = True
        else:
            message = f"Transaction failed: Insufficient funds or invalid accounts"
            success = False

        print(f"Processed transaction: {message}")
        self.printDB()
        return pbft_pb2.TransactionStatus(message=message, success=success, view_number=self.view)
    
    def PrePrepare(self, request, context):
        print(f"Pre-prepare message received: {request.transaction.sender} -> {request.transaction.receiver} : {request.transaction.amount}")
        print(f"View: {request.view}, Sequence number: {request.sequence_number}")
        if self.view != request.view:
            return pbft_pb2.PrePrepareResponse(message="Incorrect view", success=False)
        print("View is correct")
        
        digest = self.digest_message(str(request.transaction))
        if digest != request.digest:
            return pbft_pb2.PrePrepareResponse(message="Incorrect digest", success=False)
        print("Digest is correct")
        
        primary_server_id = (request.view % 7) + 1
        if not self.verify_signature(f"{request.view}{request.sequence_number}{request.digest}", request.signature, self.servers_keys[primary_server_id]):
            return pbft_pb2.PrePrepareResponse(message="Invalid signature", success=False)
        print("Signature is valid")

        for log_entry in self.log:
            if log_entry.view == request.view and log_entry.sequence_number == request.sequence_number:
                return pbft_pb2.PrePrepareResponse(message="Conflicting PRE-PREPARE message", success=False)
        print("No conflicting PRE-PREPARE message")
        
        self.log.append(request)
        # print(f'server {self.server_id} log: {self.log}')

        # Send PREPARE message to the primary only
        prepare_message = pbft_pb2.PrepareMessage(
            view=request.view,
            sequence_number=request.sequence_number,
            digest=request.digest,
            replica_id=self.server_id,
            signature=self.sign_message(f"{request.view}{request.sequence_number}{request.digest}{self.server_id}"),
            request_type=pbft_pb2.PREPARE
        )

        primary_server_address = f"localhost:{self.other_servers[primary_server_id - 1].split(':')[1]}"

        async def send_prepare(server_address):
            async with grpc.aio.insecure_channel(server_address) as channel:
                stub = pbft_pb2_grpc.PBFTServiceStub(channel)
                response = await stub.Prepare(prepare_message)
                print(f"Prepare response from {server_address}: {response.message}")

        asyncio.run(send_prepare(primary_server_address))

        return pbft_pb2.PrePrepareResponse(message="Pre-prepare accepted", success=True)
    
    def Prepare(self, request, context):
        print(f"Prepare message received from replica {request.replica_id}")
        print(f"View: {request.view}, Sequence number: {request.sequence_number}, Digest: {request.digest}")
        
        if self.view != request.view:
            return pbft_pb2.PrepareResponse(message="Incorrect view", success=False)
        print("View is correct")
        
        if not self.verify_signature(f"{request.view}{request.sequence_number}{request.digest}{request.replica_id}", request.signature, self.servers_keys[request.replica_id]):
            return pbft_pb2.PrepareResponse(message="Invalid signature", success=False)
        print("Signature is valid")

        print(self.log)
        preprepare_message = None
        for log_entry in self.log:
            if log_entry.request_type == pbft_pb2.PREPREPARE and log_entry.view == request.view and log_entry.sequence_number == request.sequence_number:
                preprepare_message = log_entry
                break
        
        # print(preprepare_message)
        if not preprepare_message:
            return pbft_pb2.PrepareResponse(message="No matching PrePrepare message", success=False)
        
        print("Matching PRE-PREPARE message found")
        print(f"Pre-prepare message: {preprepare_message.transaction.sender} -> {preprepare_message.transaction.receiver} : {preprepare_message.transaction.amount}")
        
        # Verify the digest of the received Prepare message
        if preprepare_message.digest != request.digest:
            return pbft_pb2.PrepareResponse(message="Digest mismatch", success=False)
        print("Digest is correct")

        # Collect all Prepare responses
        self.log.append(request)
        # print(f'server {self.server_id} Prepare log: {self.logs}')
        
        # Check if we have received 2f + 1 Prepare responses
        f = 2
        prepare_responses = [msg for msg in self.log if msg.view == request.view and msg.sequence_number == request.sequence_number and msg.request_type == pbft_pb2.PREPARE]
        if len(prepare_responses) >= 2 * f + 1:
            combined_signature = self.combine_signatures(prepare_responses)
            combined_message = pbft_pb2.CombinedPrepareMessage(
                view=request.view,
                sequence_number=request.sequence_number,
                digest=request.digest,
                signatures=combined_signature
            )
            print(f"Combined message: {combined_message}")
            # Send combined message to all other servers
            asyncio.run(self.send_combined_prepare(combined_message))
        
        return pbft_pb2.PrepareResponse(message="Prepare accepted", success=True)
    
    def combine_signatures(self, prepare_responses):
        # Combine signatures using threshold signature scheme
        signatures = [response.signature for response in prepare_responses]
        combined_signature = self.bls.combine_signatures(signatures)
        return combined_signature

    async def send_combined_prepare(self, combined_message):
        async def send_combined(server_address):
            async with grpc.aio.insecure_channel(server_address) as channel:
                stub = pbft_pb2_grpc.PBFTServiceStub(channel)
                response = await stub.CombinedPrepare(combined_message)
                print(f"Combined prepare response from {server_address}: {response.message}")

        await asyncio.gather(*(send_combined(server_address) for server_address in self.other_servers))

    def CombinedPrepare(self, request, context):
        print(f"Combined prepare message received: {request.view}, {request.sequence_number}, {request.digest}")
        # Verify the combined signature
        if not self.bls.verify_combined_signature(request.signatures, request.digest):
            return pbft_pb2.CombinedPrepareResponse(message="Invalid combined signature", success=False)
        print("Combined signature is valid")
        return pbft_pb2.CombinedPrepareResponse(message="Combined prepare accepted", success=True)
    
    def SetActiveStatus(self, request, context):
        self.is_active = request.is_active
        print(f"Server {self.server_id} active status set to {self.is_active}")
        return pbft_pb2.SetActiveStatusResponse(message=f"Server {self.server_id} active status set to {self.is_active}", success=True)

    def SetByzantineStatus(self, request, context):
        self.is_byzantine = request.is_byzantine
        print(f"Server {self.server_id} Byzantine status set to {self.is_byzantine}")
        return pbft_pb2.SetByzantineStatusResponse(message=f"Server {self.server_id} Byzantine status set to {self.is_byzantine}", success=True)

    def printDB(self):
        print(f"Server {self.server_id} balances: {self.balances}")


def serve(server_id, config, clients_keys, servers_keys):
    # Extract the port for the current server
    current_server = next(server for server in config['servers'] if server['id'] == server_id)
    port = current_server['port']
    
    # Construct the list of other servers
    other_servers = [f"localhost:{server['port']}" for server in config['servers'] if server['id'] != server_id]

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server_name = next(server['name'] for server in config['servers'] if server['id'] == server_id)
    pbft_pb2_grpc.add_PBFTServiceServicer_to_server(PBFTService(server_id, server_name, other_servers, clients_keys, servers_keys), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f'Server {server_id} running on port {port}')
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python server.py <server_id>")
    else:
        server_id = int(sys.argv[1])
        with open('config.json', 'r') as f:
            config = json.load(f)
        with open('keys.json', 'r') as f:
            keys_config = json.load(f)

        clients_keys = {}
        for client in keys_config['clients']:
            client_public_key_path = client['public_key']
            with open(client_public_key_path, "rb") as key_file:
                clients_keys[client['id']] = serialization.load_pem_public_key(key_file.read())
        
        servers_keys = {}
        for server in keys_config['servers']:
            server_public_key_path = server['public_key']
            with open(server_public_key_path, "rb") as key_file:
                servers_keys[server['id']] = serialization.load_pem_public_key(key_file.read())

        serve(server_id, config, clients_keys, servers_keys)
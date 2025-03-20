import grpc
from concurrent import futures
import time
import json
import sys
import hashlib
import asyncio

import pbft_pb2
import pbft_pb2_grpc

import controller_pb2
import controller_pb2_grpc

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
import uvloop

PRINT_STATEMENTS = True

# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

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
        self.f = 2
        self.last_executed = 0

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

    def Reset(self, request, context):
        self.view = 0
        self.sequence_number = 0
        self.log = []
        self.last_executed = 0
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
        return pbft_pb2.ResetResponse(success=True)

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
    
    async def pbft_protocol(self, transaction, view, sequence_number):
        # Create a digest of the transaction
        digest = self.digest_message(str(transaction))

        # Create a PRE-PREPARE message
        pre_prepare_message = pbft_pb2.PrePrepareMessage(
            view=view,
            sequence_number=sequence_number,
            digest=digest,
            signature=self.sign_message(f"{view}{sequence_number}{digest}"),
            transaction=transaction,
            request_type=pbft_pb2.PREPREPARE
        )

        self.log.append(pre_prepare_message)

        # Add the primary's own PrepareMessage to the list of valid responses
        own_prepare_message = pbft_pb2.PrepareResponse(
            view=view,
            sequence_number=sequence_number,
            digest=digest,
            replica_id=self.server_id,
            signature=self.sign_message(f"{view}{sequence_number}{digest}{self.server_id}"),
            request_type=pbft_pb2.PREPARE
        )

        tasks = [self.send_pre_prepare(server_address, pre_prepare_message) for server_address in self.other_servers]
        prepare_responses = await asyncio.gather(*tasks)
        # if PRINT_STATEMENTS:
        #     print(f"Received responses: {prepare_responses}")
        
        prepare_responses.append(own_prepare_message)
        # Validate the responses
        valid_prepare_responses = self.validate_prepare_messages(prepare_responses)
        # if PRINT_STATEMENTS:
        #     print(f"Valid responses: {valid_prepare_responses}")
        
        self.printLog()
        
        # Check if we have received 2f + 1 valid responses including self
        if len(valid_prepare_responses) >= 2 * self.f + 1:
            prepared_message = pbft_pb2.PreparedMessage(responses=valid_prepare_responses, server_id=self.server_id)
            tasks = [self.send_prepared(server_address, prepared_message) for server_address in self.other_servers]
            commit_responses = await asyncio.gather(*tasks)
            if PRINT_STATEMENTS:
                print(f"\nReceived commit responses: {commit_responses}")

            # Add the primary's own CommitResponse to the list of valid responses
            own_commit_message = pbft_pb2.CommitResponse(
                view=view,
                sequence_number=sequence_number,
                digest=digest,
                replica_id=self.server_id,
                signature=self.sign_message(f"{view}{sequence_number}{digest}{self.server_id}"),
                request_type=pbft_pb2.COMMIT,
                message="Commit message",
                success=True
            )
            commit_responses.append(own_commit_message)

            # Validate the commit responses
            valid_commit_responses = self.validate_commit_messages(commit_responses)
            if PRINT_STATEMENTS:
                print(f"Valid commit responses: {valid_commit_responses}")

            # Check if we have received 2f + 1 valid commit responses including self
            if len(valid_commit_responses) >= 2 * self.f + 1:
                asyncio.create_task(self.execute_transaction(transaction, self.view, self.sequence_number, digest))

                committed_message = pbft_pb2.CommittedMessage(responses=valid_commit_responses, server_id=self.server_id)
                tasks = [self.send_committed(server_address, committed_message) for server_address in self.other_servers]
                await asyncio.gather(*tasks)
                print(f"Sent Final commit messages to all other servers")

                if pre_prepare_message:
                    transaction = pre_prepare_message.transaction
                    asyncio.create_task(self.execute_transaction(transaction, view, sequence_number, digest))
                    self.printLog()
                else:
                    print("PrePrepareMessage not found")
                    self.printLog()

        self.printLog()

    # Send the PRE-PREPARE message to all other nodes asynchronously
    async def send_pre_prepare(self, server_address, pre_prepare_message):
        if PRINT_STATEMENTS:
            print(f"Sending pre-prepare message to {server_address}")
        try:
            async with grpc.aio.insecure_channel(server_address) as channel:
                stub = pbft_pb2_grpc.PBFTServiceStub(channel)
                response = await stub.PrePrepare(pre_prepare_message)
                if PRINT_STATEMENTS:
                    print(f"Pre-prepare response from {server_address}: {response.message}")
                return response
        except grpc.RpcError as e:
            if PRINT_STATEMENTS:
                print(f"Failed to communicate with {server_address}: {e}")
            return None
            
    async def send_prepared(self, server_address, prepared_message):
        if PRINT_STATEMENTS:
            print(f"Sending prepared message to {server_address}")
            # print(f"Prepared message: {prepared_message}")
        try:
            async with grpc.aio.insecure_channel(server_address) as channel:
                stub = pbft_pb2_grpc.PBFTServiceStub(channel)
                response = await stub.Prepare(prepared_message)
                if PRINT_STATEMENTS:
                    print(f"Prepared response from {server_address}: {response.message}")
                return response
        except grpc.RpcError as e:
            if PRINT_STATEMENTS:
                print(f"Failed to communicate with {server_address}: {e}")
                return None 

    async def send_committed(self, server_address, committed_message):
        if PRINT_STATEMENTS:
            print(f"Sending committed message to {server_address}")
            # print(f"Committed message: {committed_message}")
        try:
            async with grpc.aio.insecure_channel(server_address) as channel:
                stub = pbft_pb2_grpc.PBFTServiceStub(channel)
                response = await stub.Commit(committed_message)
                if PRINT_STATEMENTS:
                    print(f"Committed response from {server_address}: {response.message}")
                return response
        except grpc.RpcError as e:
            if PRINT_STATEMENTS:
                print(f"Failed to communicate with {server_address}: {e}")
            return None
    
    def validate_commit_messages(self, responses):
        valid_responses = []
        print(f"\nValidating Commit messages")
        for response in responses:
            if response is None:
                continue
            
            print(f"Commit message received from replica {response.replica_id}")
            print(f"View: {response.view}, Sequence number: {response.sequence_number}, Digest: {response.digest}")
            
            if self.view != response.view:
                print("Incorrect view")
                continue
            print("View is correct")
            
            if not self.verify_signature(f"{response.view}{response.sequence_number}{response.digest}{response.replica_id}", response.signature, self.servers_keys[response.replica_id]):
                print("Invalid signature")
                continue
            print("Signature is valid")

            prepare_message = None
            for log_entry in self.log:
                if log_entry.request_type == pbft_pb2.PREPARE and log_entry.view == response.view and log_entry.sequence_number == response.sequence_number:
                    prepare_message = log_entry
                    break
            
            if not prepare_message:
                print("No matching Prepare message")
                continue
            
            print("Matching PREPARE message found")
            
            # Verify the digest of the received Commit message
            if prepare_message.digest != response.digest:
                print("Digest mismatch")
                continue
            print("Digest is correct")

            self.log.append(response)
            # Collect all valid Commit responses
            valid_responses.append(response)
        return valid_responses

    def validate_prepare_messages(self, responses):
        valid_responses = []
        print(f"\nValidating Prepare messages")
        for response in responses:
            if response is None:
                continue
        
            print(f"Prepare message received from replica {response.replica_id}")
            print(f"View: {response.view}, Sequence number: {response.sequence_number}, Digest: {response.digest}")
            
            if self.view != response.view:
                print("Incorrect view")
                continue
            print("View is correct")
            
            print(self.servers_keys[response.replica_id])
            if not self.verify_signature(f"{response.view}{response.sequence_number}{response.digest}{response.replica_id}", response.signature, self.servers_keys[response.replica_id]):
                print("Invalid signature")
                continue
            print("Signature is valid")

            preprepare_message = None
            for log_entry in self.log:
                if log_entry.request_type == pbft_pb2.PREPREPARE and log_entry.view == response.view and log_entry.sequence_number == response.sequence_number:
                    preprepare_message = log_entry
                    break
            
            if not preprepare_message:
                print("No matching PrePrepare message")
                continue
            
            print("Matching PRE-PREPARE message found")
            print(f"Pre-prepare message: {preprepare_message.transaction.sender} -> {preprepare_message.transaction.receiver} : {preprepare_message.transaction.amount}")
            
            # Verify the digest of the received Prepare message
            if preprepare_message.digest != response.digest:
                print("Digest mismatch")
                continue
            print("Digest is correct")

            self.log.append(response)
            # Collect all valid Prepare responses
            valid_responses.append(response)
        return valid_responses
    
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
        
        # Increment the sequence number
        self.sequence_number += 1

        print(f"Start PBFT protocol for transaction {sender} -> {receiver} : {amount}")
        asyncio.run(self.pbft_protocol(request, self.view, self.sequence_number))

        self.printDB()
        message = f"Transaction gone through pbft: {sender} -> {receiver} : {amount}"
        success = True
        return pbft_pb2.TransactionStatus(message=message, success=success, view_number=self.view)
    
    def PrePrepare(self, request, context):
        print(f"Pre-prepare message received: {request.transaction.sender} -> {request.transaction.receiver} : {request.transaction.amount}")
        print(f"View: {request.view}, Sequence number: {request.sequence_number}")
        if self.view != request.view:
            return pbft_pb2.PrepareResponse(message="Incorrect view", success=False)
        print("View is correct")
        
        digest = self.digest_message(str(request.transaction))
        if digest != request.digest:
            return pbft_pb2.PrepareResponse(message="Incorrect digest", success=False)
        print("Digest is correct")
        
        primary_server_id = (request.view % 7) + 1
        if not self.verify_signature(f"{request.view}{request.sequence_number}{request.digest}", request.signature, self.servers_keys[primary_server_id]):
            return pbft_pb2.PrepareResponse(message="Invalid signature", success=False)
        print("Signature is valid")

        for log_entry in self.log:
            if log_entry.view == request.view and log_entry.sequence_number == request.sequence_number:
                return pbft_pb2.PrepareResponse(message="Conflicting PRE-PREPARE message", success=False)
        print("No conflicting PRE-PREPARE message")
        
        self.log.append(request)
        # print(f'server {self.server_id} log: {self.log}')

        # Send PREPARE message to the primary only
        print(f"Sending prepare message to primary server {primary_server_id}")
        prepare_message = pbft_pb2.PrepareResponse(
            view=request.view,
            sequence_number=request.sequence_number,
            digest=request.digest,
            replica_id=self.server_id,
            signature=self.sign_message(f"{request.view}{request.sequence_number}{request.digest}{self.server_id}"),
            request_type=pbft_pb2.PREPARE,
            message = "Prepare message",
            success = True
        )

        return prepare_message
    
    def Prepare(self, request, context):
        print(f"Prepared message received from replica {request.server_id}")
        # Verify the combined signature
        valid_responses = self.validate_prepare_messages(request.responses)
        if len(valid_responses) == len(request.responses):
            first_response = valid_responses[0]
            view = first_response.view
            sequence_number = first_response.sequence_number
            digest = first_response.digest
            print(f"View: {view}, Sequence number: {sequence_number}, Digest: {digest}")

            print("Valid Prepare messages, sending Commit message")
            commit_message = pbft_pb2.CommitResponse(
                view=view,
                sequence_number=sequence_number,
                digest=digest,
                replica_id=self.server_id,
                signature=self.sign_message(f"{view}{sequence_number}{digest}{self.server_id}"),
                request_type=pbft_pb2.COMMIT,
                message = "Commit message",
                success = True
            )
        else:
            commit_message = pbft_pb2.CommitResponse(
                message="Invalid Prepare messages",
                success=False
            )
        self.printLog()
        return commit_message
    
    def Commit(self, request, context):
        print(f"Commit message received from replica {request.server_id}")
        # Verify the combined signature
        valid_responses = self.validate_commit_messages(request.responses)
        if len(valid_responses) == len(request.responses):
            first_response = valid_responses[0]
            view = first_response.view
            sequence_number = first_response.sequence_number
            digest = first_response.digest
            print(f"View: {view}, Sequence number: {sequence_number}, Digest: {digest}")

            print("Valid Commit messages")

            # Extract the transaction from the PrePrepareMessage
            pre_prepare_message = self.get_pre_prepare_message(view, sequence_number)
            if pre_prepare_message:
                transaction = pre_prepare_message.transaction
                asyncio.run(self.execute_transaction(transaction, view, sequence_number, digest))
                self.printLog()
                return pbft_pb2.CommittedResponse(message="Commit message", success=True)
            else:
                print("PrePrepareMessage not found")
                self.printLog()
                return pbft_pb2.CommittedResponse(message="PrePrepareMessage not found", success=False)
        else:
            self.printLog()
            return pbft_pb2.CommittedResponse(message="Invalid Commit messages", success=False)
    
    def get_pre_prepare_message(self, view, sequence_number):
        for log_entry in self.log:
            if log_entry.request_type == pbft_pb2.PREPREPARE and log_entry.view == view and log_entry.sequence_number == sequence_number:
                return log_entry
        return None

    async def execute_transaction(self, transaction, view, sequence_number, digest):
        print(f"Executing transaction with sequence number: {sequence_number}, view: {view}, and digest: {digest}")
        
        # Wait until the last_executed sequence number is sequence_number - 1
        print(f"Last executed: {self.last_executed}")
        print(f"Current sequence number: {sequence_number}")
        while self.last_executed != sequence_number - 1:
            print(f"Waiting for previous sequence number to be executed. Last executed: {self.last_executed}")
            await asyncio.sleep(0.02)  # Wait for 10 milliseconds before checking again

        sender = transaction.sender
        receiver = transaction.receiver
        amount = transaction.amount

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
        self.last_executed = sequence_number
        print("sending reply to client")
        await self.send_reply_to_client(transaction, view, sequence_number, digest, success)

    async def send_reply_to_client(self, transaction, view, sequence_number, digest, status):
        print(f"Sending reply to client {transaction.client_id}")
        reply_message = controller_pb2.ReplyMessage(
            view=view,
            sequence_number=sequence_number,
            client_id=transaction.client_id,
            replica_id=self.server_id,
            result=f"Transaction {transaction.sender} -> {transaction.receiver} : {transaction.amount} committed",
            signature=self.sign_message(f"{view}{sequence_number}{transaction.client_id}{self.server_id}{digest}"),
            status=status
        )
        client_address = "localhost:50071"
        async with grpc.aio.insecure_channel(client_address) as channel:
            stub = controller_pb2_grpc.ControllerServiceStub(channel)
            await stub.HandleReply(reply_message)

    def SetActiveStatus(self, request, context):
        self.is_active = request.is_active
        print(f"Server {self.server_id} active status set to {self.is_active}")
        return pbft_pb2.SetActiveStatusResponse(message=f"Server {self.server_id} active status set to {self.is_active}", success=True)

    def SetByzantineStatus(self, request, context):
        self.is_byzantine = request.is_byzantine
        print(f"Server {self.server_id} Byzantine status set to {self.is_byzantine}")
        return pbft_pb2.SetByzantineStatusResponse(message=f"Server {self.server_id} Byzantine status set to {self.is_byzantine}", success=True)

    def PrintLog(self, request, context):
        self.printLog()
        return pbft_pb2.PrintResponse(response=True)
    
    def PrintDB(self, request, context):
        self.printDB()
        return pbft_pb2.PrintResponse(response=True)
    
    def count_commit_messages(self, view, sequence_number):
        count = 0
        for log_entry in self.log:
            if log_entry.request_type == pbft_pb2.COMMIT and log_entry.view == view and log_entry.sequence_number == sequence_number:
                count += 1
        return count
    
    def count_prepare_messages(self, view, sequence_number):
        count = 0
        for log_entry in self.log:
            if log_entry.request_type == pbft_pb2.PREPARE and log_entry.view == view and log_entry.sequence_number == sequence_number:
                count += 1
        return count
    
    def PrintStatus(self, request, context):
        sequence_number = request.sequence_number
        view = self.view
        status = "X"  # Default status is No Status

        preprepare_message = self.get_pre_prepare_message(view, sequence_number)
        if preprepare_message:
            print(f"Transaction: {preprepare_message.transaction.sender}, {preprepare_message.transaction.receiver} -> {preprepare_message.transaction.amount}")
            if self.last_executed >= sequence_number:
                status = "E"
            elif self.count_commit_messages(view, sequence_number) >= 2 * self.f + 1:
                status = "C"
            elif self.count_prepare_messages(view, sequence_number) >= 2 * self.f + 1:
                status = "P"
            else:
                status = "PP"

        print(f"Server {self.server_id} status for sequence number {sequence_number}: {status}")
        return pbft_pb2.PrintResponse(response=True)

    
    def printDB(self):
        print(f"Server {self.server_id} balances:")
        for account, balance in self.balances.items():
            print(f"  {account}: {balance}")

    def printLog(self):
        print(f"Server {self.server_id} Log:")
        for entry in self.log:
            if entry.request_type == pbft_pb2.PREPREPARE:
                print(f"PRE-PREPARE: {entry.transaction.sender} -> {entry.transaction.receiver} : {entry.transaction.amount} at time {entry.transaction.timestamp} view {entry.view} sequence number {entry.sequence_number}")
            elif entry.request_type == pbft_pb2.PREPARE:
                print(f"PREPARE: {entry.replica_id} for view {entry.view} sequence number {entry.sequence_number}")
            elif entry.request_type == pbft_pb2.COMMIT:
                print(f"COMMIT: {entry.replica_id} for view {entry.view} sequence number {entry.sequence_number}")
            else:
                print("Unknown message type")


def serve(server_id, config, clients_keys, servers_keys):
    # Extract the port for the current server
    current_server = next(server for server in config['servers'] if server['id'] == server_id)
    port = current_server['port']
    
    # Construct the list of other servers
    other_servers = [f"localhost:{server['port']}" for server in config['servers'] if server['id'] != server_id]

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
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
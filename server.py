import grpc
from concurrent import futures
import time
import json
import sys
import paxos_pb2
import paxos_pb2_grpc

class PaxosService(paxos_pb2_grpc.PaxosServicer):
    def __init__(self, server_id, other_servers):
        self.server_id = server_id
        self.other_servers = other_servers
        self.balance = 100  # Initialize balances
        self.local_log = []
        self.commited_log = []
        self.accept_num = None
        self.accept_val = None

    def HandleTransaction(self, request, context):
        sender = request.sender
        receiver = request.receiver
        amount = request.amount
        print(f"Received transaction: {sender} -> {receiver} : {amount}")
        if self.balance >= amount:
            self.balance -= amount
            self.local_log.append(request)
            print(f"Transaction successful in server {self.server_id}: {sender} -> {receiver} : {amount}")
            print(f"Updated balance in server {self.server_id}: {self.balance}")
            return paxos_pb2.CommitResponse(status=True)
        else:
            print(f"Transaction failed in server {self.server_id}: {sender} -> {receiver} : {amount}")
            self.initiate_leader_election()
            return paxos_pb2.CommitResponse(status=False)
        
    def Prepare(self, request, context):
        ballot_number = request.ballot_num
        server_id = request.id
        print(f"Received prepare message from {server_id} with ballot number {ballot_number}")

        if self.accept_num and self.accept_val:
            # There is a value that has been proposed and accepted but not decided
            print(f"Informing leader about the latest accepted value and ballot number")
            if self.accept_num > ballot_number:
                return paxos_pb2.PromiseResponse(
                    ballot_num=ballot_number,
                    server_id=server_id,
                    accept_num=self.accept_num,
                    accept_val=self.accept_val,
                    transactions=[]
            )
        elif self.local_log:
            # No such value, inform leader about locally processed transactions
            print(f"Informing leader about locally processed transactions")
            return paxos_pb2.PromiseResponse(
                ballot_num=ballot_number,
                server_id=server_id,
                accept_num=self.accept_num,
                accept_val=[],
                transactions=self.local_log
            )
        else:
            # Reject the prepare message
            print(f"Rejecting prepare message from {server_id} with ballot number {ballot_number}")
            return paxos_pb2.PromiseResponse(
                server_id=server_id,
                ballot_num=-1  # Denotes rejection
            )


    def initiate_leader_election(self):
        ballot_num = 1  # Change this to a consecutive number
        print(f"Initiating leader election with ballot number: {ballot_num}")
        print("Other servers: ", self.other_servers)
        
        for server_address in self.other_servers:
            print(f"Sending prepare message to {server_address}")
            try:
                with grpc.insecure_channel(server_address) as channel:
                    stub = paxos_pb2_grpc.PaxosStub(channel)
                    print("stub created")
                    response = stub.Prepare(paxos_pb2.PrepareRequest(ballot_num=ballot_num, id=self.server_id))
                    print(f"Received ACK from {server_address}: {response}")
            except grpc.RpcError as e:
                print(f"Failed to communicate with {server_address}: {e}")

def serve(server_id, config):
    # Extract the port for the current server
    current_server = next(server for server in config['servers'] if server['id'] == server_id)
    port = current_server['port']
    
    # Construct the list of other servers
    other_servers = [f"localhost:{server['port']}" for server in config['servers'] if server['id'] != server_id]
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    paxos_pb2_grpc.add_PaxosServicer_to_server(PaxosService(server_id, other_servers), server)
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
        serve(server_id, config)
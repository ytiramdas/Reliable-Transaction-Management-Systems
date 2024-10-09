import grpc
from concurrent import futures
import time
import paxos_pb2
import paxos_pb2_grpc

class PaxosService(paxos_pb2_grpc.PaxosServicer):
    def __init__(self):
        self.balance = 100 # Initialize balances

    def HandleTransaction(self, request, context):
        sender = request.sender
        receiver = request.receiver
        amount = request.amount

        if self.balance >= amount:
            self.balance -= amount
            print(f"Transaction successful: {sender} -> {receiver} : {amount}")
            print(f"Updated balances: {self.balance}")
            return paxos_pb2.CommitResponse(status=True)
        else:
            print(f"Transaction failed: {sender} -> {receiver} : {amount}")
            return paxos_pb2.CommitResponse(status=False)
        

def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    paxos_pb2_grpc.add_PaxosServicer_to_server(PaxosService(), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f'Server running on port {port}')
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
    else:
        serve(sys.argv[1])

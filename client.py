import grpc
import paxos_pb2
import paxos_pb2_grpc
import csv

sender_to_port = {
    'A': 50051,
    'B': 50052,
    'C': 50053,
    'D': 50054,
    'E': 50055
}

def run_client(port, sender, receiver, amount):
    with grpc.insecure_channel(f'localhost:{port}') as channel:
        stub = paxos_pb2_grpc.PaxosStub(channel)
        response = stub.HandleTransaction(paxos_pb2.Transaction(sender=sender, receiver=receiver, amount=amount))
        print(f"Client received: {'Success' if response.status else 'Failure'}")


if __name__ == '__main__':
    with open('data.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            sender = row['sender']
            receiver = row['receiver']
            amount = int(row['amount'])
            port = sender_to_port.get(sender)
            if port:
                run_client(port, sender, receiver, amount)

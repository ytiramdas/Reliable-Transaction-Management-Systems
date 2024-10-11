import grpc
import paxos_pb2
import paxos_pb2_grpc
import csv
import json

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config

def construct_sender_to_port_mapping(config):
    return {server['name']: server['port'] for server in config['servers']}

def run_client(port, sender, receiver, amount):
    with grpc.insecure_channel(f'localhost:{port}') as channel:
        stub = paxos_pb2_grpc.PaxosStub(channel)
        response = stub.HandleTransaction(paxos_pb2.Transaction(sender=sender, receiver=receiver, amount=amount))
        print(f"Client received: {'Success' if response.status else 'Failure'}")

if __name__ == '__main__':
    config = load_config('config.json')
    sender_to_port = construct_sender_to_port_mapping(config)
    
    with open('data.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            sender = row['sender']
            receiver = row['receiver']
            amount = int(row['amount'])
            port = sender_to_port.get(sender)
            if port:
                run_client(port, sender, receiver, amount)
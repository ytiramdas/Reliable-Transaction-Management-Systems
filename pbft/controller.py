import csv
import json
import grpc
import controller_pb2
import controller_pb2_grpc
import pbft_pb2
import pbft_pb2_grpc
from concurrent.futures import ThreadPoolExecutor, as_completed
from cryptography.hazmat.primitives import serialization
from client import Client
from concurrent import futures
import threading
import time

PRINT_STATEMENTS = True

class ControllerService(controller_pb2_grpc.ControllerServiceServicer):
    def __init__(self, config_file, keys_file, data_file):
        self.clients = []
        self.sender_to_port = {}
        self.load_config(config_file)
        self.load_keys(keys_file)
        self.parse_input_data(data_file)
        self.initialize_clients()
        self.log = {}
        self.executed_transactions = set()
        self.f = 2

    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            config = json.load(file)
        self.sender_to_port = {server['name']: server['port'] for server in config['servers']}

    def load_keys(self, keys_file):
        with open(keys_file, 'r') as file:
            keys_config = json.load(file)
        self.servers_keys = {}
        for server in keys_config['servers']:
            server_public_key_path = server['public_key']
            with open(server_public_key_path, "rb") as key_file:
                self.servers_keys[server['id']] = serialization.load_pem_public_key(key_file.read())

    def parse_input_data(self, data_file):
        self.sets = []
        cur_set = None
        with open(data_file, mode='r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if row[0]:
                    if cur_set:
                        self.sets.append(cur_set)
                    set_id = int(row[0].strip())
                    initial_transaction = row[1].strip().strip('"()').split(', ')
                    transactions = [[initial_transaction[0], initial_transaction[1], int(initial_transaction[2])]]
                    active_servers = row[2].strip().strip('"[]').split(', ')
                    byzantine_servers = row[3].strip().strip('"[]').split(', ')
                    cur_set = [set_id, transactions, active_servers, byzantine_servers]
                else:
                    transaction = row[1].strip().strip('"()').split(', ')
                    cur_set[1].append([transaction[0], transaction[1], int(transaction[2])])
            if cur_set:
                self.sets.append(cur_set)

    def initialize_clients(self):
        for i in range(1, 11):
            client = Client(client_id=i, servers_keys=self.servers_keys)
            self.clients.append(client)

    def sender_to_client_index(self, sender):
        return ord(sender.upper()) - ord('A')

    def set_active_status(self, server_address, is_active):
        with grpc.insecure_channel(server_address) as channel:
            stub = pbft_pb2_grpc.PBFTServiceStub(channel)
            response = stub.SetActiveStatus(pbft_pb2.SetActiveStatusRequest(is_active=is_active))
            if PRINT_STATEMENTS:
                print(f"Set active status response from {server_address}: {response.success}")

    def set_byzantine_status(self, server_address, is_byzantine):
        with grpc.insecure_channel(server_address) as channel:
            stub = pbft_pb2_grpc.PBFTServiceStub(channel)
            response = stub.SetByzantineStatus(pbft_pb2.SetByzantineStatusRequest(is_byzantine=is_byzantine))
            if PRINT_STATEMENTS:
                print(f"Set Byzantine status response from {server_address}: {response.success}")

    def update_server_status(self, active_servers, byzantine_servers):
        for server, port in self.sender_to_port.items():
            server_address = f'localhost:{port}'
            is_active = server in active_servers
            is_byzantine = server in byzantine_servers
            self.set_active_status(server_address, is_active)
            self.set_byzantine_status(server_address, is_byzantine)

    def HandleReply(self, request, context):
        print(f"Received reply from server {request.replica_id} for client {request.client_id}, view {request.view}, sequence number {request.sequence_number}, result {request.result}")
        client_id = request.client_id
        view = request.view
        sequence_number = request.sequence_number
        replica_id = request.replica_id
        result = request.result
        signature = request.signature
        status = request.status

        transaction_key = (client_id, sequence_number, view, status)

        if client_id not in self.log:
            self.log[client_id] = []

        self.log[client_id].append(request)

        if transaction_key in self.executed_transactions:
            return controller_pb2.ReplyResponse(success=True, message="Reply received")
        
        # Check if we have received f+1 matching responses
        valid_responses = [response for response in self.log[client_id] if response.view == view and response.sequence_number == sequence_number and response.result == result and response.status == status]
        if len(valid_responses) >= self.f + 1:
            print(f"Transaction {sequence_number} for client {client_id} has been committed with f+1 responses")
            # Start a new transaction for the client
            # self.start_new_transaction(client_id)
            self.executed_transactions.add(transaction_key)
            if status:
                print(f"Transaction {sequence_number} for client {client_id} was successful")
            else:
                print(f"Transaction {sequence_number} for client {client_id} failed due to insufficient funds")

        return controller_pb2.ReplyResponse(success=True, message="Reply received")
    
    def print_log(self, server_address):
        with grpc.insecure_channel(server_address) as channel:
            stub = pbft_pb2_grpc.PBFTServiceStub(channel)
            response = stub.PrintLog(pbft_pb2.PrintLogRequest())
            print(f"Log is printed for {server_address}: {response.response}")
    
    def print_db(self, server_address):
        with grpc.insecure_channel(server_address) as channel:
            stub = pbft_pb2_grpc.PBFTServiceStub(channel)
            response = stub.PrintDB(pbft_pb2.PrintDBRequest())
            print(f"DB is printed for {server_address}: {response.response}")

    def print_status(self, server_address, sequence_number):
        with grpc.insecure_channel(server_address) as channel:
            stub = pbft_pb2_grpc.PBFTServiceStub(channel)
            response = stub.PrintStatus(pbft_pb2.PrintStatusRequest(sequence_number=sequence_number))
            print(f"Status is printed for {server_address}: {response.response}")

    def reset_server(self, server_address):
        with grpc.insecure_channel(server_address) as channel:
            stub = pbft_pb2_grpc.PBFTServiceStub(channel)
            response = stub.Reset(pbft_pb2.ResetRequest())
            if PRINT_STATEMENTS:
                print(f"Reset response from {server_address}: {response.success}")

    def reset_all_servers(self):
        for server_name, port in self.sender_to_port.items():
            self.reset_server(f'localhost:{port}')

    def run(self):
        for set in self.sets:
            set_id, transactions, active_servers, byzantine_servers = set
            print(f"Active servers: {active_servers}")
            print(f"Byzantine servers: {byzantine_servers}")
            print(f"Processing set {set_id}")

            # Reset all servers to a fresh state
            self.reset_all_servers()
            print("All servers have been reset to a fresh state.")

            # Update the server status
            self.update_server_status(active_servers, byzantine_servers)
            print("Server status updated!")
            input("Press Enter to execute the set of instructions...")

            # Process transactions sequentially
            for transaction in transactions:
                sender, receiver, amount = transaction
                client_index = self.sender_to_client_index(sender)
                if 0 <= client_index < len(self.clients):
                    try:
                        self.clients[client_index].run_transaction(sender, receiver, amount)
                    except Exception as e:
                        print(f"Transaction failed: {e}")
            while True:
                print("\nOptions:")
                print("1. Print log")
                print("2. Print DB")
                print("3. Print Status")
                print("4. Print View")
                print("5. Execute next set")
                choice = input("Enter choice: ")
                if choice == '1':
                    print("Logs are printed in respective servers")
                    for server_name, port in self.sender_to_port.items():
                        self.print_log(f'localhost:{port}')
                elif choice == '2':
                    print("DB is printed in respective servers")
                    for server_name, port in self.sender_to_port.items():
                        self.print_db(f'localhost:{port}')
                elif choice == '3':
                    sequence_number = int(input("Enter sequence number: "))
                    print("Status is printed in respective servers")
                    for server_name, port in self.sender_to_port.items():
                        self.print_status(f'localhost:{port}', sequence_number)
                elif choice == '4':
                    print("View is printed in respective servers")
                    for server_name, port in self.sender_to_port.items():
                        # print_view(f'localhost:{port}')
                        pass
                elif choice == '5':
                    break
                else:
                    print("Invalid choice. Please try again.")

            input("Press Enter to execute the next set of instructions...")

    # def run(self):
    #     for set in self.sets:
    #         set_id, transactions, active_servers, byzantine_servers = set
    #         print(f"Active servers: {active_servers}")
    #         print(f"Byzantine servers: {byzantine_servers}")
    #         print(f"Processing set {set_id}")

    #         # Update the server status
    #         self.update_server_status(active_servers, byzantine_servers)
    #         print("Server status updated!")
    #         input("Press Enter to execute the set of instructions...")

    #         # Create a dictionary to hold transactions for each client
    #         client_transactions = {i: [] for i in range(10)}

    #         # Assign transactions to the appropriate client based on the sender
    #         for transaction in transactions:
    #             sender, receiver, amount = transaction
    #             client_index = self.sender_to_client_index(sender)
    #             if 0 <= client_index < 10:
    #                 client_transactions[client_index].append(transaction)

    #         # Create and start client threads
    #         client_threads = []
    #         for i in range(10):
    #             if client_transactions[i]:
    #                 client_thread = ClientThread(self.clients[i], client_transactions[i])
    #                 client_threads.append(client_thread)
    #                 client_thread.start()

    #         # Wait for all client threads to complete
    #         for client_thread in client_threads:
    #             client_thread.join()

    #         input("Press Enter to execute the next set of instructions...")

class ClientThread(threading.Thread):
    def __init__(self, client, transactions):
        threading.Thread.__init__(self)
        self.client = client
        self.transactions = transactions

    def run(self):
        for transaction in self.transactions:
            sender, receiver, amount = transaction
            try:
                self.client.run_transaction(sender, receiver, amount)
                # time.sleep(1)
            except Exception as e:
                print(f"Transaction failed: {e}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    controller_service = ControllerService('config.json', 'keys.json', 'test(Lab2 - PBFT).csv')
    controller_pb2_grpc.add_ControllerServiceServicer_to_server(controller_service, server)
    server.add_insecure_port('[::]:50071')
    server.start()
    controller_service.run()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
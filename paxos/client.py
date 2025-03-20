import grpc
import paxos_pb2
import paxos_pb2_grpc
import csv
import json
import threading

PRINT_STATEMENTS = False

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config

def construct_sender_to_port_mapping(config):
    return {server['name']: server['port'] for server in config['servers']}

def set_active_status(server_address, is_active):
    with grpc.insecure_channel(server_address) as channel:
        stub = paxos_pb2_grpc.PaxosStub(channel)
        response = stub.SetActiveStatus(paxos_pb2.SetActiveStatusRequest(is_active=is_active))
        if PRINT_STATEMENTS:
            print(f"Set active status response from {server_address}: {response.success}")

def update_active_servers(active_servers, sender_to_port):
    for server, port in sender_to_port.items():
        is_active = server in active_servers
        set_active_status(f'localhost:{port}', is_active)

def run_client(port, sender, receiver, amount):
    def send_transaction():
        with grpc.insecure_channel(f'localhost:{port}') as channel:
            stub = paxos_pb2_grpc.PaxosStub(channel)
            response = stub.HandleTransaction(paxos_pb2.Transaction(sender=sender, receiver=receiver, amount=amount))
            if PRINT_STATEMENTS:
                print(f"Client received: {'Success' if response.status else 'Failure'}")
    
    thread = threading.Thread(target=send_transaction)
    thread.start()

def parse_input_data(csv_file):
    sets = []
    cur_set = None
    with open(csv_file, mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if row[0]:
                if cur_set:
                    sets.append(cur_set)
                set_id = int(row[0].strip())
                initial_transaction = row[1].strip().strip('"()').split(', ')
                # print(initial_transaction)
                transactions = [[initial_transaction[0], initial_transaction[1], int(initial_transaction[2])]]
                active_servers = row[2].strip().strip('"[]').split(', ')
                cur_set = [set_id, transactions, active_servers]
            else:
                transaction = row[1].strip().strip('"()').split(', ')
                cur_set[1].append([transaction[0], transaction[1], int(transaction[2])])
            # print(cur_set)
        if cur_set:
            sets.append(cur_set)
        print("sets")
        # print(sets)
    return sets

def print_balance(server_address):
    with grpc.insecure_channel(server_address) as channel:
        stub = paxos_pb2_grpc.PaxosStub(channel)
        response = stub.PrintBalance(paxos_pb2.PrintBalanceRequest())
        if PRINT_STATEMENTS:
            print(f"Balance is printed for server {server_address}: {response.response}")

def print_log(server_address):
    with grpc.insecure_channel(server_address) as channel:
        stub = paxos_pb2_grpc.PaxosStub(channel)
        response = stub.PrintLog(paxos_pb2.PrintLogRequest())
        if PRINT_STATEMENTS:
            print(f"Log is printed for server {server_address}: {response.response}")

def print_db(server_address):
    with grpc.insecure_channel(server_address) as channel:
        stub = paxos_pb2_grpc.PaxosStub(channel)
        response = stub.PrintDB(paxos_pb2.PrintDBRequest())
        if PRINT_STATEMENTS:
            print(f"Datastore balance is printed for server {server_address}: {response.response}")
           
def get_current_balance(server_address):
    with grpc.insecure_channel(server_address) as channel:
        stub = paxos_pb2_grpc.PaxosStub(channel)
        response = stub.GetCurrentBalance(paxos_pb2.GetCurrentBalanceRequest())
        return response

def aggregate_balances_and_logs(sender_to_port):
    server_balances = {}
    aggregated_logs = []
    for server_name, port in sender_to_port.items():
        response = get_current_balance(f'localhost:{port}')
        server_balances[server_name] = response.balance
        aggregated_logs.extend(response.local_logs)
    
    # Update balances based on local transactions
    for log in aggregated_logs:
        if log.receiver in server_balances:
            server_balances[log.receiver] += log.amount

    return server_balances, aggregated_logs

def print_current_balances_and_logs(sender_to_port):
    server_balances, _ = aggregate_balances_and_logs(sender_to_port)
    print("Server Balances:")
    for server, balance in server_balances.items():
        print(f"{server}: {balance}")

def performance(server_address):
    with grpc.insecure_channel(server_address) as channel:
        stub = paxos_pb2_grpc.PaxosStub(channel)
        response = stub.Performance(paxos_pb2.PerformanceRequest())
        print(f"Performance Metrices for server {server_address}:")
        print(f"    Transaction Throughput: {round(response.transaction_throughput, 6)} transactions/second")
        print(f"    Average Transaction Latency: {round(response.average_transaction_latency, 6)} seconds")
        # print(f"    Leader Election Count: {response.leader_election_count}")
        print(f"    Average Leader Election Time: {round(response.average_leader_election_time, 6)} seconds")
        # print(f"    RPC Call Count: {response.rpc_call_count}")
        print(f"    Average RPC Time: {round(response.average_rpc_time, 6)} seconds")
        print()

if __name__ == '__main__':
    config = load_config('config.json')
    sender_to_port = construct_sender_to_port_mapping(config)
    
    print("Parsing input data!")
    sets = parse_input_data('LAB1_TEST.CSV')
    
    for set_id, transactions, active_servers in sets:
        print(f"Executing set {set_id}")
        
        # Update active servers
        update_active_servers(active_servers, sender_to_port)
        # time.sleep(1)
        # Execute transactions

        for transaction in transactions:
            sender, receiver, amount = transaction
            port = sender_to_port.get(sender)
            if port:
                run_client(port, sender, receiver, amount)
        
        while True:
            print("\nOptions:")
            print("1. Print Balance")
            print("2. Print Log")
            print("3. Print DB")
            print("4. Performance and Latency")
            print("5. Aggregated Balance of all servers")
            print("6. Continue to next set")
            choice = input("Enter your choice: ")

            if choice == '1':
                print("Balance is printed on respective servers.")
                for server_name, port in sender_to_port.items():
                    print_balance(f'localhost:{port}')
            elif choice == '2':
                print("Local log is printed on respective servers.")
                for server_name, port in sender_to_port.items():
                    print_log(f'localhost:{port}')
            elif choice == '3':
                print("Datastore is printed on respective servers.")
                for server_name, port in sender_to_port.items():
                    print_db(f'localhost:{port}')
            elif choice == '4':
                for server_name, port in sender_to_port.items():
                    performance(f'localhost:{port}')
            elif choice == '5':
                print_current_balances_and_logs(sender_to_port)
            elif choice == '6':
                break
            else:
                print("Invalid choice. Please try again.")

        input("Press Enter to execute the next set of transactions...")
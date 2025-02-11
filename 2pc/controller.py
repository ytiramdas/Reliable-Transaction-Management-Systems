import grpc
from concurrent import futures
import json
import time
import csv
import paxos_pb2
import paxos_pb2_grpc
import asyncio
import subprocess

PRINT_STATEMENTS = False

def create_config_file(num_clusters, cluster_size, total_clients):
    config = {
        "servers": [],
        "clusters": []
    }

    port = 50051
    server_id = 1

    for cluster_id in range(1, num_clusters + 1):
        for _ in range(cluster_size):
            server = {
                "name": f"S{server_id}",
                "id": server_id,
                "cluster_id": cluster_id,
                "port": port
            }
            config["servers"].append(server)
            port += 1
            server_id += 1

    # Divide clients equally among clusters and assign ranges
    clients_per_cluster = total_clients // num_clusters
    client_start_id = 1

    for cluster_id in range(1, num_clusters + 1):
        client_end_id = client_start_id + clients_per_cluster - 1
        cluster = {
            "cluster_id": cluster_id,
            "client_range": [client_start_id, client_end_id]
        }
        config["clusters"].append(cluster)
        client_start_id = client_end_id + 1

    with open("config.json", "w") as file:
        json.dump(config, file, indent=4)

def create_start_servers_script(config):
    script_lines = [
        "#!/bin/bash",
        "",
        "# Loop through the server IDs and open a new terminal for each"
    ]

    for server in config["servers"]:
        server_id = server["id"]
        script_lines.append(
            f'osascript -e "tell application \\"Terminal\\" to do script \\"cd $(pwd); source myenv/bin/activate; python3 $(pwd)/server.py {server_id}\\""'
        )

    script_content = "\n".join(script_lines)

    with open("start_servers.sh", "w") as file:
        file.write(script_content)

    # Make the script executable
    import os
    os.chmod("start_servers.sh", 0o755)

def start_servers():
    subprocess.run(["./start_servers.sh"])

def parse_input_data(data_file):
    sets = []
    cur_set = None
    with open(data_file, mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if row[0]:
                if cur_set:
                    sets.append(cur_set)
                set_id = int(row[0].strip())
                initial_transaction = row[1].strip().strip('"()').split(', ')
                transactions = [[initial_transaction[0], initial_transaction[1], int(initial_transaction[2])]]
                active_servers = row[2].strip().strip('"[]').split(', ')
                contact_servers = row[3].strip().strip('"[]').split(', ')
                cur_set = [set_id, transactions, active_servers, contact_servers]
            else:
                transaction = row[1].strip().strip('"()').split(', ')
                cur_set[1].append([transaction[0], transaction[1], int(transaction[2])])
        if cur_set:
            sets.append(cur_set)
    return sets

def get_cluster_id(client_id, config):
    for cluster in config['clusters']:
        if cluster['client_range'][0] <= client_id <= cluster['client_range'][1]:
            return cluster['cluster_id']
    return None

def set_active_status(server_address, is_active):
    if PRINT_STATEMENTS:
        print(f"Setting active status for {server_address} to {is_active}")
    with grpc.insecure_channel(server_address) as channel:
            stub = paxos_pb2_grpc.TransactionServiceStub(channel)
            response = stub.SetActiveStatus(paxos_pb2.SetActiveStatusRequest(is_active=is_active))
            if PRINT_STATEMENTS:
                print(f"Set active status response from {server_address}: {response.success}")

def set_contact_status(server_address, is_contact):
    if PRINT_STATEMENTS:
        print(f"Setting contact status for {server_address} to {is_contact}")
    with grpc.insecure_channel(server_address) as channel:
            stub = paxos_pb2_grpc.TransactionServiceStub(channel)
            response = stub.SetContactStatus(paxos_pb2.SetContactStatusRequest(is_contact=is_contact))
            if PRINT_STATEMENTS:
                print(f"Set Contact status response from {server_address}: {response.success}")

def update_server_status(active_servers, contact_servers, sender_to_port):
    print("Updating server status...")
    print(f"Active servers: {active_servers}")
    print(f"Contact servers: {contact_servers}")
    for server_name, port in sender_to_port.items():
        server_address = f'localhost:{port}'
        is_active = server_name in active_servers
        is_contact = server_name in contact_servers
        set_active_status(server_address, is_active)
        set_contact_status(server_address, is_contact)

def intra_shard_transaction(sender, receiver, amount, contact_server_address):
    print(f"Intra-shard transaction: {sender} -> {receiver} : {amount}")
    timestamp = int(time.time() * 1000)
    with grpc.insecure_channel(contact_server_address) as channel:
        stub = paxos_pb2_grpc.TransactionServiceStub(channel)
        request = paxos_pb2.TransactionRequest(sender=sender, receiver=receiver, amount=amount, timestamp=timestamp, type="intra")
        response = stub.ProcessTransaction(request)
        print(f"Transaction response: {response.message}")

async def cross_shard_transaction(sender, receiver, amount, config, sender_contact_server_address, receiver_contact_server_address):
    print(f"Cross-shard transaction: {sender} -> {receiver} : {amount}")
    
    # Prepare Phase
    async with grpc.aio.insecure_channel(sender_contact_server_address) as sender_channel, grpc.aio.insecure_channel(receiver_contact_server_address) as receiver_channel:
        sender_stub = paxos_pb2_grpc.TransactionServiceStub(sender_channel)
        receiver_stub = paxos_pb2_grpc.TransactionServiceStub(receiver_channel)

        timestamp = int(time.time() * 1000)
        sender_request = paxos_pb2.CrossShardPrepareRequest(sender=sender, receiver=receiver, amount=amount, timestamp=timestamp, type="cross", sender_or_receiver="sender")
        receiver_request = paxos_pb2.CrossShardPrepareRequest(sender=sender, receiver=receiver, amount=amount, timestamp=timestamp, type="cross", sender_or_receiver="receiver")

        sender_response_future = sender_stub.CrossShardPrepare(sender_request)
        receiver_response_future = receiver_stub.CrossShardPrepare(receiver_request)

        sender_response, receiver_response = await asyncio.gather(sender_response_future, receiver_response_future)

        if PRINT_STATEMENTS:
            print(f"Sender response: {sender_response}")
            print(f"Receiver response: {receiver_response}")
        
        if PRINT_STATEMENTS:
            print(f"Sender Prepare Response: {sender_response.message}")
            print(f"Receiver Prepare Response: {receiver_response.message}")

        commit = None
        if sender_response.success and receiver_response.success:
            if PRINT_STATEMENTS:
                print("Prepare phase successful for both clusters.")
                print("Sending commit requests...")
            print(f"Prepare succeeded for both sender and receiver for transaction: {sender} -> {receiver} : {amount}")
            commit = True
        else:
            if PRINT_STATEMENTS:
                print("Prepare phase failed for one or both clusters. Aborting transaction.")
                print("Sending abort requests...")
                
            print()
            if not sender_response.success and not receiver_response.success:
                print(f"Prepare failed for both sender and receiver for transaction: {sender} -> {receiver} : {amount}")
                print(f"Sender prepare failed due to {sender_response.message}")
                print(f"Receiver prepare failed due to {receiver_response.message}")
            elif not sender_response.success:
                print(f"Sender prepare failed due to {sender_response.message} for transaction: {sender} -> {receiver} : {amount}")
            elif not receiver_response.success:
                print(f"Receiver prepare failed due to {receiver_response.message} for transaction: {sender} -> {receiver} : {amount}")
            commit = False
        commit_request_sender = paxos_pb2.CrossShardCommitRequest(
            ballot_number=sender_response.ballot_number,
            server_id=sender_response.server_id,
            sender=sender,
            receiver=receiver,
            amount=amount,
            timestamp=timestamp,
            type="cross",
            sender_or_receiver="sender",
            commit = commit
        )
        commit_request_receiver = paxos_pb2.CrossShardCommitRequest(
            ballot_number=receiver_response.ballot_number,
            server_id=receiver_response.server_id,
            sender=sender,
            receiver=receiver,
            amount=amount,
            timestamp=timestamp,
            type="cross",
            sender_or_receiver="receiver",
            commit = commit
        )
        await asyncio.gather(
            *[send_commit_to_server(server, commit_request_sender, sender_response, sender_contact_server_address) for server in config["servers"] if server["cluster_id"] == get_cluster_id(int(sender), config)],
            *[send_commit_to_server(server, commit_request_receiver, receiver_response, receiver_contact_server_address) for server in config["servers"] if server["cluster_id"] == get_cluster_id(int(receiver), config)]
        )

async def send_commit_to_server(server, commit_request, response, server_address):
    async with grpc.aio.insecure_channel(f'localhost:{server["port"]}') as channel:
        stub = paxos_pb2_grpc.TransactionServiceStub(channel)
        commit_response = await stub.CrossShardCommit(commit_request)
        if PRINT_STATEMENTS:
            print(f"Commit response from server {server['name']} (ID: {server['id']}): {commit_response}")       

def print_balance(client_id, config, sender_to_port):
    cluster_id = get_cluster_id(client_id, config)
    if cluster_id is None:
        print(f"Client ID {client_id} not found in any cluster.")
        return

    print(f"Printing balance for client ID {client_id} in cluster {cluster_id}")
    for server in config["servers"]:
        if server["cluster_id"] == cluster_id:
            server_address = f'localhost:{server["port"]}'
            with grpc.insecure_channel(server_address) as channel:
                stub = paxos_pb2_grpc.TransactionServiceStub(channel)
                response = stub.GetBalance(paxos_pb2.BalanceRequest(client_id=client_id))
                print(f"Balance on server {server['name']} (ID: {server['id']}): {response.balance}")

def print_datastore(config, sender_to_port):
    print("Printing datastore for all servers:")
    for server in config["servers"]:
        server_address = f'localhost:{server["port"]}'
        with grpc.insecure_channel(server_address) as channel:
            stub = paxos_pb2_grpc.TransactionServiceStub(channel)
            response = stub.GetDatastore(paxos_pb2.DatastoreRequest())
            print(f"\nDatastore on server {server['name']} (ID: {server['id']}):")
            for item in response.transactions:
                if item.transaction.type == "intra":
                    print(f"  <{item.ballot_number}, {item.server_id}>, [{item.transaction.sender} -> {item.transaction.receiver} : {item.transaction.amount}] - {item.message} ({item.transaction.type})")
                else:
                    c = None
                    if item.message == "prepare-prepared" or item.message == "prepare-aborted":
                        c = "P"
                    elif item.message == "commit-committed":
                        c = "C"
                    elif item.message == "commit-aborted":
                        c = "A"
                    print(f"  <{item.ballot_number}, {item.server_id}>, {c}, [{item.transaction.sender} -> {item.transaction.receiver} : {item.transaction.amount}] - {item.message} ({item.transaction.type})")

def calculate_performance(start_times, end_times):
    total_transactions = len(start_times)
    total_time = sum(end_times[i] - start_times[i] for i in range(total_transactions))
    throughput = total_transactions / total_time if total_time > 0 else 0
    latency = total_time / total_transactions if total_transactions > 0 else 0
    print(f"Throughput: {throughput:.3f} transactions per second")
    print(f"Average Latency: {latency:.3f} seconds per transaction")

async def run(sets, config, sender_to_port):
    start_times = []
    end_times = []
    for set in sets:
        set_id, transactions, active_servers, contact_servers = set
        print(f"Running set {set_id}")

        input("Press Enter to execute the set of instructions...")

        update_server_status(active_servers, contact_servers, sender_to_port)

        print("Server status updated!")
        
        # Process transactions sequentially
        tasks = []
        for transaction in transactions:
            sender, receiver, amount = transaction
            sender_id = int(sender)
            receiver_id = int(receiver)
            sender_cluster = get_cluster_id(sender_id, config)
            receiver_cluster = get_cluster_id(receiver_id, config)

            start_time = time.time()
            start_times.append(start_time)

            if sender_cluster == receiver_cluster:
                contact_server = contact_servers[sender_cluster-1]
                contact_server_address = f'localhost:{sender_to_port[contact_server]}'
                intra_shard_transaction(sender, receiver, amount, contact_server_address)
            else:
                sender_contact_server = contact_servers[sender_cluster-1]
                receiver_contact_server = contact_servers[receiver_cluster-1]
                if PRINT_STATEMENTS:
                    print(f"Sender contact server: {sender_contact_server}")
                    print(f"Receiver contact server: {receiver_contact_server}")
                sender_contact_server_address = f'localhost:{sender_to_port[sender_contact_server]}'
                receiver_contact_server_address = f'localhost:{sender_to_port[receiver_contact_server]}'
                await asyncio.sleep(0.01)  # Add a delay of 10ms
                tasks.append(asyncio.create_task(cross_shard_transaction(sender, receiver, amount, config, sender_contact_server_address, receiver_contact_server_address)))

            end_time = time.time()
            end_times.append(end_time)

        # Wait for all cross-shard transactions to complete
        await asyncio.gather(*tasks)

        while True:
            print("\nOptions:")
            print("1. Print Balance")
            print("2. Print Datastore")
            print("3. Print Performance")
            print("4. Execute next set")
            choice = input("Enter choice: ")
            if choice == '1':
                while True:
                    client_id = input("Enter client ID (or type 'exit' to go back): ")
                    if client_id.lower() == 'exit':
                        break
                    try:
                        client_id = int(client_id)
                        print_balance(client_id, config, sender_to_port)
                    except ValueError:
                        print("Invalid client ID. Please enter a valid integer.")
            elif choice == '2':
                print_datastore(config, sender_to_port)
            elif choice == '3':
                calculate_performance(start_times, end_times)
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please try again.")

        input("Press Enter to execute the next set of instructions...")

if __name__ == '__main__':
    num_clusters = int(input("Enter the number of clusters: "))
    cluster_size = int(input("Enter the cluster size: "))
    total_clients = 3000  # Total number of clients

    create_config_file(num_clusters, cluster_size, total_clients)
    
    with open("config.json", "r") as file:
        config = json.load(file)
    
    create_start_servers_script(config)

    start_servers()

    sender_to_port = {server['name']: server['port'] for server in config['servers']}
    
    print("Config file and start_servers.sh script created successfully.")

    data_file = 'Test_Cases_-_Lab3.csv'
    sets = parse_input_data(data_file)
    if PRINT_STATEMENTS:
        print(sets)

    asyncio.run(run(sets, config, sender_to_port))


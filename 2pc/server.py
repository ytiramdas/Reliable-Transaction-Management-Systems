import grpc
from concurrent import futures
import time
import json
import sys

import paxos_pb2
import paxos_pb2_grpc

import db_manager as db
import time

PRINT_STATEMENTS = False

class TransactionService(paxos_pb2_grpc.TransactionServiceServicer):
    def __init__(self, server_id, cluster_id, other_servers_by_cluster, client_range, num_servers_in_cluster):
        self.server_id = server_id
        self.cluster_id = cluster_id
        self.other_servers_by_cluster = other_servers_by_cluster
        self.client_range = client_range
        self.num_of_servers_in_cluster = num_servers_in_cluster
        self.f = (self.num_of_servers_in_cluster - 1) // 2
        self.db_file = f"db_{server_id}.db"
        self.db_manager = db.DatabaseManager(self.db_file)
        self.db_manager.initialize(client_range)
        self.is_active = False
        self.is_contact = False
        self.ballot_number = 0
        self.num_of_committed_transactions = 0

    def ProcessTransaction(self, request, context):
        print(f"Received transaction: {request.sender} -> {request.receiver} : {request.amount} at {request.timestamp}, type: {request.type}")
        if request.type == "intra":
            print("Intra-shard transaction, initiating consensus")
            success, message = self.initiate_consensus(request)
        return paxos_pb2.TransactionResponse(success=success, message=message)
    
    def SetActiveStatus(self, request, context):
        self.is_active = request.is_active
        message = f"Server {self.server_id} active status set to {self.is_active}"
        print(message)
        return paxos_pb2.SetActiveStatusResponse(message=message, success=True)

    def SetContactStatus(self, request, context):
        self.is_contact = request.is_contact
        message = f"Server {self.server_id} contact status set to {self.is_contact}"
        print(message)
        return paxos_pb2.SetContactStatusResponse(message=message, success=True)
    
    def GetBalance(self, request, context):
        client_id = request.client_id
        balance = self.db_manager.get_balance(client_id)
        print(f"Balance of client {client_id}: {balance}")
        return paxos_pb2.BalanceResponse(client_id=client_id, balance=balance)
    
    def GetDatastore(self, request, context):
        if PRINT_STATEMENTS:
            print(f"Received datastore request")

        transactions = self.db_manager.get_transactions()
        
        print("\nDatastore items:")
        for t in transactions:
            print(f"<{t[0]}, {t[1]}>, {t[2]} -> {t[3]}, {t[4]}, {t[5]}, {t[6]}, {t[7]}")
        print("\n")

        transaction_messages = [
            paxos_pb2.DatastoreItem(
                ballot_number=t[0],
                server_id=t[1],
                transaction=paxos_pb2.TransactionRequest(
                    sender=t[2],
                    receiver=t[3],
                    amount=t[4],
                    timestamp=t[5],
                    type=t[6]
                ),
                message=t[7]
            ) for t in transactions
        ]
        return paxos_pb2.DatastoreResponse(transactions=transaction_messages)

    def initiate_consensus(self, transaction_request):
        print(f"Initiating consensus for transaction: {transaction_request}")
        self.ballot_number += 1
        ballot_number = self.ballot_number
        server_id = self.server_id
        if PRINT_STATEMENTS:
            print(f"Ballot number: {ballot_number}")
            print(f"Server ID: {server_id}")
        transactions = self.db_manager.get_transactions()
        transactions_messages = [
            paxos_pb2.DatastoreItem(
                ballot_number=t[0],
                server_id=t[1],
                transaction=paxos_pb2.TransactionRequest(
                    sender=t[2],
                    receiver=t[3],
                    amount=t[4],
                    timestamp=t[5],
                    type=t[6]
                ),
                message=t[7]
            ) for t in transactions
        ]
        prepare_message = paxos_pb2.PrepareMessage(
            ballot_number=ballot_number,
            server_id=server_id,
            transaction=transaction_request,
            datastore_items=transactions_messages
        )
        if PRINT_STATEMENTS:
            print(f"Prepare message: {prepare_message}")
        promises = []
        for server_address in self.other_servers_by_cluster[self.cluster_id]:
            print(f"Sending prepare message to {server_address}")
            promise = self.send_prepare_message(server_address, prepare_message)
            promises.append(promise)

        # Add the current server's promise message
        current_server_promise = paxos_pb2.PromiseMessage(
            ballot_number=ballot_number,
            server_id=server_id,
            success=True,
            message="Promise sent"
        )
        promises.append(current_server_promise)
        
        valid_promises = [p for p in promises if p.success]

        # Find the promise with the maximum length of datastore_items
        if PRINT_STATEMENTS:
            print("Valid promises:")
            print(valid_promises)
        max_datastore_items = []
        for promise in valid_promises:
            if len(promise.datastore_items) > len(max_datastore_items):
                max_datastore_items = promise.datastore_items

        if PRINT_STATEMENTS:
            print(f"Max Datastore Items that need to be synchronized: {max_datastore_items}")
        # Synchronize the leader with the most up-to-date logs
        if max_datastore_items:
            self.synchronize_state_in_leader(max_datastore_items)
        
        if len(valid_promises) >= self.f + 1:
            print("Received majority of valid promises, proceeding to next stage.")
            conditions_satisfied, message = self.check_conditions(transaction_request)
            if not conditions_satisfied:
                print(f"Conditions not satisfied: {message}")
                self.db_manager.insert_datastore_item(ballot_number, server_id, transaction_request, "aborted")
                self.propagate_abort(transaction_request, ballot_number, server_id)
                return (False, message)

            self.db_manager.insert_datastore_item(ballot_number, server_id, transaction_request, "prepared")
            self.db_manager.lock_client(transaction_request.sender)
            self.db_manager.lock_client(transaction_request.receiver)

            accept_message = paxos_pb2.AcceptMessage(
                ballot_number=ballot_number,
                server_id=server_id,
                transaction=transaction_request
            )

            accepted_responses = []
            for server_address in self.other_servers_by_cluster[self.cluster_id]:
                print(f"Sending accept message to {server_address}")
                accepted_response = self.send_accept_message(server_address, accept_message)
                accepted_responses.append(accepted_response)
            
            # Add the current server's accept response
            current_server_accepted_response = paxos_pb2.AcceptedResponse(
                ballot_number=ballot_number,
                server_id=server_id,
                success=True,
                message="Transaction accepted"
            )
            accepted_responses.append(current_server_accepted_response)

            valid_accepts = [r for r in accepted_responses if r.success]
            if len(valid_accepts) >= self.f + 1:
                print("Received majority of valid accept responses, committing transaction.")
                self.commit_transaction(transaction_request)
                self.db_manager.update_datastore_item_status(ballot_number, server_id, "committed")

                commit_message = paxos_pb2.CommitMessage(
                    ballot_number=ballot_number,
                    server_id=server_id,
                    transaction=transaction_request
                )

                commit_responses = []
                for server_address in self.other_servers_by_cluster[self.cluster_id]:
                    print(f"Sending commit message to {server_address}")
                    commit_response = self.send_commit_message(server_address, commit_message)
                    commit_responses.append(commit_response)

                return (True, "Transaction committed")
            else:
                print("Did not receive majority of valid accept responses, aborting transaction.")
                self.db_manager.update_datastore_item_status(ballot_number, server_id, "aborted")
                self.propagate_abort(transaction_request, ballot_number, server_id)
                return (False, "Consensus not reached")
        else:
            message = "Did not receive majority of valid promises, aborting transaction"
            self.db_manager.insert_datastore_item(ballot_number, server_id, transaction_request, "aborted")
            self.propagate_abort(transaction_request, ballot_number, server_id)
            return (False, message)
                
    def check_conditions(self, transaction_request):
        sender = transaction_request.sender
        receiver = transaction_request.receiver
        amount = transaction_request.amount

        # Check if there are no locks on data items
        if self.db_manager.is_locked(sender) or self.db_manager.is_locked(receiver):
            return False, "Data items are locked"

        # Check if the balance of sender is at least equal to amount
        if self.db_manager.get_balance(sender) < amount:
            return False, "Insufficient balance"

        return True, "Conditions satisfied"
    
    def check_conditions_for_cross_shard(self, transaction_request):
        if PRINT_STATEMENTS:
            print(f"Checking conditions for cross shard transaction: {transaction_request}")
        sender = transaction_request.sender
        receiver = transaction_request.receiver
        amount = transaction_request.amount

        if transaction_request.sender_or_receiver == "sender":
            if self.db_manager.is_locked(sender):
                return False, "Data items are locked"
            if self.db_manager.get_balance(sender) < amount:
                return False, "Insufficient balance"
        elif transaction_request.sender_or_receiver == "receiver":
            if self.db_manager.is_locked(receiver):
                return False, "Data items are locked"

        return True, "Conditions satisfied"
    
    def commit_transaction(self, transaction_request):
        sender = transaction_request.sender
        receiver = transaction_request.receiver
        amount = transaction_request.amount

        # Commit the transaction
        self.db_manager.update_balance(sender, -amount)
        self.db_manager.update_balance(receiver, amount)

        # Unlock the data items
        self.db_manager.unlock_client(sender)
        self.db_manager.unlock_client(receiver)

        if PRINT_STATEMENTS:
            print(f"Transaction committed: {transaction_request}")

    def commit_transaction_cross_shard(self, transaction_request):
        sender = transaction_request.sender
        receiver = transaction_request.receiver
        amount = transaction_request.amount

        time.sleep(0.01)
        if transaction_request.sender_or_receiver == "sender":
            self.db_manager.update_balance(sender, -amount)
            self.db_manager.unlock_client(sender)
        elif transaction_request.sender_or_receiver == "receiver":
            self.db_manager.update_balance(receiver, amount)
            self.db_manager.unlock_client(receiver)

        if PRINT_STATEMENTS:
            print(f"Transaction committed: {transaction_request} on server {self.server_id}")

    def send_prepare_message(self, server_address, prepare_message):
        with grpc.insecure_channel(server_address) as channel:
            stub = paxos_pb2_grpc.TransactionServiceStub(channel)
            response = stub.Prepare(prepare_message)
            if PRINT_STATEMENTS:
                print(f"Received promise from {server_address}: {response}")
            return response

    def send_accept_message(self, server_address, accept_message):
        with grpc.insecure_channel(server_address) as channel:
            stub = paxos_pb2_grpc.TransactionServiceStub(channel)
            response = stub.Accept(accept_message)
            if PRINT_STATEMENTS:
                print(f"Received accept response from {server_address}: {response}")
            return response
        
    def send_commit_message(self, server_address, commit_message):
        with grpc.insecure_channel(server_address) as channel:
            stub = paxos_pb2_grpc.TransactionServiceStub(channel)
            response = stub.Commit(commit_message)
            if PRINT_STATEMENTS:
                print(f"Received commit response from {server_address}: {response}")
            return response
        
    def propagate_abort(self, transaction_request, ballot_number, server_id):
        abort_message = paxos_pb2.AbortMessage(
            ballot_number=ballot_number,
            server_id=server_id,
            transaction=transaction_request
        )
        for server_address in self.other_servers_by_cluster[self.cluster_id]:
            if PRINT_STATEMENTS:
                print(f"Sending abort message to {server_address}")
            self.send_abort_message(server_address, abort_message)

    def send_abort_message(self, server_address, abort_message):
        with grpc.insecure_channel(server_address) as channel:
            stub = paxos_pb2_grpc.TransactionServiceStub(channel)
            response = stub.Abort(abort_message)
            if PRINT_STATEMENTS:
                print(f"Received abort response from {server_address}: {response}")
            return response

    def initiate_consensus_cross_shard(self, request):
        print(f"Initiating consensus for cross shard transaction: {request}")
        self.ballot_number += 1
        ballot_number = self.ballot_number
        server_id = self.server_id
        if PRINT_STATEMENTS:
            print(f"Ballot number: {ballot_number}")
            print(f"Server ID: {server_id}")

        time.sleep(0.05)
        transactions = self.db_manager.get_transactions()
        transactions_messages = [
            paxos_pb2.DatastoreItem(
                ballot_number=t[0],
                server_id=t[1],
                transaction=paxos_pb2.TransactionRequest(
                    sender=t[2],
                    receiver=t[3],
                    amount=t[4],
                    timestamp=t[5],
                    type=t[6]
                ),
                message=t[7]
            ) for t in transactions
        ]

        transaction_request = paxos_pb2.TransactionRequest(
            sender=request.sender,
            receiver=request.receiver,
            amount=request.amount,
            timestamp=request.timestamp,
            type=request.type,
        )

        prepare_message = paxos_pb2.PrepareMessage(
            ballot_number=ballot_number,
            server_id=server_id,
            transaction=transaction_request,
            datastore_items=transactions_messages,
        )
        if PRINT_STATEMENTS:
            print(f"Prepare message: {prepare_message}")
        promises = []
        for server_address in self.other_servers_by_cluster[self.cluster_id]:
            print(f"Sending prepare message to {server_address}")
            promise = self.send_prepare_message(server_address, prepare_message)
            promises.append(promise)

        # Add the current server's promise message
        current_server_promise = paxos_pb2.PromiseMessage(
            ballot_number=ballot_number,
            server_id=server_id,
            success=True,
            message="Promise sent"
        )
        promises.append(current_server_promise)
        
        valid_promises = [p for p in promises if p.success]

        # Find the promise with the maximum length of datastore_items
        if PRINT_STATEMENTS:
            print("Valid promises:")
            print(valid_promises)
        max_datastore_items = []
        for promise in valid_promises:
            if len(promise.datastore_items) > len(max_datastore_items):
                max_datastore_items = promise.datastore_items

        if PRINT_STATEMENTS:
            print(f"Max Datastore Items that need to be synchronized: {max_datastore_items}")
        # Synchronize the leader with the most up-to-date logs
        if max_datastore_items:
            self.synchronize_state_in_leader(max_datastore_items)
        
        if len(valid_promises) >= self.f + 1:
            print("Received majority of valid promises, proceeding to next stage.")
            conditions_satisfied, message = self.check_conditions_for_cross_shard(request)
            if not conditions_satisfied:
                print(f"Conditions not satisfied: {message}")
                self.db_manager.insert_datastore_item(ballot_number, server_id, transaction_request, "prepare-aborted")
                self.propagate_abort(transaction_request, ballot_number, server_id)
                return (False, message, ballot_number, server_id)

            self.db_manager.insert_datastore_item(ballot_number, server_id, request, "prepare-prepared")
            if request.sender_or_receiver == "sender":
                self.db_manager.lock_client(request.sender)
            elif request.sender_or_receiver == "receiver":
                self.db_manager.lock_client(request.receiver)
            
            accept_message = paxos_pb2.AcceptMessage(
                ballot_number=ballot_number,
                server_id=server_id,
                transaction=transaction_request
            )

            accepted_responses = []
            for server_address in self.other_servers_by_cluster[self.cluster_id]:
                print(f"Sending accept message to {server_address}")
                accepted_response = self.send_accept_message(server_address, accept_message)
                accepted_responses.append(accepted_response)

            return (True, "Transaction prepared", ballot_number, server_id)
        else:
            return (False, "Did not receive majority of valid promises, aborting transaction", ballot_number, server_id)

    def CrossShardPrepare(self, request, context):
        if not self.is_active:
            if PRINT_STATEMENTS:
                print(f"Server {self.server_id} is not active. Ignoring cross shard prepare message.")
            return paxos_pb2.CrossShardPrepareResponse(
                message = "Server is not active",
                success = False
            )
        
        if PRINT_STATEMENTS:
            print(f"Received cross shard prepare message: {request}")

        # Add a 10ms delay
        time.sleep(0.01)
        success, message, ballot_number, server_id = self.initiate_consensus_cross_shard(request)
        return paxos_pb2.CrossShardPrepareResponse(
            message=message,
            success=success,
            ballot_number=ballot_number,
            server_id=server_id
        )

    def CrossShardCommit(self, request, context):
        if not self.is_active:
            if PRINT_STATEMENTS:
                print(f"Server {self.server_id} is not active. Ignoring cross shard commit message.")
            return paxos_pb2.CrossShardCommitResponse(
                success=False,
                message="Server is not active"
            )
        if PRINT_STATEMENTS:
            print(f"Received cross shard commit message: {request}")
        
        transaction = paxos_pb2.TransactionRequest(
            sender=request.sender,
            receiver=request.receiver,
            amount=request.amount,
            timestamp=request.timestamp,
            type=request.type
        )

        if request.commit:
            self.commit_transaction_cross_shard(request)
            self.db_manager.insert_datastore_item(request.ballot_number, request.server_id, transaction, "commit-committed")
        else:
            if request.sender_or_receiver == "sender":
                self.db_manager.unlock_client(request.sender)
            elif request.sender_or_receiver == "receiver":
                self.db_manager.unlock_client(request.receiver)
            self.db_manager.insert_datastore_item(request.ballot_number, request.server_id, transaction, "commit-aborted")
            print(f"Transaction aborted: {transaction}")
        return paxos_pb2.CrossShardCommitResponse(
            success=True,
            message="Transaction committed"
        )

        
    def Prepare(self, request, context):
        # Not responding anything here
        if not self.is_active:
            if PRINT_STATEMENTS:
                print(f"Server {self.server_id} is not active. Ignoring prepare message.")
            return paxos_pb2.PromiseMessage(
                message = "Server is not active",
                success = False
            )
        if PRINT_STATEMENTS:
            print(f"Received prepare message: {request}")

        different_records = self.compare_datastore(request.datastore_items)
        items = []

        if different_records is not None:
            for record in different_records:
                item = paxos_pb2.DatastoreItem(
                    ballot_number=record[0],
                    server_id=record[1],
                    transaction=paxos_pb2.TransactionRequest(
                        sender=record[2],
                        receiver=record[3],
                        amount=record[4],
                        timestamp=record[5],
                        type=record[6]
                    ),
                    message=record[7]
                )
                items.append(item)

        ballot_number = request.ballot_number
        server_id = request.server_id
        self.ballot_number = request.ballot_number
        promise_message = paxos_pb2.PromiseMessage(
            ballot_number=ballot_number,
            server_id=server_id,
            success=True,
            message = "Promise sent",
            datastore_items=items if different_records else None
        )
        print(f"Sending promise to server {request.server_id} with ballot number {self.ballot_number}")
        return promise_message
        
    def Accept(self, request, context):
        if not self.is_active:
            if PRINT_STATEMENTS:
                print(f"Server {self.server_id} is not active. Ignoring accept message.")
            return paxos_pb2.AcceptedResponse(
                ballot_number=request.ballot_number,
                server_id=self.server_id,
                success=False,
                message="Server is not active"
            )
        if PRINT_STATEMENTS:
            print(f"Received accept message: {request}")
        
        sender = request.transaction.sender
        receiver = request.transaction.receiver

        if request.transaction.type == "intra":
            self.db_manager.lock_client(sender)
            self.db_manager.lock_client(receiver)
            self.db_manager.insert_datastore_item(request.ballot_number, request.server_id, request.transaction, "prepared")
        elif request.transaction.type == "cross":
            if request.transaction.sender_or_receiver == "sender":
                self.db_manager.lock_client(sender)
            elif request.transaction.sender_or_receiver == "receiver":
                self.db_manager.lock_client(receiver)
            self.db_manager.insert_datastore_item(request.ballot_number, request.server_id, request.transaction, "prepare-prepared")

        if PRINT_STATEMENTS:
            print(f"Accepted transaction: {request.transaction}")
        return paxos_pb2.AcceptedResponse(
            ballot_number=self.ballot_number,
            server_id=self.server_id,
            success=True,
            message="Transaction accepted"
        )
    
    def Commit(self, request, context):
        if not self.is_active:
            if PRINT_STATEMENTS:
                print(f"Server {self.server_id} is not active. Ignoring commit message.")
            return paxos_pb2.CommitResponse(
                success=False,
                message="Server is not active"
            )
        if PRINT_STATEMENTS:
            print(f"Received commit message: {request}")
        
        self.commit_transaction(request.transaction)
        self.db_manager.update_datastore_item_status(request.ballot_number, request.server_id, "committed")

        return paxos_pb2.CommitResponse(
            success=True,
            message="Transaction committed"
        )
    
    def Abort(self, request, context):
        if not self.is_active:
            if PRINT_STATEMENTS:
                print(f"Server {self.server_id} is not active. Ignoring abort message.")
            return paxos_pb2.AbortResponse()
        
        if PRINT_STATEMENTS:
            print(f"Received abort message: {request}")

        if request.transaction.type == "intra":
            self.db_manager.insert_datastore_item(request.ballot_number, request.server_id, request.transaction, "aborted")
        elif request.transaction.type == "cross":
            self.db_manager.insert_datastore_item(request.ballot_number, request.server_id, request.transaction, "prepare-aborted")
        self.ballot_number = request.ballot_number
        print(f"Transaction aborted: {request.transaction}")
        return paxos_pb2.AbortResponse()

    def compare_datastore(self, datastore_items):
        curr_datastore_items = self.db_manager.get_transactions()

        if PRINT_STATEMENTS:
            print("This is the current datastore:")
            print(curr_datastore_items)
        
        # Convert received datastore_items to the same format as curr_datastore_items
        received_items = [
            (item.ballot_number, item.server_id, item.transaction.sender, item.transaction.receiver, item.transaction.amount, item.transaction.timestamp, item.transaction.type, item.message)
            for item in datastore_items
        ]
        
        if PRINT_STATEMENTS:
            print("Converted received datastore items:")
            print(received_items)
        
        different_records = []
        
        # Compare from the end until a match is found
        i = len(received_items) - 1
        j = len(curr_datastore_items) - 1
        if PRINT_STATEMENTS:
            print(f"i: {i}, j: {j}")
            print("Comparing received and current datastore items:")
        if i == j:
            return different_records
        
        if i > j:
            if PRINT_STATEMENTS:
                print("Received items are more than current datastore items")
            for k in range(i, j, -1):
                different_records.append(received_items[k])
            self.synchronize_state(different_records)
            return None
        else:
            if PRINT_STATEMENTS:
                print("Current datastore items are more than received items")
            for k in range(j, i, -1):
                different_records.append(curr_datastore_items[k])
            if PRINT_STATEMENTS:
                print("Different records:")
            print(different_records)
            return different_records
    
    def synchronize_state_in_leader(self, datastore_items):
        print("Synchronizing state in leader")
        for item in datastore_items:
            if item.message == "committed":
                self.commit_transaction(item.transaction)
            self.db_manager.insert_datastore_item(item.ballot_number, item.server_id, item.transaction, item.message)

    def synchronize_state(self, datastore_items):
        print("Synchronizing state")
        for item in datastore_items:
            ballot_number = item[0]
            server_id = item[1]
            transaction = paxos_pb2.TransactionRequest(
                sender=item[2],
                receiver=item[3],
                amount=item[4],
                timestamp=item[5],
                type=item[6]
            )
            status = item[7]
            if status == "committed":
                self.commit_transaction(transaction)
            self.db_manager.insert_datastore_item(ballot_number, server_id, transaction, status)

def serve(server_id, config):
    # Extract the port and cluster_id for the current server
    current_server = next(server for server in config['servers'] if server['id'] == server_id)
    print(f"current_server: {current_server}")
    port = current_server['port']
    cluster_id = current_server['cluster_id']
    print(f"cluster_id: {cluster_id}")
    
    # Construct the list of other servers by cluster
    other_servers_by_cluster = {}
    for cluster in config['clusters']:
        cluster_id_new = cluster['cluster_id']
        other_servers_by_cluster[cluster_id_new] = [
            f"localhost:{server['port']}" for server in config['servers']
            if server['cluster_id'] == cluster_id_new and server['id'] != server_id
        ]

    # Get the client range for the current server's cluster
    client_range = next(cluster['client_range'] for cluster in config['clusters'] if cluster['cluster_id'] == cluster_id)
    print(f"Server {server_id} in cluster {cluster_id} serving clients {client_range[0]} to {client_range[1]}")

    # Get the number of servers in the current cluster
    num_servers_in_cluster = len([server for server in config['servers'] if server['cluster_id'] == cluster_id])

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    paxos_pb2_grpc.add_TransactionServiceServicer_to_server(TransactionService(server_id, cluster_id, other_servers_by_cluster, client_range, num_servers_in_cluster), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f'Server {server_id} in cluster {cluster_id} running on port {port}')
    if PRINT_STATEMENTS:
        print(f'Other servers by cluster: {other_servers_by_cluster}')
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
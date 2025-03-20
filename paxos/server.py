import grpc
import time
import json
import pickle
import os
import sys
import random
import time
import asyncio
import paxos_pb2
import paxos_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp
from datetime import datetime
from concurrent import futures
from performance_tracker import PerformanceTracker

PRINT_STATEMENTS = False

def get_committed_log_filename(server_id):
    return f'committed_log_server_{server_id}.pkl'

def initialize_committed_log_file(server_id):
    """Create the log file if it does not exist."""
    filename = get_committed_log_filename(server_id)
    with open(filename, 'wb') as f:
        pickle.dump([], f)  # Create an empty list in the JSON file

def append_to_committed_log_file(server_id, major_block):
    """Append a new major block to the committed log file."""
    filename = get_committed_log_filename(server_id)
    with open(filename, 'rb') as f:
        committed_log = pickle.load(f)
    
    # Append the new major block
    committed_log.append(major_block)

    # Save back to the file
    with open(filename, 'wb') as f:
        pickle.dump(committed_log, f)

def load_committed_log(server_id):
    """Load the committed log from the file."""
    filename = get_committed_log_filename(server_id)
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
    else:
        return []

class PaxosService(paxos_pb2_grpc.PaxosServicer):
    global_ballot_num = 0
    num_servers = 5

    def __init__(self, server_id, server_name, other_servers):
        self.server_id = server_id
        self.server_name = server_name
        self.other_servers = other_servers
        self.balance = 100  # Initialize balances
        self.local_log = []
        # self.commited_log = []
        self.accept_num = None
        self.accept_val = None
        self.ballot_num = None
        # intially all servers are not active. They will be activated by from controller
        self.is_active = False
        self.previous_commited_ballot_num = -1
        self.major_block = []
        self.promised_ballot_num = None
        self.performance_tracker = PerformanceTracker()
        initialize_committed_log_file(self.server_id)

    @PerformanceTracker().track_rpc 
    @PerformanceTracker().track_transaction
    def HandleTransaction(self, request, context):
        sender = request.sender
        receiver = request.receiver
        amount = request.amount
        timestamp = Timestamp()
        timestamp.GetCurrentTime()
        if PRINT_STATEMENTS:
            print(f"Received transaction: {sender} -> {receiver} : {amount} at {timestamp}")

        def process_transaction():
            if self.balance >= amount:
                self.balance -= amount
                transaction = paxos_pb2.Transaction(sender=sender, receiver=receiver, amount=amount, timestamp=timestamp)
                self.local_log.append(transaction)
                if PRINT_STATEMENTS:
                    print(f"Transaction successful in server {self.server_id}: {sender} -> {receiver} : {amount}")
                    print(f"Updated balance in server {self.server_id}: {self.balance}")
                return paxos_pb2.CommitResponse(status=True)
            else:
                if PRINT_STATEMENTS:
                    print(f"Transaction failed in server {self.server_id}: {sender} -> {receiver} : {amount}")
                return paxos_pb2.CommitResponse(status=False)
            
        response = process_transaction()
        if response.status:
            return response

        asyncio.run(self.initiate_leader_election())

        # Retry the transaction after leader election
        response = process_transaction()
        if response.status:
            if PRINT_STATEMENTS:
                print(f"Transaction successful in server {self.server_id}: {sender} -> {receiver} : {amount}")
                print(f"Updated balance in server {self.server_id}: {self.balance}")
            return response
        else:
            if PRINT_STATEMENTS:
                print(f"Transaction failed after leader election in server {self.server_id}: {sender} -> {receiver} : {amount}")
            response = self.retry_transaction(sender, receiver, amount, timestamp)
            return paxos_pb2.CommitResponse(status=response)
        
    def retry_transaction(self, sender, receiver, amount, timestamp):
        retry_interval = random.uniform(0.01, 0.03)  # Retry interval in seconds
        time.sleep(retry_interval)

        def process_transaction():
            if self.balance >= amount:
                self.balance -= amount
                transaction = paxos_pb2.Transaction(sender=sender, receiver=receiver, amount=amount, timestamp=timestamp)
                self.local_log.append(transaction)
                if PRINT_STATEMENTS:
                    print(f"Transaction successful in server before leader election {self.server_id}: {sender} -> {receiver} : {amount}")
                    print(f"Updated balance in server {self.server_id}: {self.balance}")
                return True
            else:
                if PRINT_STATEMENTS:
                    print(f"Transaction failed in server {self.server_id}: {sender} -> {receiver} : {amount}")
                return False
            
        response = process_transaction()
        if response:
            return response

        if PRINT_STATEMENTS:
            print(f"Retrying transaction: {sender} -> {receiver} : {amount} at {timestamp}")
        asyncio.run(self.initiate_leader_election())

        response = process_transaction()
        # Retry the transaction after leader election
        if response:
            if PRINT_STATEMENTS:
                print(f"Transaction successful in server {self.server_id}: {sender} -> {receiver} : {amount}")
                print(f"Updated balance in server {self.server_id}: {self.balance}")
            return True
        else:
            if PRINT_STATEMENTS:
                print(f"Transaction failed after retry in server {self.server_id}: {sender} -> {receiver} : {amount}")
            # Schedule another retry
            return self.retry_transaction(sender, receiver, amount, timestamp)
        
    @PerformanceTracker().track_rpc    
    def Prepare(self, request, context):
        if not self.is_active:
            if PRINT_STATEMENTS:
                print(f"Server {self.server_id} is not active. Ignoring prepare message.")
            return
        
        ballot_number = request.ballot_num
        server_id = request.id
        if PRINT_STATEMENTS:
            print(f"Received prepare message from {server_id} with ballot number {ballot_number}")

        # Check if a promise has already been sent for this ballot number
        if self.promised_ballot_num and self.promised_ballot_num >= ballot_number:
            if PRINT_STATEMENTS:
                print(f"Rejecting prepare message from {server_id} with ballot number {ballot_number}")
            return paxos_pb2.PromiseResponse(
                server_id=server_id,
                ballot_num=-1  # Denotes rejection
            )

        # Update the promised ballot number
        self.promised_ballot_num = ballot_number

        if self.previous_commited_ballot_num and self.previous_commited_ballot_num >= ballot_number:
            if PRINT_STATEMENTS:
                print(f"Rejecting prepare message from {server_id} with ballot number {ballot_number}")
            return paxos_pb2.PromiseResponse(
                server_id=server_id,
                ballot_num=-1  # Denotes rejection
            )
        
        if self.accept_num and self.accept_val:
            # There is a value that has been proposed and accepted but not decided
            if PRINT_STATEMENTS:
                print(f"Informing leader about the latest accepted value and ballot number")
            if self.accept_num > ballot_number:
                return paxos_pb2.PromiseResponse(
                    ballot_num=ballot_number,
                    server_id=server_id,
                    accept_num=self.accept_num,
                    accept_val=self.accept_val,
                    transactions=[]
                )
        else:
            # No such value, inform leader about locally processed transactions even if it is empty
            if PRINT_STATEMENTS:
                print(f"Informing leader about locally processed transactions")
            return paxos_pb2.PromiseResponse(
                ballot_num=ballot_number,
                server_id=server_id,
                accept_num=self.accept_num,
                accept_val=[],
                transactions=self.local_log
            )
    
    @PerformanceTracker().track_rpc
    def Accept(self, request, context):
        if not self.is_active:
            if PRINT_STATEMENTS:
                print(f"Server {self.server_id} is not active. Ignoring accept message.")
            return
        
        self.accept_num = request.ballot_num
        self.accept_val = request.major_block
        if PRINT_STATEMENTS:
            print(f"Received accept message with ballot number {self.accept_num} and transactions {self.accept_val}")
            print(f"Accepted value: {self.accept_val}")
        return paxos_pb2.AcceptedResponse(
            ballot_num=request.ballot_num,
            server_id=request.server_id,
            major_block=request.major_block
        )
    
    @PerformanceTracker().track_rpc
    def Commit(self, request, context):
        if not self.is_active:
            if PRINT_STATEMENTS:
                print(f"Server {self.server_id} is not active. Ignoring commit message.")
            return paxos_pb2.CommitResponse(status=False)
        
        self.accept_num = None
        self.accept_val = None
        self.promised_ballot_num = None
        major_block = request.major_block
        # self.commited_log.append(major_block)
        append_to_committed_log_file(self.server_id, major_block)
        self.previous_commited_ballot_num = major_block.ballot_num
        self.update_balance(major_block.transactions)
        if PRINT_STATEMENTS:
            print(f"Committed major block: {major_block}")
            print(f"Updated balance in server {self.server_id}: {self.balance}")

        # Remove committed transactions from the local log
        committed_transactions = set((t.sender, t.receiver, t.amount, t.timestamp.seconds, t.timestamp.nanos) for t in major_block.transactions)
        self.local_log = [t for t in self.local_log if (t.sender, t.receiver, t.amount, t.timestamp.seconds, t.timestamp.nanos) not in committed_transactions]

        return paxos_pb2.CommitResponse(status=True)
    
    def Performance(self, request, context):
        metrics = self.performance_tracker.get_metrics()
        return paxos_pb2.PerformanceResponse(
            transaction_throughput=metrics["transaction_throughput"],
            average_transaction_latency=metrics["average_transaction_latency"],
            leader_election_count=metrics["leader_election_count"],
            average_leader_election_time=metrics["average_leader_election_time"],
            rpc_call_count=metrics["rpc_call_count"],
            average_rpc_time=metrics["average_rpc_time"]
        )
    
    def GetCurrentBalance(self, request, context):
        response = paxos_pb2.GetCurrentBalanceResponse()
        response.balance = self.balance
        for txn in self.local_log:
            transaction = paxos_pb2.Transaction(
                sender=txn.sender,
                receiver=txn.receiver,
                amount=txn.amount,
                timestamp=txn.timestamp
            )
            response.local_logs.append(transaction)
        return response

    def update_balance(self, transactions):
        for transaction in transactions:
            if transaction.receiver == self.server_name:
                self.balance += transaction.amount
        if PRINT_STATEMENTS:
            print(f"Updated balance in server {self.server_id}: {self.balance}")

    def SetActiveStatus(self, request, context):
        prev_status = self.is_active
        self.is_active = request.is_active
        if PRINT_STATEMENTS:
            print(f"Set is_active to {self.is_active} for server {self.server_id}")
        if self.is_active:
            # time.sleep(0.05)
            asyncio.run(self.synchronize_with_others())
        return paxos_pb2.SetActiveStatusResponse(success=True)

    async def synchronize_with_others(self):
        if PRINT_STATEMENTS:
            print(f"Synchronizing with other servers...")
        tasks = [self.send_synchronize(server_address) for server_address in self.other_servers]
        responses = await asyncio.gather(*tasks)
        
        most_updated_log = []
        highest_ballot_num = self.previous_commited_ballot_num

        for response in responses:
            if response:
                for log in response.committed_log:
                    if log.ballot_num > highest_ballot_num:
                        highest_ballot_num = log.ballot_num
                        most_updated_log = response.committed_log

        if most_updated_log:
            self.update_committed_log(most_updated_log)

    async def send_synchronize(self, server_address):
        committed_log = load_committed_log(self.server_id)
        if PRINT_STATEMENTS:
            print(f"Sending synchronize request to {server_address}")
        try:
            async with grpc.aio.insecure_channel(server_address) as channel:
                stub = paxos_pb2_grpc.PaxosStub(channel)
                response = await stub.Synchronize(paxos_pb2.SynchronizeRequest(
                    # committed_log=self.commited_log,
                    committed_log=committed_log,
                    last_committed_ballot_num=self.previous_commited_ballot_num
                ))
                if PRINT_STATEMENTS:
                    print(f"Received synchronize response from {server_address}: {response}")
                return response
        except grpc.RpcError as e:
            if PRINT_STATEMENTS:
                print(f"Failed to communicate with {server_address}: {e}")
            return None

    @PerformanceTracker().track_rpc 
    def Synchronize(self, request, context):
        if not self.is_active:
            if PRINT_STATEMENTS:
                print(f"Server {self.server_id} is not active. Ignoring synchronize request.")
            return
        if PRINT_STATEMENTS:
            print(f"Received synchronization request with last committed ballot number {request.last_committed_ballot_num}")
        committed_logs = load_committed_log(self.server_id)
        missing_logs = [log for log in committed_logs if log.ballot_num > request.last_committed_ballot_num]
        # missing_logs = [log for log in self.commited_log if log.ballot_num > request.last_committed_ballot_num]
        if PRINT_STATEMENTS:
            print(f"Sending missing logs: {missing_logs}")
        return paxos_pb2.SynchronizeResponse(committed_log=missing_logs)

    def update_committed_log(self, committed_log):
        self_commited_log = load_committed_log(self.server_id)
        for log in committed_log:
            if log not in self_commited_log:
                append_to_committed_log_file(self.server_id, log)
                self.update_balance(log.transactions)
        if PRINT_STATEMENTS:
            print(f"Updated committed log: {load_committed_log(self.server_id)}")
      
    async def send_prepare(self, server_address):
        if PRINT_STATEMENTS:
            print(f"Sending prepare message to {server_address}")
        try:
            async with grpc.aio.insecure_channel(server_address) as channel:
                stub = paxos_pb2_grpc.PaxosStub(channel)
                response = await stub.Prepare(paxos_pb2.PrepareRequest(ballot_num=self.ballot_num, id=self.server_id))
                if PRINT_STATEMENTS:
                    print(f"Received Promise message from {server_address}: {response}")
                return response
        except grpc.RpcError as e:
            if PRINT_STATEMENTS:
                print(f"Failed to communicate with {server_address}: {e}")
            return None
        
    async def send_accept(self, server_address, major_block):
        if PRINT_STATEMENTS:
            print(f"Sending accept message to {server_address}")
        try:
            async with grpc.aio.insecure_channel(server_address) as channel:
                stub = paxos_pb2_grpc.PaxosStub(channel)
                response = await stub.Accept(paxos_pb2.AcceptRequest(ballot_num=self.ballot_num, server_id=self.server_id, major_block=major_block))
                if PRINT_STATEMENTS:
                    print(f"Received Accepted message from {server_address}: {response}")
                return response
        except grpc.RpcError as e:
            if PRINT_STATEMENTS:
                print(f"Failed to communicate with {server_address}: {e}")
            return None
        
    async def send_commit(self, server_address, major_block):
        if PRINT_STATEMENTS:
            print(f"Sending commit message to {server_address}")
        try:
            async with grpc.aio.insecure_channel(server_address) as channel:
                stub = paxos_pb2_grpc.PaxosStub(channel)
                response = await stub.Commit(paxos_pb2.CommitRequest(ballot_num=self.ballot_num, server_id=self.server_id, major_block=major_block))
                if PRINT_STATEMENTS:
                    print(f"Received Commited message response from {server_address}: {response}")
                return response
        except grpc.RpcError as e:
            if PRINT_STATEMENTS:
                print(f"Failed to communicate with {server_address}: {e}")
            return None

    @PerformanceTracker().track_leader_election
    async def initiate_leader_election(self):
        self.ballot_num = self.propose_ballot_num()
        if PRINT_STATEMENTS:
            print(f"Initiating leader election with ballot number: {self.ballot_num}")
            print("Other servers: ", self.other_servers)
        
        tasks = [self.send_prepare(server_address) for server_address in self.other_servers]
        self.promised_ballot_num = self.ballot_num
        responses = await asyncio.gather(*tasks)

        # Filter out None responses and count valid responses
        valid_responses = [response for response in responses if response is not None and response.ballot_num != -1]

        if all(response.transactions == [] for response in valid_responses):
            if PRINT_STATEMENTS:
                print("All servers returned empty local_logs. Aborting leader election.")
            return
        
        if len(valid_responses) >= len(self.other_servers) // 2:
            # Check if any response has accept_val and accept_num
            max_accept_num = -1
            chosen_accept_val = None
            for response in valid_responses:
                if response.accept_num > max_accept_num:
                    max_accept_num = response.accept_num
                    chosen_accept_val = response.accept_val

            if chosen_accept_val:
                # Send accept message with chosen accept_val
                accept_tasks = [self.send_accept(server_address, chosen_accept_val) for server_address in self.other_servers]
                accept_responses = await asyncio.gather(*accept_tasks)
            else:
                # Construct MajorBlock with all local transactions
                self.construct_major_block(valid_responses)
                accept_tasks = [self.send_accept(server_address, self.major_block) for server_address in self.other_servers]
                accept_responses = await asyncio.gather(*accept_tasks)

            # Filter out None responses and count valid responses
            valid_accept_responses = [response for response in accept_responses if response is not None]
            if len(valid_accept_responses) >= len(self.other_servers) // 2:
                # Commit the major block
                # self.commited_log.append(self.major_block)
                append_to_committed_log_file(self.server_id, self.major_block)
                if PRINT_STATEMENTS:
                    # print(f"Committed major block: {self.commited_log[-1]}")
                    print(f"Committed major block: {self.major_block}")
                self.update_balance(self.major_block.transactions)

                committed_transactions = set((t.sender, t.receiver, t.amount, t.timestamp.seconds, t.timestamp.nanos) for t in self.major_block.transactions)
                self.local_log = [t for t in self.local_log if (t.sender, t.receiver, t.amount, t.timestamp.seconds, t.timestamp.nanos) not in committed_transactions]

                # Send commit message to all other servers
                commit_tasks = [self.send_commit(server_address, self.major_block) for server_address in self.other_servers]
                commit_responses = await asyncio.gather(*commit_tasks)
                if PRINT_STATEMENTS:
                    print(f"Received commit responses: {commit_responses}")
                return
            else:
                if PRINT_STATEMENTS:
                    print("Failed to receive majority accept responses. Leader election failed.")
        else:
            if PRINT_STATEMENTS:
                print("Failed to receive majority responses. Leader election failed.")
            

    def construct_major_block(self, responses):
        combined_log = self.local_log[:]
        for response in responses:
            combined_log.extend(response.transactions)
        
        self.major_block = paxos_pb2.MajorBlock(
            ballot_num=self.ballot_num,
            server_id=self.server_id,
            transactions=combined_log
        )
        if PRINT_STATEMENTS:
            print(f"Constructed Major Block: {self.major_block}")

    def propose_ballot_num(self):
        if self.previous_commited_ballot_num > PaxosService.global_ballot_num:
            PaxosService.global_ballot_num = self.previous_commited_ballot_num + 1
        else:
            PaxosService.global_ballot_num += 1
        return PaxosService.global_ballot_num
    
    def PrintBalance(self, request, context):
        print()
        print("*" * 50)
        print(f"Balance for {self.server_name}: {self.balance}\n")
        return paxos_pb2.PrintResponse(response=True)

    def PrintLog(self, request, context):
        print("*" * 50)
        print(f"Local log of server {self.server_name}:")
        if len(self.local_log) == 0:
            print("No transactions in local log")
        else:
            for transaction in self.local_log:
                timestamp = datetime.fromtimestamp(transaction.timestamp.seconds + transaction.timestamp.nanos / 1e9)
                formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Format to milliseconds
                print(f"{transaction.sender} -> {transaction.receiver} : {transaction.amount} at {formatted_time}")
                # print(f"{transaction.sender} -> {transaction.receiver} : {transaction.amount} at {transaction.timestamp}")
        print()
        return paxos_pb2.PrintResponse(response=True)

    def PrintDB(self, request, context):
        print("*" * 50)
        # datastore = [str(transaction) for transaction in self.commited_log]
        committed_logs = load_committed_log(self.server_id)
        print(f"Database for {self.server_name}:")
        # for record in self.commited_log:
        for record in committed_logs:
            print(f"ballot number: {record.ballot_num}")
            print(f"server id: {record.server_id}")
            for transaction in record.transactions:
                timestamp = datetime.fromtimestamp(transaction.timestamp.seconds + transaction.timestamp.nanos / 1e9)
                formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Format to milliseconds
                print(f"{transaction.sender} -> {transaction.receiver} : {transaction.amount} at {formatted_time}")
            print()
        print()
        # print(f"Local log: {datastore}")
        return paxos_pb2.PrintResponse(response=True)

def serve(server_id, config):
    # Extract the port for the current server
    current_server = next(server for server in config['servers'] if server['id'] == server_id)
    port = current_server['port']
    
    # Construct the list of other servers
    other_servers = [f"localhost:{server['port']}" for server in config['servers'] if server['id'] != server_id]
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server_name = next(server['name'] for server in config['servers'] if server['id'] == server_id)
    # print(f"Server {server_id} name: {server_name}")
    paxos_pb2_grpc.add_PaxosServicer_to_server(PaxosService(server_id, server_name, other_servers), server)
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
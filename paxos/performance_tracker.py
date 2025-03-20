import threading
import time

class PerformanceTracker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PerformanceTracker, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.transaction_count = 0
        self.total_transaction_time = 0.0
        self.leader_election_count = 0
        self.total_leader_election_time = 0.0
        self.rpc_call_count = 0
        self.total_rpc_time = 0.0
        self.start_time = time.time()

    def track_transaction(self, func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            self.transaction_count += 1
            self.total_transaction_time += (end_time - start_time)
            return result
        return wrapper

    def track_leader_election(self, func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            self.leader_election_count += 1
            self.total_leader_election_time += (end_time - start_time)
            return result
        return wrapper

    def track_rpc(self, func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            self.rpc_call_count += 1
            self.total_rpc_time += (end_time - start_time)
            return result
        return wrapper

    def get_metrics(self):
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        throughput = self.transaction_count / elapsed_time if elapsed_time > 0 else 0
        average_transaction_latency = self.total_transaction_time / self.transaction_count if self.transaction_count > 0 else 0
        average_leader_election_time = self.total_leader_election_time / self.leader_election_count if self.leader_election_count > 0 else 0
        average_rpc_time = self.total_rpc_time / self.rpc_call_count if self.rpc_call_count > 0 else 0
        return {
            "transaction_throughput": throughput,
            "average_transaction_latency": average_transaction_latency,
            "leader_election_count": self.leader_election_count,
            "average_leader_election_time": average_leader_election_time,
            "rpc_call_count": self.rpc_call_count,
            "average_rpc_time": average_rpc_time
        }
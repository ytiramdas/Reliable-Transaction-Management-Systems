import sqlite3

PRINT_STATEMENTS = False

class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS balances (
                id INTEGER PRIMARY KEY,
                balance INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locks (
                id INTEGER PRIMARY KEY,
                locked INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS datastore_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ballot_number INTEGER,
                server_id INTEGER,
                sender TEXT,
                receiver TEXT,
                amount INTEGER,
                timestamp INTEGER,
                type TEXT,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print(f"Database initialized: {self.db_file}")

    def initialize(self, client_range):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM datastore_items')
        for client_id in range(client_range[0], client_range[1] + 1):
            cursor.execute('''
                INSERT INTO balances (id, balance) 
                VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET balance=excluded.balance
            ''', (client_id, 10))
            cursor.execute('''
                INSERT INTO locks (id, locked) 
                VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET locked=excluded.locked
            ''', (client_id, 0))
        conn.commit()
        conn.close()
        if PRINT_STATEMENTS:
            print(f"Clients and locks initialized for range {client_range}")

    def lock_client(self, client_id):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE locks SET locked = 1 WHERE id = ?
        ''', (client_id,))
        conn.commit()
        conn.close()
        print(f"Client locked: {client_id}")

    def unlock_client(self, client_id):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE locks SET locked = 0 WHERE id = ?
        ''', (client_id,))
        conn.commit()
        conn.close()
        print(f"Client unlocked: {client_id}")

    def is_locked(self, client_id):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT locked FROM locks WHERE id = ?
        ''', (client_id,))
        result = cursor.fetchone()
        conn.close()
        if result is not None:
            return result[0] == 1
        return False

    def get_balance(self, client_id):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT balance FROM balances WHERE id = ?
        ''', (client_id,))
        result = cursor.fetchone()
        conn.close()
        if result is not None:
            return result[0]
        return None

    def update_balance(self, client_id, amount):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE balances SET balance = balance + ? WHERE id = ?
        ''', (amount, client_id))
        conn.commit()
        conn.close()
        if PRINT_STATEMENTS:
            print(f"Balance updated for client {client_id}: {amount}")

    def insert_datastore_item(self, ballot_number, server_id, transaction, status):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM datastore_items WHERE ballot_number = ? AND server_id = ? AND sender = ? AND receiver = ? AND amount = ? AND timestamp = ? AND type = ? AND status = ?
        ''', (ballot_number, server_id, transaction.sender, transaction.receiver, transaction.amount, transaction.timestamp, transaction.type, status))
        result = cursor.fetchone()
        if result[0] == 0:
            cursor.execute('''
                INSERT INTO datastore_items (ballot_number, server_id, sender, receiver, amount, timestamp, type, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ballot_number, server_id, transaction.sender, transaction.receiver, transaction.amount, transaction.timestamp, transaction.type, status))
            conn.commit()
            if PRINT_STATEMENTS:
                print(f"Datastore item inserted: {transaction}")
        else:
            if PRINT_STATEMENTS:
                print(f"Datastore item already exists: {transaction}")
        conn.close()

    def update_datastore_item_status(self, ballot_number, server_id, status):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE datastore_items SET status = ? WHERE ballot_number = ? AND server_id = ?
        ''', (status, ballot_number, server_id))
        conn.commit()
        conn.close()
        if PRINT_STATEMENTS:
            print(f"Datastore item status updated: ballot_number={ballot_number}, server_id={server_id}, status={status}")

    def get_transactions(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ballot_number, server_id, sender, receiver, amount, timestamp, type, status FROM datastore_items
        ''')
        transactions = cursor.fetchall()
        conn.close()
        return transactions
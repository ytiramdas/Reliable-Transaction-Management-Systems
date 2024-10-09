# Paxos-Transaction

# gRPC Server and Client Setup

This project demonstrates how to run multiple gRPC servers on different ports and send transactions to them based on the sender.

## Prerequisites

- Python 3.x
- `pip` (Python package installer)
- `virtualenv` package
- gRPC and related packages

## Setup

1. **Clone the repository**:
   ```sh
   git clone git@github.com:ytiramdas/Paxos-Transaction.git
   cd Paxos-Transaction
   ```
2. **Create Virtual Environment**:
    ```sh
   python3 -m venv myenv
   ```
3. **Activate the virtual environment**:
- On macOS and Linux
    ```
    source myenv/bin/activate
    ```
- On Windows
    ```
    myenv\Scripts\activate
    ```
4. **Install dependencies**:
    ```sh
   pip install -r requirements.txt
   ```

## Running the servers
1. Ensure the run_servers.sh script is executable:
    ```
    chmod +x run_servers.sh
    ```
2. Run the script to start the servers:
    ```
    ./run_servers.sh
    ```

## Running the client

1. **Run the client script:**
    ```
    python3 client.py
    ```
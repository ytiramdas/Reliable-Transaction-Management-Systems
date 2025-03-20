#!/bin/bash

# Array of server IDs
server_ids=(1 2 3 4 5)

# Loop through the server IDs and open a new terminal for each
for id in "${server_ids[@]}"
do
  osascript -e "tell application \"Terminal\" to do script \"cd $(pwd); source myenv/bin/activate; python3 $(pwd)/server.py $id\""
done
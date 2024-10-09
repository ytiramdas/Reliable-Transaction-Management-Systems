#!/bin/bash

# Array of ports
ports=(50051 50052 50053 50054 50055)

# Loop through the ports and open a new terminal for each
for port in "${ports[@]}"
do
  osascript -e "tell application \"Terminal\" to do script \"cd $(pwd); source myenv/bin/activate; python3 $(pwd)/server.py $port\""
done
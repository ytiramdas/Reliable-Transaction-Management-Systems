#!/bin/bash

# Loop through the server IDs and open a new terminal for each
osascript -e "tell application \"Terminal\" to do script \"cd $(pwd); source myenv/bin/activate; python3 $(pwd)/server.py 1\""
osascript -e "tell application \"Terminal\" to do script \"cd $(pwd); source myenv/bin/activate; python3 $(pwd)/server.py 2\""
osascript -e "tell application \"Terminal\" to do script \"cd $(pwd); source myenv/bin/activate; python3 $(pwd)/server.py 3\""
osascript -e "tell application \"Terminal\" to do script \"cd $(pwd); source myenv/bin/activate; python3 $(pwd)/server.py 4\""
osascript -e "tell application \"Terminal\" to do script \"cd $(pwd); source myenv/bin/activate; python3 $(pwd)/server.py 5\""
osascript -e "tell application \"Terminal\" to do script \"cd $(pwd); source myenv/bin/activate; python3 $(pwd)/server.py 6\""
osascript -e "tell application \"Terminal\" to do script \"cd $(pwd); source myenv/bin/activate; python3 $(pwd)/server.py 7\""
osascript -e "tell application \"Terminal\" to do script \"cd $(pwd); source myenv/bin/activate; python3 $(pwd)/server.py 8\""
osascript -e "tell application \"Terminal\" to do script \"cd $(pwd); source myenv/bin/activate; python3 $(pwd)/server.py 9\""
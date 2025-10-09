#!/bin/bash

# Base URL of your server
BASE_URL="http://localhost:8080/upload"

# Number of concurrent POST requests
NUM_REQUESTS=5

# Function to send POST request
send_post() {
    JSON_DATA="{\"name\": \"Nistha\", \"project\": \"HTTP Server\", \"request\": \"$1\"}"
    curl -s -X POST "$BASE_URL" \
         -H "Content-Type: application/json" \
         -d "$JSON_DATA"
    echo ""
}

# Loop to start multiple POST requests concurrently
for i in $(seq 1 $NUM_REQUESTS)
do
    send_post "$i" &
done

# Wait for all background requests to finish
wait

echo "✅ All POST requests completed."

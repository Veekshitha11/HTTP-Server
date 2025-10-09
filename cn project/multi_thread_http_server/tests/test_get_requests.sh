#!/bin/bash

# Base URL
BASE_URL="http://localhost:8080"

# Files to test (added notes.txt, friend.jpg, family.jpg)
FILES=("/" "/about.html" "/contact.html" "/sample.txt" "/logo.png" "/photo.png" "/notes.txt" "/friend.jpg" "/family.jpg")

for file in "${FILES[@]}"
do
    echo "Fetching $file ..."
    curl -O "$BASE_URL$file"
    echo ""
done

echo "✅ GET requests completed."

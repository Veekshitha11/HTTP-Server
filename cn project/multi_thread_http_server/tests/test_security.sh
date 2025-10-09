#!/bin/bash

# Base URL
BASE_URL="http://localhost:8080"

echo "🔒 Testing Path Traversal Protection"

# Test Path Traversal attempts
TRAVERSAL_PATHS=(
    "/../etc/passwd"
    "/../../config"
    "//etc/hosts"
)

for path in "${TRAVERSAL_PATHS[@]}"
do
    echo "Testing $path ..."
    curl -s -o /dev/null -w "%{http_code}\n" "$BASE_URL$path"
done

echo ""
echo "🔒 Testing Host Header Validation"

# Correct Host header
echo "Testing correct Host header ..."
curl -s -o /dev/null -w "%{http_code}\n" -H "Host: localhost:8080" "$BASE_URL/"

# Missing Host header (empty Host)
echo "Testing missing Host header ..."
curl -s -o /dev/null -w "%{http_code}\n" -H "Host:" "$BASE_URL/"

# Wrong Host header
echo "Testing wrong Host header ..."
curl -s -o /dev/null -w "%{http_code}\n" -H "Host: evil.com" "$BASE_URL/"

echo ""
echo "✅ Security tests completed."

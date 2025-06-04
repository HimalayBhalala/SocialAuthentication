#!/bin/bash

# Django Environment Variables Generator Script (Testing Version)
# Generates .env file with test/development values

echo "🧪 Django Test Environment Generator"
echo "===================================="
echo ""

# Generate random secret key
generate_secret_key() {
    python3 -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
secret_key = ''.join(secrets.choice(alphabet) for i in range(50))
print(secret_key)
" 2>/dev/null || openssl rand -base64 32 | tr -d "=+/" | cut -c1-50
}
import sys, hmac, hashlib, base64

# Unpack command line arguments
username, client_id, key = sys.argv[1:4]

# Create message and key bytes
message, key = (username + client_id).encode('utf-8'), key.encode('utf-8')

# Calculate secret hash
secret_hash = base64.b64encode(hmac.new(key, message, digestmod=hashlib.sha256).digest()).decode()

print(secret_hash)
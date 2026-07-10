import sys
import os
import requests
from requests.exceptions import ConnectionError

# Try to connect to backend
try:
    response = requests.get("http://localhost:8000/health")
    if response.status_code == 200:
        print("✅ Backend API is running and healthy.")
        print(response.json())
    else:
        print(f"❌ Backend API returned status code: {response.status_code}")
except ConnectionError:
    print("❌ Could not connect to Backend API. Is it running on port 8000?")

# Here you can also add checks for Redis, PostgreSQL if needed.
print("System check completed.")

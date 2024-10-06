import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
email = "test@email.pt"
password = "Password1234!"

# Register user
verification_link = requests.post(f"{BASE_URL}/user/register/", data = {
  "email": email,
  "password": password,
  "first_name": "First Name",
  "last_name": "Last Name"
}).json()["data"]["verification_link"]

# Verify link
requests.get(verification_link)

# Get token
token = requests.post(f"{BASE_URL}/token", data = {
  "email": email,
  "password": password,
}).json()["access"]

headers = {"headers": {"Authorization": f"Bearer {token}"}}
with open('api-fuzzing-overrides.json', 'w') as overrides_file:
     overrides_file.write(json.dumps(headers))

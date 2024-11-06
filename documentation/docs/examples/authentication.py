import requests

email = "your_email@example.com"
password = "your_password"

response = requests.post('https://predico-elia.inesctec.pt/api/v1/token',
                         data={'email': email, 'password': password})

# Check if authentication was successful
if response.status_code == 200:
    token = response.json().get('access')
    print(f"Access Token: {token}")
else:
    print("Authentication failed. Please check your credentials.")
    print(f"Status code: {response.status_code}")
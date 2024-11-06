# Authentication

Before interacting with the Predico API, you need to authenticate using your registered email and password.
**Ensure that you have completed the registration process and that your email address has been validated**. 
If you haven't registered yet, please refer to the [Forecaster Application](introduction.md) section for instructions.

## Retrieving an Access Token

To authenticate with the Predico API, you need to obtain an access token using your credentials. This token will be used in the headers of your subsequent API requests to authorize your actions.

Here is how you can retrieve an access token using Python:

```python title="authentication.py"
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
```

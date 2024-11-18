import requests

# Authenticate via `/token` endpoint
access_token = "your_access_token_here"
headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json'
}

# List your historical submissions:
response = requests.get(
    url='https://127.0.0.1/api/v1/market/challenge/submission',
    headers=headers
)

# Check if the request was successful
if response.status_code == 200:
    submissions = response.json()
else:
    print("Failed to retrieve submissions.")
    print(f"Status code: {response.status_code}")
    exit()

# Select a submission and respective challenge:
selected_submission = submissions["data"][0]
submission_id = selected_submission['id']
challenge_id = selected_submission['market_session_challenge']
print("Selected Submission:")
print(f"Submission ID: {submission_id}")
print(f"Challenge ID: {challenge_id}")

# Request the submitted forecast timeseries for this challenge
response = requests.get(
    url='https://127.0.0.1/api/v1/market/challenge/submission/forecasts',
    params={'challenge': challenge_id},
    headers=headers
)

# Check if the request was successful
if response.status_code == 200:
    submission_forecasts = response.json()
    print(submission_forecasts)
else:
    print("Failed to retrieve submission forecasts.")
    print(f"Status code: {response.status_code}")
    exit()
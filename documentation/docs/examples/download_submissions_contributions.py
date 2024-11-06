import requests

# Authenticate via `/token` endpoint
access_token = "your_access_token_here"
headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json'
}

# List your historical submissions:
response = requests.get(
    url='https://predico-elia.inesctec.pt/api/v1/market/challenge/submission',
    headers=headers
)

# Check if the request was successful
if response.status_code == 200:
    challenges = response.json()
else:
    print("Failed to retrieve submissions.")
    print(f"Status code: {response.status_code}")
    exit()

# Select a submission and respective challenge:
selected_submission = challenges[0]
submission_id = selected_submission['id']
challenge_id = selected_submission['market_session_challenge']
print("Selected Submission:")
print(f"Submission ID: {submission_id}")
print(f"Challenge ID: {challenge_id}")

# Request the submission contributions (weights) for the selected challenge
response = requests.get(
    url='https://predico-elia.inesctec.pt/api/v1/market/challenge/ensemble-weights',
    params={'challenge': challenge_id},
    headers=headers
)

# Check if the request was successful
if response.status_code == 200:
    submission_contributions = response.json()
    print(submission_contributions)
else:
    print("Failed to retrieve submission contributions.")
    print(f"Status code: {response.status_code}")
    exit()
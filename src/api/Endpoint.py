from dataclasses import dataclass
from collections import namedtuple

api_version = "v1"
api_base_url = f"/api/{api_version}"
fields = ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'uri')
endpoint = namedtuple('endpoint', fields, defaults=(None,) * len(fields))

# HTTP methods
http_methods = "GET", "POST", "PUT", "DELETE", "PATCH",

# Authentication
login = endpoint(*http_methods, f"{api_base_url}/token/login")

# User & Role
user_list = endpoint(*http_methods, f"{api_base_url}/user/list")
user_resources = endpoint(*http_methods, f"{api_base_url}/user/resource")

# Market endpoints
market_session = endpoint(*http_methods, f"{api_base_url}/market/session")
market_challenge = endpoint(*http_methods, f"{api_base_url}/market/challenge")
market_challenge_ensemble_forecasts = endpoint(*http_methods, f"{api_base_url}/market/challenge/{{challenge_id}}/ensemble-forecasts")
market_challenge_ensemble_ramp_alerts = endpoint(*http_methods, f"{api_base_url}/market/challenge/{{challenge_id}}/ramp-alerts")
market_challenge_ensemble_weights = endpoint(*http_methods, f"{api_base_url}/market/challenge/ensemble-weights")
market_challenge_ensemble_meta = endpoint(*http_methods, f"{api_base_url}/market/challenge/ensemble-forecasts-meta")
market_challenge_id_ensemble_weights = endpoint(*http_methods, f"{api_base_url}/market/challenge/{{challenge_id}}/ensemble-weights")
market_challenge_submissions = endpoint(*http_methods, f"{api_base_url}/market/challenge/submission")
market_challenge_submissions_forecasts = endpoint(*http_methods, f"{api_base_url}/market/challenge/submission/forecasts")
market_challenge_submissions_scores = endpoint(*http_methods, f"{api_base_url}/market/challenge/{{challenge_id}}/submission-scores")

# Data endpoints
data_measurements = endpoint(*http_methods, f"{api_base_url}/data/raw-measurements")
data_forecasts = endpoint(*http_methods, f"{api_base_url}/data/market-forecasts")


@dataclass(frozen=True)
class Endpoint:
    http_method: str
    uri: str

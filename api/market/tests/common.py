import numpy as np
import pandas as pd
import datetime as dt

from django.urls import reverse
from django.contrib.auth import get_user_model


def drop_dict_field(d, key):
    new_d = d.copy()
    new_d.pop(key)
    return new_d


def create_user(use_custom_data=False, verify_email=True, **kwargs):
    if use_custom_data:
        data = {
            'email': kwargs["email"],
            'password': kwargs["password"],
            'first_name': kwargs["first_name"],
            'last_name': kwargs["last_name"],
        }
    else:
        data = {
            'email': 'carl.sagan@bob.bob',
            'password': 'foo',
            'first_name': "Carl",
            'last_name': "Sagan"
        }

    user = get_user_model().objects.create_user(**data,
                                                is_active=verify_email,
                                                is_verified=verify_email)
    user.raw_password = data["password"]
    return user


def create_superuser(use_custom_data, **kwargs):
    if use_custom_data:
        data = {'email': kwargs['email'], 'password': kwargs['password'], 'is_session_manager': kwargs["is_session_manager"]}
    else:
        data = {'email': 'admin@user.com', 'password': 'admin_foo', 'is_session_manager': True}
    admin_user = get_user_model().objects.create_superuser(
        email=data["email"],
        password=data["password"],
        is_session_manager=data["is_session_manager"]
    )
    admin_user.raw_password = data["password"]
    return admin_user


def create_and_login_superuser(client, use_custom_data=False, **kwargs):
    user = create_superuser(use_custom_data=use_custom_data, **kwargs)
    client.login(email=user.email, password=user.raw_password)
    return user


def login_user(client, user):
    response = client.post(reverse("token_obtain_pair"),
                           data={"email": user.email,
                                 "password": user.raw_password})
    user_token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION="Bearer " + user_token)


def create_market_challenge_data(market_session_id, resource_id):
    return {
        "market_session": market_session_id,
        "resource": resource_id,
        "use_case": "wind_power"
    }


def create_market_historical_forecasts_data(resource_id, variable, forecasts,
                                            launch_time):
    return {
        "resource": resource_id,
        "launch_time": launch_time,
        "variable": variable,
        "forecasts": forecasts
    }


def create_market_submission_data(variable, forecasts):
    return {
        "variable": variable,
        "forecasts": forecasts
    }


def create_market_ensemble_data(variable, forecasts):
    return {
        "model": "GBR",
        "variable": variable,
        "forecasts": forecasts
    }


def create_raw_data(resource_id):
    raw_data_template = {
        "timeseries": [],
        "resource": resource_id,
        "units": "mw"
    }
    # Create 1month of historical data (sampled from uniform dist):
    # Generate datetime values for the challenge period:
    dt_now = pd.to_datetime(dt.datetime.utcnow()).round("15min")
    datetime_range = pd.date_range(start=dt_now - pd.DateOffset(days=31),
                                   end=dt_now,
                                   freq='15T')
    datetime_range = [x.strftime("%Y-%m-%dT%H:%M:%SZ") for x in datetime_range]
    # Generate random values for the "value" column
    values = np.random.uniform(low=0.0, high=1.0, size=len(datetime_range))
    values = [round(x, 3) for x in values]

    timeseries = [dict(zip(["datetime", "value"], x))
                  for x in zip(datetime_range, values)]
    raw_data_template["timeseries"] = timeseries
    return raw_data_template


def create_forecasts_submission_data(start_date, end_date):
    # Create 1month of historical data (sampled from uniform dist):
    # Generate datetime values for the challenge period:
    datetime_range = pd.date_range(start=start_date, end=end_date, freq='15T')
    datetime_range = [x.strftime("%Y-%m-%dT%H:%M:%SZ") for x in datetime_range]
    # Generate random values for the "value" column
    values = np.random.uniform(low=0.0, high=1.0, size=len(datetime_range))
    values = [round(x, 3) for x in values]
    # Forecasts data:
    timeseries = [dict(zip(["datetime", "value"], x))
                  for x in zip(datetime_range, values)]
    return timeseries

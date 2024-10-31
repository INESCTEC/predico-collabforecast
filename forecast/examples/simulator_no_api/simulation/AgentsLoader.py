import os
import json

import pandas as pd

from loguru import logger
from conf import settings


class AgentsLoader:
    """
    AgentsLoader Class responsible for:
    - Reading CSV data

    """
    def __init__(self, launch_time, market_session, data_path,
                delimiter=',', datetime_fmt="%Y-%m-%d %H:%M"):
        self.launch_time = launch_time
        self.market_session = market_session
        self.data_path = None
        self.buyers_resources = None
        self.sellers_resources = None
        self.buyers_users = None
        self.sellers_users = None
        self.users_forecasts = None
        self.measurements = {}
        self.forecasts = {}
        self.users_list = None
        self.resource_list = None
        self.measurements_list = None
        self.forecasts_list = None
        self.bids_per_resource = None
        self.data_path = data_path
        self.datetime_fmt = datetime_fmt
        self.delimiter = delimiter
        self.submissions = []

    def read_dataset(self, data_type: str):
        """
        Read CSV data. Drops duplicates based on datetime and initializes
        a 'self.dataset' class attribute containing the loaded timeseries

        :param data_type:
        :param sep:
        :return:
        """
        if data_type not in ["measurements", "forecasts"]:
            raise ValueError("data_type must be either "
                                "'measurements' or 'forecasts'")

        # dataset path:
        dataset_path = os.path.join(self.data_path, f"{data_type}.csv")
        if os.path.exists(dataset_path):
            dataset = pd.read_csv(dataset_path, sep=self.delimiter)
            dataset.drop_duplicates("datetime", inplace=True)
            dataset.loc[:, 'datetime'] = pd.to_datetime(
                dataset["datetime"],
                format=self.datetime_fmt).dt.tz_localize("UTC")
            dataset.set_index("datetime", inplace=True)
            dataset.dropna(how="all", inplace=True)
        else:
            logger.warning(f"File {dataset_path} not found. "
                            f"Creating empty {data_type} dataset.")
            dataset = pd.DataFrame()
        return dataset

    def load_user_resources(self):
        """
        Loads user and user resources metadata.
        Initializes 'self.resource_list' class attribute with this information.
        """
        # user buyer resources path for that dataset:
        buyers_res_path = os.path.join(self.data_path, "buyers_resources.json")
        with open(buyers_res_path, "r") as f:
            self.buyers_resources = json.load(f)

        # user sellers resources path for that dataset:
        sellers_res_path = os.path.join(self.data_path, "sellers_resources.json")
        with open(sellers_res_path, "r") as f:
            self.sellers_resources = json.load(f)

        self.buyers_users = [x["user"] for x in self.buyers_resources]
        self.sellers_users = [x["user"] for x in self.sellers_resources]
        self.measurements_list = [x["id"] for x in self.buyers_resources]

        if len(set(self.measurements_list)) != len(self.measurements_list):
            raise AttributeError("There are repeated resource id's in buyers_resources.json.")

        return self

    def load_measurements(self):
        self.measurements = {}
        end_date = self.launch_time.strftime("%Y-%m-%d %H:%M:%S.%f")
        dataset = self.read_dataset(data_type="measurements")

        if (pd.infer_freq(dataset.index) is None) or (pd.infer_freq(dataset.index) != settings.MARKET_DATA_TIME_RESOLUTION):  # noqa
            dataset = dataset.resample(settings.MARKET_DATA_TIME_RESOLUTION).interpolate()

        if dataset.empty:
            exit("Empty measurements dataset. Cannot continue.")

        # make sure we only load data until market launch (historical)
        _ts = dataset[:end_date].index

        for resource_id in self.measurements_list:
            _v = dataset.loc[:end_date, f"{resource_id}"].dropna()
            if _v.empty:
                raise ValueError(f"Resource {resource_id} has no data (hint: check measurements.csv)")
            _ts = _v.index
            _v = _v.values
            self.measurements[resource_id] = pd.DataFrame({
                "datetime": _ts,
                "value": _v,
            }).set_index("datetime")
        return self

    def load_forecasts(self):
        time_freq = settings.MARKET_DATA_TIME_RESOLUTION
        self.forecasts = dict([(x, {}) for x in self.sellers_users])
        end_date = (self.launch_time + pd.DateOffset(days=3)).strftime("%Y-%m-%d %H:%M:%S.%f")
        dataset = self.read_dataset(data_type="forecasts")

        for resource in self.sellers_resources:
            target_resource = resource["market_session_challenge_resource_id"]
            csv_colname = f"{resource['user']}_{resource['variable']}_{target_resource}"
            forecasts_df = dataset.loc[:end_date, csv_colname].dropna()
            forecasts_df = forecasts_df.resample(time_freq).interpolate()
            if forecasts_df.empty:
                _df = pd.DataFrame({
                    "datetime": [],
                    "value": [],
                }).set_index("datetime")
            else:
                _ts = forecasts_df.index
                _v = forecasts_df.values
                _df = pd.DataFrame({
                    "datetime": _ts,
                    "value": _v,
                }).set_index("datetime")

            if target_resource not in self.forecasts[resource["user"]]:
                self.forecasts[resource["user"]][target_resource] = {}
            self.forecasts[resource["user"]][target_resource][resource['variable']] = _df

        return self

    def load_challenge_measurements_data(self, resource_list, start_date, end_date):
        dataset = self.read_dataset(data_type="measurements")
        if (pd.infer_freq(dataset.index) is None) or (pd.infer_freq(dataset.index) != settings.MARKET_DATA_TIME_RESOLUTION):  # noqa
            dataset = dataset.resample(settings.MARKET_DATA_TIME_RESOLUTION).interpolate()

        if dataset.empty:
            exit("Empty measurements dataset. Cannot continue.")

        # make sure we only load data for the requested period:
        _ts = dataset[start_date:end_date].index

        measurements = {}
        for resource_id in resource_list:
            _v = dataset.loc[:end_date, f"{resource_id}"].dropna()
            if _v.empty:
                raise ValueError(f"Resource {resource_id} has no data (hint: check measurements.csv)")
            _ts = _v.index
            _v = _v.values
            measurements[resource_id] = pd.DataFrame({
                "datetime": _ts,
                "value": _v,
            }).set_index("datetime")
        return measurements

    def load_datasets(self):
        # Load user resources (metadata)
        self.load_user_resources()
        # Read measurements data and assign to each user resource
        self.load_measurements()
        # Load forecasts data and assign to each user resource
        self.load_forecasts()
        return self

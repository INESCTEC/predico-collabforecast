import os
import json
import pandas as pd
import datetime as dt

from copy import deepcopy
from loguru import logger


__ROOT_PATH__ = os.path.dirname(__file__)


class SimulatorManager:
    """
    SimulatorManager class responsible for:
    - Creating the sessions list
    - Creating the reports directory
    - Creating the logger
    - Creating the report templates
    """

    def __init__(self,
                 dataset_path,
                 nr_sessions,
                 first_lt_utc,
                 session_freq,
                 delimiter=",",
                 datetime_fmt="%Y-%m-%d %H:%M",
                 report_name_suffix=None
                 ):

        # Simulator params:
        self.nr_sessions = nr_sessions
        self.session_freq = session_freq
        self.DATASET_PATH = dataset_path
        self.DATASET_NAME = os.path.basename(self.DATASET_PATH)
        self.DATETIME_FMT = datetime_fmt
        self.DATA_DELIMITER = delimiter
        self.REPORT_NAME_SUFFIX = report_name_suffix
        self.buyers_resources = None
        self.sellers_resources = None

        # parse first launch time:
        self.first_lt_utc = dt.datetime.strptime(first_lt_utc, "%Y-%m-%dT%H:%M:%SZ") # noqa

        # Create auxiliary variables:
        self.__create_reports_dir()
        self.__create_logger()
        self.__create_sessions_list()
        self.__create_report_templates()

    def set_buyers_resources(self, buyers_resources):
        self.buyers_resources = buyers_resources

    def set_sellers_resources(self, sellers_resources):
        self.sellers_resources = sellers_resources

    def __create_reports_dir(self):
        current_time = dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        _d = os.path.dirname
        report_dirname = f"{current_time}"

        if self.REPORT_NAME_SUFFIX is not None:
            report_dirname = f"{report_dirname}_{self.REPORT_NAME_SUFFIX}"

        self.REPORTS_PATH = os.path.join(_d(_d(__file__)),
                                         "files", "reports",
                                         self.DATASET_NAME,
                                         report_dirname)
        os.makedirs(self.REPORTS_PATH, exist_ok=True)

    def __create_logger(self):
        # logger:
        format = "{time:YYYY-MM-DD HH:mm:ss} | {level:<5} | {message}"
        logger.add(os.path.join(self.REPORTS_PATH, "logfile.log"),
                   format=format,
                   level='INFO',
                   backtrace=True)
        logger.info("-" * 79)

    def __create_sessions_list(self):
        # Simulator params:
        nr_sessions = self.nr_sessions
        self.SESSIONS_LAUNCH_TIME = pd.date_range(
            start=self.first_lt_utc,
            end=self.first_lt_utc + pd.DateOffset(
                hours=self.session_freq * nr_sessions
            ),
            freq=f"{self.session_freq}H",
        )
        self.SESSIONS_LIST = [(i, lt) for i, lt in enumerate(self.SESSIONS_LAUNCH_TIME)][:-1]  # noqa

    def __create_report_templates(self):
        # Template for market report:
        self.market_session_report = dict([(k, {}) for k, _ in self.SESSIONS_LIST])

        # Expected columns for CSV reports:
        self.session_details_fields = ['session_id',
                                       'session_lt',
                                       'status',
                                       'launch_ts',
                                       'buyer_resources',
                                       'elapsed_time',
                                       'challenges']
        self.buyers_results_fields = ['session_id',
                                      'user_id',
                                      'resource_id']
        self.sellers_results_fields = ['session_id',
                                       'user_id',
                                       'resource_id',
                                       'has_to_receive']

    def add_session_reports(self,
                            session_id,
                            session_lt,
                            session_details,
                            session_buyers_results,
                            session_buyers_forecasts,
                            session_buyers_weights):
        # Session report template:
        sess_dict = {
            "session_details": [],
            "buyers_results": [],
            "buyers_forecasts": [],
            "buyers_weights": []
        }
        # Update Market dataframe with this session details:
        details_ = deepcopy(session_details)
        # Add session details to market report:
        details_["session_id"] = session_id
        details_["session_lt"] = session_lt
        details_["buyer_resources"] = [x["resource"] for x in details_["challenges"]]
        details_["buyer_resources"] = ','.join(details_["buyer_resources"])
        sess_dict["session_details"] = details_
        # Add buyers results to market report:
        sess_dict["buyers_results"] = list(session_buyers_results.values())
        # Add buyers forecasts:
        for k, v in session_buyers_forecasts.items():
            v_ = [{**d,
                   "session_id": session_id, "buyer_resource_id": k,
                   "f_model": v["model"]}
                  for d in v["forecasts"]]
            sess_dict["buyers_forecasts"] += v_

        for k, v in session_buyers_weights.items():
            v_ = {"session_id": session_id, "buyer_resource_id": k}
            for qt, w in v.items():
                v_[qt] = w
            sess_dict["buyers_weights"].append(v_)

        # Update market report with this session details:
        self.market_session_report[session_id] = sess_dict

    def save_reports(self, sess_elapsed_time):
        data_details = []
        data_buyers = []
        data_forecasts = []
        data_weights = []

        for session_id, session_data in self.market_session_report.items():
            if session_data == {}:
                # Skip empty sessions:
                continue
            # Session details:
            session_details = session_data["session_details"]
            session_details["elapsed_time"] = sess_elapsed_time
            data_details.append(session_details)
            # Buyers results:
            buyers_results = deepcopy(session_data["buyers_results"])
            buyers_results = [{**d, "session_id": session_id} for d in buyers_results]  # noqa
            data_buyers += buyers_results
            # Buyers forecasts:
            buyers_forecasts = deepcopy(session_data["buyers_forecasts"])
            data_forecasts += buyers_forecasts
            # Buyers weights:
            buyers_weights = deepcopy(session_data["buyers_weights"])
            data_weights += buyers_weights

        # to CSV:
        pd.DataFrame(data_details, columns=self.session_details_fields).to_csv(os.path.join(self.REPORTS_PATH, "market.csv"), index=False)  # noqa
        pd.DataFrame(data_buyers, columns=self.buyers_results_fields).to_csv(os.path.join(self.REPORTS_PATH, "buyers.csv"), index=False)   # noqa
        pd.DataFrame(data_forecasts).to_csv(os.path.join(self.REPORTS_PATH, "forecasts.csv"), index=False) # noqa
        pd.DataFrame(data_weights).to_csv(os.path.join(self.REPORTS_PATH, "weights.csv"), index=False) # noqa

        # Save buyer / seller resources:
        # Dump JSON for buyers resources:
        with open(os.path.join(self.REPORTS_PATH, "buyers_resources.json"), "w") as f:
            json.dump(self.buyers_resources, f, indent=4)

        # Dump JSON for sellers resources:
        with open(os.path.join(self.REPORTS_PATH, "sellers_resources.json"), "w") as f:
            json.dump(self.sellers_resources, f, indent=4)

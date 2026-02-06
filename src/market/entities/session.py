import datetime as dt

from dataclasses import dataclass
from ..helpers.class_helpers import ValidatorClass


@dataclass()
class SessionClass(ValidatorClass):
    status: str = None  # Session status
    session_id: int = None  # Session ID (unique)
    launch_ts: dt.datetime = None  # Session start timestamp (launch)
    finish_ts: dt.datetime = None  # Session end timestamp (finish)
    buyers_results: dict = None  # Session results by buyer
    buyers_forecasts: dict = None  # Session forecasts by buyer
    buyers_weights: dict = None  # Session forecasts by buyer
    status_list = ["open", "closed", "running", "finished"]
    challenges: list = None

    def set_initial_conditions(self):
        self.buyers_results = {}
        self.buyers_forecasts = {}
        self.buyers_weights = {}

    def validate_attributes(self):
        if self.session_id is None:
            raise ValueError("SessionClass identifier not defined.")

        # Validate parameters types:
        self.validate_attr_types()

    @property
    def details(self):
        return {
            "session_id": self.session_id,
            "status": self.status,
            "launch_ts": self.launch_ts.strftime("%Y-%m-%d %H:%M:%S"),
            "challenges": self.challenges,
        }

    def set_buyer_result(self, buyer_cls):
        self.buyers_results[buyer_cls.resource_id] = buyer_cls.details

    def set_buyer_forecasts(self, buyer_cls):
        """Store all strategy forecasts for a buyer.

        Uses all_forecasts_dict to include all strategy results.
        """
        self.buyers_forecasts[buyer_cls.resource_id] = buyer_cls.all_forecasts_dict

    def set_session_challenges(self, challenges):
        self.challenges = challenges

    def start_session(self):
        self.status = "running"

    def end_session(self):
        self.status = "finished"
        self.finish_ts = dt.datetime.utcnow()

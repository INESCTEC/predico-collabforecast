import uuid
import pandas as pd
import datetime as dt


class SessionGenerator:
    session_number = 1

    def __init__(self):
        self.session_id = None
        self.launch_time = None
        self.session_date = None
        self.status = None
        self.buyers_data = None
        self.challenges_data = None

    def create_session(self, session_id, launch_time, buyers_data):
        self.session_id = session_id
        self.launch_time = launch_time
        self.status = "running"
        self.buyers_data = buyers_data

    def create_session_challenges(self):
        challenges = []
        for buyer in self.buyers_data:
            local_launch_time = pd.Timestamp(self.launch_time, tz="utc").tz_convert(buyer["timezone"]).date()
            target_day = local_launch_time + dt.timedelta(days=1)
            # Set challenge forecast range (Day ahead - local time)
            f_start_ = dt.datetime.combine(target_day, dt.time(0, 0))
            f_end_ = dt.datetime.combine(target_day, dt.time(23, 45))
            # Locate dates in local time and then convert to UTC
            f_start_ = pd.Timestamp(f_start_, tz=buyer["timezone"])
            f_end_ = pd.Timestamp(f_end_, tz=buyer["timezone"])
            # Convert dates to utc:
            f_start_ = f_start_.tz_convert("UTC")
            f_end_ = f_end_.tz_convert("UTC")
            if buyer["use_case"] not in ["wind_power_ramp", "wind_power"]:
                raise AttributeError(f"Invalid use case for resource {buyer['id']} of buyer {buyer['user']}")
            challenges.append({
                "id": uuid.uuid4(),
                "user": buyer["user"],
                "resource": buyer["id"],
                "start_datetime": f_start_.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_datetime": f_end_.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "registered_at": self.launch_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated_at": self.launch_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "use_case": buyer["use_case"],
                "target_day": target_day.strftime("%Y-%m-%d"),
                "market_session": self.session_id,
                "submission_list": []
            })

        self.challenges_data = challenges
        return challenges

    def create_submissions_to_challenges(self, sellers_resources):
        for challenge in self.challenges_data:
            buyer_resource_id = challenge["resource"]
            # Get sellers resources with 'target' equal to buyer resource id
            sellers = [x for x in sellers_resources if x["market_session_challenge_resource_id"] == buyer_resource_id]
            # Create submissions for each seller resource
            for seller in sellers:
                challenge["submission_list"].append({
                    "id": uuid.uuid4(),
                    "market_session_challenge_id": challenge["id"],
                    "registered_at": self.launch_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "user_id": seller["user"]
                })

        return self.challenges_data

    @property
    def session_data(self):
        return {'close_ts': None,
                'finish_ts': None,
                'id': self.session_id,
                'launch_ts': None,
                'open_ts': None,
                'session_date': self.launch_time.date(),
                'status': self.status}

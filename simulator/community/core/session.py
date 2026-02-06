"""
Session Generator for creating mock market sessions.

This module provides the SessionGenerator class which creates:
- Market session metadata
- Day-ahead forecast challenges
- Seller submissions to challenges

Example:
    >>> from core import SessionGenerator
    >>> generator = SessionGenerator()
    >>> generator.create_session(
    ...     session_id=1,
    ...     launch_time=datetime(2023, 2, 15, 10, 30),
    ...     buyers_data=buyers_resources,
    ... )
    >>> generator.create_challenges()
    >>> generator.create_submissions(sellers_resources)
"""

from __future__ import annotations

import uuid
from datetime import datetime, time, timedelta
from typing import Any

import pandas as pd


# Valid use cases for challenges
VALID_USE_CASES = frozenset(
    [
        "wind_power",
        "wind_power_ramp",
        "solar_power",
        "load",
    ]
)


class SessionGenerator:
    """Creates mock market sessions and challenges.

    The SessionGenerator simulates the creation of market sessions by:
    1. Creating session metadata (ID, status, timestamps)
    2. Generating day-ahead forecast challenges for each buyer resource
    3. Creating seller submissions linking forecasters to challenges

    :Example:
        >>> generator = SessionGenerator()
        >>> generator.create_session(
        ...     session_id=1,
        ...     launch_time=datetime(2023, 2, 15, 10, 30),
        ...     buyers_data=buyers_resources,
        ... )
        >>> challenges = generator.create_challenges()
        >>> generator.create_submissions(sellers_resources)
        >>> session_data = generator.session_data
    """

    def __init__(self) -> None:
        """Initialize the session generator."""
        self._session_id: int | None = None
        self._launch_time: datetime | None = None
        self._status: str = "pending"
        self._buyers_data: list[dict[str, Any]] = []
        self._challenges: list[dict[str, Any]] = []

    @property
    def session_id(self) -> int | None:
        """Return the current session ID."""
        return self._session_id

    @property
    def launch_time(self) -> datetime | None:
        """Return the session launch time."""
        return self._launch_time

    @property
    def challenges(self) -> list[dict[str, Any]]:
        """Return the list of challenges for this session."""
        return self._challenges

    @property
    def session_data(self) -> dict[str, Any]:
        """Return session metadata as a dictionary.

        :return: Dictionary with session metadata including:
            - id: Session identifier
            - status: Current session status
            - session_date: Date of the session
            - launch_ts, open_ts, close_ts, finish_ts: Timestamp placeholders
        """
        return {
            "id": self._session_id,
            "status": self._status,
            "session_date": self._launch_time.date() if self._launch_time else None,
            "launch_ts": None,
            "open_ts": None,
            "close_ts": None,
            "finish_ts": None,
        }

    def create_session(
        self,
        session_id: int,
        launch_time: datetime,
        buyers_data: list[dict[str, Any]],
    ) -> "SessionGenerator":
        """Initialize a new market session.

        :param session_id: Unique session identifier
        :param launch_time: Session launch time (UTC)
        :param buyers_data: List of buyer resource dictionaries with keys:
            - user: Buyer user ID
            - id: Resource ID
            - timezone: Buyer's timezone (e.g., "Europe/Brussels")
            - use_case: Type of forecast (e.g., "wind_power")

        :return: Self for method chaining
        """
        self._session_id = session_id
        self._launch_time = launch_time
        self._status = "running"
        self._buyers_data = buyers_data
        self._challenges = []

        return self

    def create_challenges(self) -> list[dict[str, Any]]:
        """Create day-ahead forecast challenges for each buyer resource.

        Challenges are created for the day following the launch time,
        with forecast range from 00:00 to 23:45 in the buyer's local timezone.

        :return: List of challenge dictionaries

        :raises ValueError: If a buyer has an invalid use_case
        :raises RuntimeError: If create_session() was not called first
        """
        if self._launch_time is None:
            raise RuntimeError("Call create_session() before create_challenges()")

        challenges = []

        for buyer in self._buyers_data:
            # Validate use case
            use_case = buyer.get("use_case", "")
            if use_case not in VALID_USE_CASES:
                raise ValueError(
                    f"Invalid use_case '{use_case}' for resource {buyer['id']}. "
                    f"Valid options: {sorted(VALID_USE_CASES)}"
                )

            # Calculate target day in buyer's timezone
            buyer_tz = buyer.get("timezone", "UTC")
            local_launch = pd.Timestamp(self._launch_time, tz="UTC").tz_convert(
                buyer_tz
            )
            target_day = local_launch.date() + timedelta(days=1)

            # Set forecast range (00:00 to 23:45 local time)
            forecast_start = datetime.combine(target_day, time(0, 0))
            forecast_end = datetime.combine(target_day, time(23, 45))

            # Convert to UTC timestamps
            forecast_start_utc = pd.Timestamp(forecast_start, tz=buyer_tz).tz_convert(
                "UTC"
            )
            forecast_end_utc = pd.Timestamp(forecast_end, tz=buyer_tz).tz_convert("UTC")

            # Create challenge
            challenge = {
                "id": uuid.uuid4(),
                "user": buyer["user"],
                "resource": buyer["id"],
                "start_datetime": forecast_start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_datetime": forecast_end_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "registered_at": self._launch_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated_at": self._launch_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "use_case": use_case,
                "target_day": target_day.strftime("%Y-%m-%d"),
                "market_session": self._session_id,
                "submission_list": [],
            }
            challenges.append(challenge)

        self._challenges = challenges
        return challenges

    def create_submissions(
        self,
        sellers_resources: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Create seller submissions for each challenge.

        Links sellers to challenges based on their target resource ID.

        :param sellers_resources: List of seller resource dictionaries with keys:
            - user: Seller user ID
            - variable: Forecast variable (e.g., "q50", "q10", "q90")
            - market_session_challenge_resource_id: Target buyer resource ID

        :return: Updated list of challenges with submissions

        :raises RuntimeError: If create_challenges() was not called first
        """
        if not self._challenges:
            raise RuntimeError("Call create_challenges() before create_submissions()")

        for challenge in self._challenges:
            target_resource = challenge["resource"]

            # Find sellers targeting this resource
            matching_sellers = [
                s
                for s in sellers_resources
                if s.get("market_session_challenge_resource_id") == target_resource
            ]

            # Create submission for each matching seller
            for seller in matching_sellers:
                submission = {
                    "id": uuid.uuid4(),
                    "market_session_challenge_id": challenge["id"],
                    "registered_at": self._launch_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "user_id": seller["user"],
                    "variable": seller.get("variable"),
                }
                challenge["submission_list"].append(submission)

        return self._challenges

    def reset(self) -> None:
        """Reset the generator to create a new session."""
        self._session_id = None
        self._launch_time = None
        self._status = "pending"
        self._buyers_data = []
        self._challenges = []

import os
import pickle

from loguru import logger

from conf.settings import SESSIONS_DIR


def store_session_datasets(
    session_id,
    buyer_measurements,
    sellers_forecasts,
    challenges_data,
    sellers_resources,
):
    # Create session dir if does not exist:
    os.makedirs(os.path.join(SESSIONS_DIR, str(session_id)), exist_ok=True)

    # Store session datasets to pickle
    session_datasets = {
        "session_id": str(session_id),
        "buyer_measurements": buyer_measurements,
        "sellers_forecasts": sellers_forecasts,
        "challenges_data": challenges_data,
        "sellers_resources": sellers_resources,
    }
    # Store session datasets to pickle
    file_path = os.path.join(SESSIONS_DIR, str(session_id), "session_datasets.pkl")
    with open(file_path, "wb") as f:
        pickle.dump(session_datasets, f)

    logger.success(f"Session datasets stored successfully.\n > Location = {file_path}.")

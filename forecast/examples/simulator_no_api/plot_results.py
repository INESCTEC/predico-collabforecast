import os
import json
import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt

sns.set_style("whitegrid")


def load_json(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    return data


# Load the results
DATASET = "example_elia"
QUANTILES = ["q10", "q50", "q90"]
FORECASTING_MODEL = "LR"
FILES_DT_FORMAT = "%Y-%m-%d %H:%M"
SIMULATION_REPORT_ID = "20240626095233_test"
report_dirs = os.listdir(os.path.join("files", "reports", DATASET))
# Load buyers and sellers resources:
buyers_resources_path = os.path.join("files", "datasets", DATASET, "buyers_resources.json")
sellers_resources_path = os.path.join("files", "datasets", DATASET, "sellers_resources.json")
buyers_resources = load_json(buyers_resources_path)
sellers_resources = load_json(sellers_resources_path)
# Load measurements data:
measurements_path = os.path.join("files", "datasets", DATASET, "measurements.csv")
measurements = pd.read_csv(measurements_path)
measurements["datetime"] = pd.to_datetime(measurements["datetime"], format=FILES_DT_FORMAT)
# Load forecasters data:
forecasters_path = os.path.join("files", "datasets", DATASET, "forecasts.csv")
forecasters = pd.read_csv(forecasters_path)
forecasters["datetime"] = pd.to_datetime(forecasters["datetime"], format=FILES_DT_FORMAT)
ensemble = pd.DataFrame()

# load report data:
forecast_path = os.path.join("files", "reports", DATASET, SIMULATION_REPORT_ID, "forecasts.csv")
ensemble_ = pd.read_csv(forecast_path)
ensemble = pd.concat([ensemble, ensemble_], axis=0)

# Reformat dataframe:
ensemble["datetime"] = pd.to_datetime(ensemble["datetime"], format="%Y-%m-%dT%H:%M:%SZ")
unique_buyer_ids = ensemble["buyer_resource_id"].unique()
unique_datetimes = ensemble["datetime"].unique()

ensemble_final = pd.DataFrame(index=unique_datetimes)
for buyer_id in unique_buyer_ids:
    for quantile in QUANTILES:
        ensemble_buyer = ensemble.loc[ensemble["buyer_resource_id"] == buyer_id, :]
        ensemble_buyer = ensemble_buyer.loc[ensemble_buyer["variable"] == quantile, :]
        ensemble_buyer = ensemble_buyer.loc[ensemble_buyer["f_model"] == FORECASTING_MODEL, :]
        ensemble_buyer = ensemble_buyer.drop(columns=["buyer_resource_id", "variable"])
        ensemble_buyer = ensemble_buyer.set_index("datetime")
        ensemble_buyer.drop(["session_id", "f_model"], axis=1, inplace=True)
        ensemble_buyer.rename(columns={"value": f"ensemble_{quantile}_{buyer_id}"}, inplace=True)
        ensemble_final = ensemble_final.join(ensemble_buyer)

for buyer_id in unique_buyer_ids:
    buyer_resource_info = [x for x in buyers_resources if x["id"] == buyer_id]
    sellers_resource_info = [x for x in sellers_resources if x["market_session_challenge_resource_id"] == buyer_id]
    sellers_features = [f"{x['user']}_{x['variable']}_{x['market_session_challenge_resource_id']}" for x in sellers_resource_info]
    if len(buyer_resource_info) > 1:
        raise ValueError("Detected more than one resource with the same ID in buyers_resources.json.")

    buyer_use_case = buyer_resource_info[0]["use_case"]
    forecasters_cols = ["datetime"] + sellers_features
    ensemble_cols = [x for x in ensemble_final.columns if x.endswith(buyer_id)]
    measurements_cols = ["datetime"] + [x for x in measurements.columns if x.endswith(buyer_id)]

    ind_forecasts = forecasters.loc[:, forecasters_cols].copy()
    observed = measurements.loc[:, measurements_cols].copy()
    ensemble = ensemble_final.loc[:, ensemble_cols].copy()

    # Set index to datetime:
    ind_forecasts.set_index("datetime", inplace=True)
    observed.set_index("datetime", inplace=True)

    # Reindex to expect datetime index
    ind_forecasts = ind_forecasts.reindex(ensemble.index)
    observed = observed.reindex(ensemble.index)

    # If buyer use case is "wind_power_ramp" - differenciate:
    observed_raw = observed.copy()
    if buyer_use_case == "wind_power_ramp":
        observed = observed.diff()

    fig, ax = plt.subplots(2, 1, figsize=(18, 8))
    ax[0].set_title(f"Buyer {buyer_id}")
    # first subplot:
    ind_forecasts.plot(ax=ax[0])
    observed_raw.plot(ax=ax[0], color="black", linewidth=2)
    # second subplot:
    ensemble.plot(ax=ax[1])
    observed.plot(ax=ax[1], color="black", linewidth=2)
    # axis:
    ax[0].set_ylabel("Avg. Power")
    ax[1].set_ylabel("Avg. Power")
    plt.tight_layout()
    plt.show()

import numpy as np
import pandas as pd


np.random.seed(13)


def generate_measurements(
    start_date, end_date, scale_factor=1, freq="H", outliers=False
):
    _st = start_date.replace(second=0, microsecond=0)
    _et = end_date.replace(second=0, microsecond=0)
    _ts = pd.date_range(_st, _et, freq=freq, tz="utc")
    _v = np.random.uniform(low=0, high=1, size=len(_ts)) * scale_factor
    measurements = pd.DataFrame(
        {
            "datetime": _ts,
            "value": _v,
            "variable": ["measurements"] * len(_ts),
            "units": ["w"] * len(_ts),
        }
    )
    return measurements


class MeasurementsGenerator:
    def __init__(self):
        self.mock_dataset = pd.DataFrame()

    def load_from_csv(self, path):
        self.mock_dataset = pd.read_csv(path, sep=";")
        self.mock_dataset.loc[:, "datetime"] = pd.to_datetime(
            self.mock_dataset["datetime"], format="%Y-%m-%d %H:%M"
        ).dt.tz_localize("UTC")
        self.mock_dataset.set_index("datetime", inplace=True)

    @staticmethod
    def __add_season(data):
        _n_cicles = np.random.randint(3)
        return data + np.sin(_n_cicles * np.pi * np.arange(len(data)) / len(data))

    @staticmethod
    def __add_noise(data):
        _noise_mult = np.random.uniform(0.05, 0.7)
        _sigma = data.std() * _noise_mult
        return data + np.random.normal(0, _sigma, size=(len(data),))

    @staticmethod
    def __wave_generator(amplitude, n_samples, freq):
        _24h_sin = amplitude * np.sin(freq * np.pi * np.arange(24) / 24)
        return np.append(
            np.tile(_24h_sin, n_samples // 24), _24h_sin[: (n_samples % 24)]
        )

    @staticmethod
    def __add_nan(data):
        _time = np.arange(len(data))
        _pct_nans = np.random.uniform(0.01, 0.1)
        _number_of_nans = int(np.ceil(_pct_nans * len(data)))
        _nan_idx = np.random.choice(_time, size=_number_of_nans)
        data[_nan_idx] = np.nan
        return data

    def sin_harmonics_generator(self, n_obs):
        # Data sample configs:
        n_harmonics_ = np.random.randint(1, 5)
        base_wave = self.__wave_generator(1, n_obs, 3)
        for _ in range(n_harmonics_):
            _freq = np.random.randint(5)
            _amp = np.random.randint(5)
            harmonic_wave = self.__wave_generator(_amp, n_obs, _freq)
            base_wave += harmonic_wave
        if bool(np.random.choice(2, 1, p=[0.2, 0.8])[0]):
            base_wave = self.__add_noise(base_wave)
        if bool(np.random.choice(2, 1, p=[0.3, 0.7])[0]):
            base_wave = self.__add_season(base_wave)
        if bool(np.random.choice(2, 1, p=[0.1, 0.9])[0]):
            base_wave = self.__add_nan(base_wave)
        return base_wave

    @staticmethod
    def var_lasso_generator(n_agents, n_obs):
        n_obs_var = n_obs + 2000  # add 2000 values for var warmup
        from .var_lasso_funcs import random_coef_VAR

        ###########################################
        # COLUNAS PAGAM A LINHAS! (J PAGA A I)
        ###########################################
        # Simulate data from a VAR with n_agents, 1lag
        coefs_var = random_coef_VAR(n_lags=1, n_agents=n_agents)
        sim_measurements = np.zeros((n_obs_var, n_agents))
        # the first "lags" rows are randomly defined as well as the intercepts
        intercepts_ = np.random.normal(1000, 100, (1, n_agents))
        sim_measurements[0, :] = np.random.normal(0, 1, (1, n_agents))
        # then a VAR process is used to simulate the next observations
        for idx in range(1, n_obs_var):
            sim_measurements[idx, :] = (
                intercepts_
                + np.matmul(sim_measurements[idx - 1, :].flatten(order="A"), coefs_var)
                + np.random.normal(0, 50, (1, n_agents))
            )
        # Remove var warmup period:
        sim_measurements = sim_measurements[2000:, :]
        # Calculate standardized var coefficients:
        std_dict = pd.DataFrame(sim_measurements).std().to_dict()
        std_coefs = np.zeros(shape=coefs_var.shape)
        for i in range(coefs_var.shape[0]):
            mult_ = std_dict[i]
            for j in range(coefs_var.shape[1]):
                if i == j:
                    continue
                denom_ = std_dict[j]
                std_coefs[i, j] = (coefs_var[i, j] * mult_) / denom_
        # Create dict showing how much each buyer should receive from
        # each seller
        abs_std_coefs = np.abs(std_coefs)
        revenue_dict = {}
        for j in range(abs_std_coefs.shape[1]):
            # remove diag coef. (case where agent sells to himself)
            coefs_sum_ = np.delete(abs_std_coefs[:, j], j).sum()
            norm_coefs_ = abs_std_coefs[:, j] / coefs_sum_
            revenue_dict[j] = dict(
                [(k, v) for k, v in enumerate(norm_coefs_) if k != j]
            )
            revenue_dict[j][j] = 0.0
        return sim_measurements, revenue_dict

    def generate_mock_data_var_lasso(self, n_agents, start_date, end_date):
        start_date = start_date.replace(microsecond=0, second=0, minute=0)
        end_date = end_date.replace(microsecond=0, second=0, minute=0)
        _st = start_date.strftime("%Y-%m-%d %H:%M:%S")
        _et = end_date.strftime("%Y-%m-%d %H:%M:%S")
        _ts = pd.date_range(_st, _et, freq="H", tz="utc")

        agent_values = []
        values, revenue_coefs = self.var_lasso_generator(
            n_agents=n_agents, n_obs=len(_ts)
        )
        for agent in range(n_agents):
            agent_values.append(
                pd.DataFrame(
                    {
                        "datetime": _ts,
                        "value": values[:, agent],
                        "variable": ["measurements"] * len(_ts),
                    }
                )
            )
        return agent_values, revenue_coefs

    def generate_mock_data_sin(self, start_date, end_date):
        _st = start_date.strftime("%Y-%m-%d %H:%M:%S")
        _et = end_date.strftime("%Y-%m-%d %H:%M:%S")
        _ts = pd.date_range(_st, _et, freq="h", tz="utc")
        # Data sample configs:
        n_harmonics_ = np.random.randint(1, 5)
        base_wave = self.__wave_generator(1, len(_ts), 3)
        for _ in range(n_harmonics_):
            _freq = np.random.randint(5)
            _amp = np.random.randint(5)
            harmonic_wave = self.__wave_generator(_amp, len(_ts), _freq)
            base_wave += harmonic_wave
        if bool(np.random.choice(2, 1, p=[0.2, 0.8])[0]):
            base_wave = self.__add_noise(base_wave)
        if bool(np.random.choice(2, 1, p=[0.3, 0.7])[0]):
            base_wave = self.__add_season(base_wave)
        if bool(np.random.choice(2, 1, p=[0.1, 0.9])[0]):
            base_wave = self.__add_nan(base_wave)

        return pd.DataFrame(
            {
                "datetime": _ts,
                "value": base_wave,
                "variable": ["measurements"] * len(_ts),
            }
        )

    def get_measurements(self, agent_id, end_date):
        _ts = self.mock_dataset[:end_date].index
        _v = self.mock_dataset.loc[:end_date, f"A{agent_id}"].values
        measurements = pd.DataFrame(
            {
                "datetime": _ts,
                "value": _v,
                "variable": ["measurements"] * len(_ts),
            }
        )
        return measurements

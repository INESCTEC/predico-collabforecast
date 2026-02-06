"""Lag feature generation utilities."""

import pandas as pd


def create_lag_features(
    df: pd.DataFrame,
    max_lags: int = 2,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """
    Create lagged features for time series data.

    Generates lag features for the specified columns, creating columns
    named `{original_col}_t-1`, `{original_col}_t-2`, etc.

    :param df: Input DataFrame with datetime index
    :param max_lags: Number of lag periods (1, 2, ..., max_lags)
    :param columns: Columns to create lags for (default: all numeric columns)
    :return: DataFrame with lag features only (not original columns)

    Example::

        >>> df = pd.DataFrame({'a': [1, 2, 3, 4]}, index=pd.date_range('2024-01-01', periods=4, freq='h'))
        >>> lags = create_lag_features(df, max_lags=2)
        >>> df_augmented = pd.concat([df, lags], axis=1)
    """
    if df.empty:
        return pd.DataFrame(index=df.index)

    if columns is None:
        columns = df.select_dtypes(include="number").columns.tolist()

    if not columns:
        return pd.DataFrame(index=df.index)

    lag_features = {}

    for col in columns:
        if col not in df.columns:
            continue
        for lag in range(1, max_lags + 1):
            lag_features[f"{col}_t-{lag}"] = df[col].shift(lag)

    return pd.DataFrame(lag_features, index=df.index)

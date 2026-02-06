"""Rolling window statistics utilities."""

import pandas as pd


def create_rolling_features(
    df: pd.DataFrame,
    window: int = 2,
    stats: list[str] | None = None,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """
    Create rolling window statistics.

    Generates rolling statistics for the specified columns, creating columns
    named `{original_col}_{stat}` (e.g., 'price_avg', 'price_std').

    :param df: Input DataFrame with datetime index
    :param window: Rolling window size (number of periods)
    :param stats: Statistics to compute. Options: "mean", "std", "var", "min", "max".
                 Default: ["mean", "std"]
    :param columns: Columns to transform (default: all numeric columns)
    :return: DataFrame with rolling features only (not original columns)

    Example::

        >>> df = pd.DataFrame({'a': [1, 2, 3, 4, 5]}, index=pd.date_range('2024-01-01', periods=5, freq='h'))
        >>> rolling = create_rolling_features(df, window=2, stats=['mean', 'std'])
        >>> # Returns DataFrame with 'a_avg', 'a_std' columns
    """
    if df.empty:
        return pd.DataFrame(index=df.index)

    if stats is None:
        stats = ["mean", "std"]

    if columns is None:
        columns = df.select_dtypes(include="number").columns.tolist()

    if not columns:
        return pd.DataFrame(index=df.index)

    # Mapping of stat name to suffix and aggregation function
    stat_config = {
        "mean": ("avg", "mean"),
        "std": ("std", "std"),
        "var": ("var", "var"),
        "min": ("min", "min"),
        "max": ("max", "max"),
    }

    rolling_features = {}

    for col in columns:
        if col not in df.columns:
            continue
        rolling = df[col].rolling(window=window, min_periods=1)
        for stat in stats:
            if stat not in stat_config:
                continue
            suffix, agg_func = stat_config[stat]
            rolling_features[f"{col}_{suffix}"] = getattr(rolling, agg_func)()

    return pd.DataFrame(rolling_features, index=df.index)

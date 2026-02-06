"""Differencing feature generation utilities."""

import pandas as pd


def create_difference_features(
    df: pd.DataFrame,
    order: int = 1,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """
    Create differenced features.

    Generates difference features for the specified columns, creating columns
    named `{original_col}_diff` (first order) or `{original_col}_diff{order}` (higher orders).

    :param df: Input DataFrame with datetime index
    :param order: Differencing order (1 = first difference, 2 = second difference)
    :param columns: Columns to difference (default: all numeric columns)
    :return: DataFrame with difference features only (not original columns)

    Example::

        >>> df = pd.DataFrame({'a': [1, 3, 6, 10]}, index=pd.date_range('2024-01-01', periods=4, freq='h'))
        >>> diff = create_difference_features(df, order=1)
        >>> # Returns DataFrame with 'a_diff' column: [NaN, 2, 3, 4]
    """
    if df.empty:
        return pd.DataFrame(index=df.index)

    if columns is None:
        columns = df.select_dtypes(include="number").columns.tolist()

    if not columns:
        return pd.DataFrame(index=df.index)

    diff_features = {}

    for col in columns:
        if col not in df.columns:
            continue

        # Compute successive differences (diff of diff of diff...)
        current_diff = df[col]
        for o in range(1, order + 1):
            current_diff = current_diff.diff()
            suffix = "diff" if o == 1 else f"diff{o}"
            diff_features[f"{col}_{suffix}"] = current_diff

    return pd.DataFrame(diff_features, index=df.index)

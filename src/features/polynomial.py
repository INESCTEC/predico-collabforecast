"""Polynomial feature generation utilities."""

import pandas as pd


def create_polynomial_features(
    df: pd.DataFrame,
    degree: int = 2,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """
    Create polynomial features (squared, cubic, etc.).

    Generates polynomial transformations for the specified columns, creating
    columns named `{original_col}_sqr` (degree 2), `{original_col}_cub` (degree 3), etc.

    :param df: Input DataFrame
    :param degree: Maximum polynomial degree (2 = squared only, 3 = squared + cubic)
    :param columns: Columns to transform (default: all numeric columns)
    :return: DataFrame with polynomial features only (not original columns)

    Example::

        >>> df = pd.DataFrame({'a': [1, 2, 3, 4]})
        >>> poly = create_polynomial_features(df, degree=2)
        >>> # Returns DataFrame with 'a_sqr' column
    """
    if df.empty:
        return pd.DataFrame(index=df.index)

    if columns is None:
        columns = df.select_dtypes(include="number").columns.tolist()

    if not columns:
        return pd.DataFrame(index=df.index)

    # Mapping of degree to suffix
    degree_suffix = {
        2: "sqr",
        3: "cub",
        4: "pow4",
        5: "pow5",
    }

    poly_features = {}

    for col in columns:
        if col not in df.columns:
            continue
        for d in range(2, degree + 1):
            suffix = degree_suffix.get(d, f"pow{d}")
            poly_features[f"{col}_{suffix}"] = df[col] ** d

    return pd.DataFrame(poly_features, index=df.index)

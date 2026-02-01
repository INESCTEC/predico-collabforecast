from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_predict


def linear_regression_pipe(**kwargs):
    # Define the steps for the pipeline
    steps = [
        ('scaler', StandardScaler()),  # Standardize data
        ('regressor', LinearRegression(fit_intercept=True))  # Train model
    ]
    # Create the pipeline
    pipeline = Pipeline(steps)
    return pipeline


def recent_hours_forecast(X, y, n_hours, f_pipeline):
    # Todo: prepare function for cases where there are no sufficient hours
    #  for the train / validation set
    # Train/test split and focus on recent hours performance (validation set)
    X_train = X[0:(X.shape[0] - n_hours - 1), :]
    X_val = X[(X.shape[0] - n_hours):, :]
    y_train = y[0:(X.shape[0] - n_hours - 1), :]
    y_val = y[(X.shape[0] - n_hours):, :]
    # Generate forecasts:
    forecasts = f_pipeline.fit(X_train, y_train).predict(X_val)
    return forecasts, y_val


def cv_forecast(X, y, f_pipeline):
    # Define the number of folds
    nr_samples_per_fold = 400   # Minimum number of samples per fold
    min_n_folds, max_n_folds = (2, 12)
    # Adjust number of folds based on the number of samples
    for cv in range(min_n_folds, max_n_folds + 1):
        if X.shape[0] <= cv * nr_samples_per_fold:
            break
    else:
        # If the loop completes without breaking, set cv to max_n_folds
        cv = max_n_folds
    # Run the forecast pipeline in a cross-validation setting
    forecasts = cross_val_predict(f_pipeline, X, y, cv=cv)
    return forecasts, y

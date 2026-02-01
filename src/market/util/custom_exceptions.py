class CustomExceptions(BaseException):
    pass


class NoMarketDataException(CustomExceptions):
    pass


class NoMarketBuyersExceptions(CustomExceptions):
    pass


class NoMarketUsersExceptions(CustomExceptions):
    pass


class FeatureEngException(CustomExceptions):
    pass


class ModelTrainException(CustomExceptions):
    pass


class ModelFitException(CustomExceptions):
    pass


class ModelLoadException(CustomExceptions):
    pass


class MissingInputsException(CustomExceptions):
    pass


class ModelUpdateException(CustomExceptions):
    pass


class ModelForecastException(CustomExceptions):
    pass


class TrainEmptyDatasetError(CustomExceptions):
    pass


class UpdateEmptyDatasetError(CustomExceptions):
    pass


class TrainScalerError(CustomExceptions):
    pass


class UpdateScalerError(CustomExceptions):
    pass


class LoadScalerError(CustomExceptions):
    pass


class ForecastError(CustomExceptions):
    pass


class ForecastAuxError(CustomExceptions):
    pass


class ModelClassNonExistantMethod(CustomExceptions):
    pass

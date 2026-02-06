"""
Strategy registry for forecast strategies.

This module provides the StrategyRegistry class for registering and
retrieving forecast strategies. Strategies are registered using a
decorator pattern, allowing contributors to add new strategies without
modifying core code.

Example usage::

    from src.strategies import StrategyRegistry

    # Register a strategy using decorator
    @StrategyRegistry.register("my_strategy")
    class MyStrategy:
        ...

    # Get a registered strategy
    strategy = StrategyRegistry.get("my_strategy")

    # List all registered strategies
    available = StrategyRegistry.list_strategies()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from ...core.exceptions import StrategyNotFoundError

if TYPE_CHECKING:
    from ...core.interfaces import ForecastStrategy


class StrategyRegistry:
    """
    Registry for forecast strategies.

    This class maintains a mapping of strategy names to strategy classes.
    Strategies are registered using the :meth:`register` decorator and
    retrieved using the :meth:`get` method.

    The registry is implemented as a class with class methods, allowing
    global access without instantiation.

    Example::

        @StrategyRegistry.register("weighted_avg")
        class WeightedAverageStrategy:
            ...

        # Later, retrieve and instantiate
        strategy = StrategyRegistry.get("weighted_avg", beta=0.001)
    """

    _strategies: dict[str, type["ForecastStrategy"]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type], type]:
        """
        Decorator to register a strategy class.

        :param name: Unique name for the strategy. Should be lowercase
            with underscores (e.g., "weighted_avg", "stacked_lr").

        :return: Decorator function that registers the class

        :raises ValueError: If a strategy with the same name is already registered

        Example::

            @StrategyRegistry.register("my_ensemble")
            class MyEnsembleStrategy:
                @property
                def name(self) -> str:
                    return "my_ensemble"
                ...
        """

        def decorator(
            strategy_cls: type["ForecastStrategy"],
        ) -> type["ForecastStrategy"]:
            if name in cls._strategies:
                raise ValueError(
                    f"Strategy '{name}' is already registered. "
                    f"Use a different name or unregister the existing strategy first."
                )
            cls._strategies[name] = strategy_cls
            return strategy_cls

        return decorator

    @classmethod
    def get(cls, name: str, **kwargs: Any) -> "ForecastStrategy":
        """
        Get an instance of a registered strategy.

        :param name: Name of the strategy to retrieve
        :param kwargs: Arguments to pass to the strategy constructor

        :return: Instance of the requested strategy

        :raises StrategyNotFoundError: If no strategy with the given name is registered

        Example::

            strategy = StrategyRegistry.get("weighted_avg", beta=0.001)
            strategy.fit(X_train, y_train, quantiles)
        """
        if name not in cls._strategies:
            available = ", ".join(cls._strategies.keys()) or "none"
            raise StrategyNotFoundError(
                f"Strategy '{name}' not found. Available strategies: {available}",
                {"requested": name, "available": list(cls._strategies.keys())},
            )
        return cls._strategies[name](**kwargs)

    @classmethod
    def list_strategies(cls) -> list[str]:
        """
        List all registered strategy names.

        :return: List of registered strategy names
        """
        return list(cls._strategies.keys())

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Remove a strategy from the registry.

        :param name: Name of the strategy to remove

        :raises StrategyNotFoundError: If no strategy with the given name is registered
        """
        if name not in cls._strategies:
            raise StrategyNotFoundError(
                f"Cannot unregister: strategy '{name}' not found.",
                {"requested": name},
            )
        del cls._strategies[name]

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if a strategy is registered.

        :param name: Name of the strategy to check

        :return: True if the strategy is registered, False otherwise
        """
        return name in cls._strategies

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered strategies.

        This is primarily useful for testing.
        """
        cls._strategies.clear()

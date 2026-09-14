"""Provider interfaces for FactorLab market data.

Providers return data in the canonical schema defined by
``qbot.research.data.schema``.  Network- and vendor-specific details must not
leak into factor, label, or dataset code.
"""

from abc import ABC, abstractmethod
from typing import Optional, Union

import pandas as pd


DateLike = Union[str, pd.Timestamp]


class MarketDataProvider(ABC):
    """Uniform interface implemented by all FactorLab market-data vendors."""

    @abstractmethod
    def get_daily_bars(
        self, symbol: str, start: DateLike, end: DateLike
    ) -> pd.DataFrame:
        """Return canonical daily stock bars for the inclusive date range."""

    @abstractmethod
    def get_index_bars(
        self, symbol: str, start: DateLike, end: DateLike
    ) -> pd.DataFrame:
        """Return canonical daily index bars for the inclusive date range."""

    @abstractmethod
    def get_trade_calendar(
        self, start: DateLike, end: DateLike
    ) -> pd.DatetimeIndex:
        """Return benchmark trading sessions for the inclusive date range."""

    @abstractmethod
    def get_index_constituents(
        self, symbol: str, as_of: Optional[DateLike] = None
    ) -> pd.DataFrame:
        """Return a constituent snapshot when the provider supports it.

        A provider that only exposes the current snapshot must reject a
        historical ``as_of`` value.  It must never silently substitute current
        members for a point-in-time request.
        """

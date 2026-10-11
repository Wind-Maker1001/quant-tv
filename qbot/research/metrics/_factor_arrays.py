"""Single-call numeric workspaces; public contracts remain in factor.py.

Only ordinary float64 factors/labels and nonmissing string symbols use this
path. Other accepted public inputs keep the original Pandas implementation.
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import rankdata


def _pearson_finite(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 2 or np.all(left == left[0]) or np.all(right == right[0]):
        return float("nan")
    # This is also the numerical kernel used by pandas.Series.corr.
    return float(np.corrcoef(left, right)[0, 1])


def _rank_finite(
    left: np.ndarray, right: np.ndarray, right_ranks: Optional[np.ndarray] = None
) -> float:
    if len(left) < 2 or np.all(left == left[0]) or np.all(right == right[0]):
        return float("nan")
    if right_ranks is None:
        right_ranks = rankdata(right, method="average")
    ranked = np.column_stack((rankdata(left, method="average"), right_ranks))
    # Same orientation and coefficient as scipy.stats.spearmanr, without its
    # unused p-value calculation. Ranks are computed AFTER pairwise filtering.
    return float(np.corrcoef(ranked, rowvar=False)[1, 0])


class _PreparedFactors:
    def __init__(self, frame: pd.DataFrame, factors: List[str], target: str) -> None:
        self.frame = frame
        self.factors = factors
        self.values = frame[factors].to_numpy(copy=False)
        self.target = frame[target].to_numpy(copy=False)
        self.finite = np.isfinite(self.values)
        self.target_finite = np.isfinite(self.target)
        self.symbols = frame["symbol"].to_numpy(copy=False)
        self.days = []
        self.by_date = {}
        # GroupBy preserves original row order inside each date. A contiguous
        # date can use a view; unsorted callers retain their positional indices.
        for date, positions in frame.groupby("date", sort=True).indices.items():
            indexer = positions
            if len(positions) and positions[-1] - positions[0] == len(positions) - 1:
                indexer = slice(int(positions[0]), int(positions[-1]) + 1)
            self.days.append((date, indexer))
            self.by_date[date] = indexer

    @classmethod
    def create(cls, frame: pd.DataFrame, factors: List[str], target: str):
        if not factors or len(set(factors)) != len(factors):
            return None
        if set(factors).intersection(("date", "symbol", target)) or frame.columns.has_duplicates:
            return None
        for name in factors + [target]:
            if not isinstance(frame[name].dtype, np.dtype) or frame[name].dtype != np.dtype("float64"):
                return None
        if not all(isinstance(value, str) for value in frame["symbol"].unique()):
            return None
        return cls(frame, factors, target)

    def daily_ic(self, minimum_cross_section: int, scope: str) -> pd.DataFrame:
        rows = []
        for date, indexer in self.days:
            values = self.values[indexer]
            target = self.target[indexer]
            finite = self.finite[indexer]
            target_finite = self.target_finite[indexer]
            target_ranks: Dict[bytes, np.ndarray] = {}
            for number, factor in enumerate(self.factors):
                valid = finite[:, number] & target_finite
                count = int(valid.sum())
                pearson = rank_ic = float("nan")
                if count >= minimum_cross_section:
                    left, right = values[valid, number], target[valid]
                    pearson = _pearson_finite(left, right)
                    key = valid.tobytes()
                    if key not in target_ranks:
                        target_ranks[key] = rankdata(right, method="average")
                    rank_ic = _rank_finite(left, right, target_ranks[key])
                rows.append({"scope": scope, "date": date, "factor": factor,
                             "observations": count, "coverage": count / float(len(values)),
                             "IC": pearson, "RankIC": rank_ic})
        return pd.DataFrame(rows)

    def autocorrelation(self, minimum_cross_section: int, scope: str, dates: pd.DatetimeIndex) -> pd.DataFrame:
        # One key alignment per adjacent session, rather than one merge per
        # factor. get_indexer preserves the current (left merge) row order.
        by_factor = [[] for _ in self.factors]
        previous = None
        for date in dates:
            indexer = self.by_date.get(date, slice(0, 0))
            symbols = self.symbols[indexer]
            values = self.values[indexer]
            if previous is not None:
                previous_symbols, previous_values = previous
                matches = pd.Index(previous_symbols).get_indexer(symbols)
                found = matches >= 0
                current = values[found]
                earlier = previous_values[matches[found]]
                for number, factor in enumerate(self.factors):
                    left, right = current[:, number], earlier[:, number]
                    # The legacy observation count removes NaN BEFORE testing
                    # the threshold; infinities still count here. Its correlation
                    # helper then removes infinities and requires at least two.
                    not_missing = ~np.isnan(left) & ~np.isnan(right)
                    count = int(not_missing.sum())
                    value = float("nan")
                    if count >= minimum_cross_section:
                        finite = np.isfinite(left) & np.isfinite(right)
                        value = _rank_finite(left[finite], right[finite])
                    by_factor[number].append({"scope": scope, "date": date, "factor": factor,
                                               "autocorrelation": value, "observations": count})
            previous = symbols, values
        return pd.DataFrame([row for rows in by_factor for row in rows])

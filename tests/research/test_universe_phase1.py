"""Offline contracts for the CSI500 point-in-time universe and filters."""

import pandas as pd
import pytest

from qbot.research.errors import PointInTimeUniverseError
from qbot.research.universe.csi500 import (
    DataFramePointInTimeUniverse,
    canonical_symbol,
    compress_membership_intervals,
    validate_daily_membership,
)
from qbot.research.universe.filters import (
    UniverseFilterConfig,
    apply_universe_filters,
    build_filter_flags,
)


def _membership(dates, members_by_date):
    rows = []
    for date, symbols in zip(dates, members_by_date):
        rows.extend(
            {"date": date, "symbol": symbol, "is_member": True}
            for symbol in symbols
        )
    return pd.DataFrame(rows)


def test_canonical_symbol_accepts_source_forms_and_rejects_invalid_values():
    assert canonical_symbol("sh.600000") == "600000.SH"
    assert canonical_symbol("000001.sz") == "000001.SZ"
    assert canonical_symbol("600000") == "600000.SH"
    assert canonical_symbol("830001") == "830001.BJ"
    with pytest.raises(PointInTimeUniverseError, match="POINT-IN-TIME UNIVERSE REQUIRED"):
        canonical_symbol("AAPL")


def test_daily_membership_requires_exact_dates_counts_and_unique_keys():
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    valid = _membership(dates, [["600000.SH", "000001.SZ"]] * 2)
    result = validate_daily_membership(valid, dates, expected_member_count=2)
    assert result.groupby("date")["symbol"].nunique().tolist() == [2, 2]

    with pytest.raises(PointInTimeUniverseError, match="snapshot coverage mismatch"):
        validate_daily_membership(valid[valid["date"] == dates[0]], dates, 2)
    with pytest.raises(PointInTimeUniverseError, match="expected 2 unique members"):
        validate_daily_membership(valid.iloc[:-1], dates, 2)
    with pytest.raises(PointInTimeUniverseError, match="duplicate memberships"):
        validate_daily_membership(pd.concat([valid, valid.iloc[[0]]]), dates, 2)


def test_membership_flags_are_parsed_strictly_instead_of_using_truthiness():
    date = pd.Timestamp("2024-01-02")
    frame = pd.DataFrame(
        {
            "date": [date, date],
            "symbol": ["600000.SH", "000001.SZ"],
            "is_member": [1.0, "0"],
        }
    )
    result = validate_daily_membership(frame, [date], expected_member_count=1)
    assert result["symbol"].tolist() == ["600000.SH"]

    frame.loc[1, "is_member"] = "not-a-boolean"
    with pytest.raises(PointInTimeUniverseError, match="invalid is_member"):
        validate_daily_membership(frame, [date], expected_member_count=1)


def test_membership_intervals_preserve_exit_and_reentry_boundaries():
    dates = pd.bdate_range("2024-01-02", periods=5)
    daily = _membership(
        dates,
        [
            ["600000.SH"],
            ["600000.SH"],
            ["000001.SZ"],
            ["600000.SH"],
            ["600000.SH"],
        ],
    )
    intervals = compress_membership_intervals(daily)
    stock = intervals[intervals["symbol"] == "600000.SH"].reset_index(drop=True)
    assert stock[["entry_date", "exit_date", "interval"]].to_dict("records") == [
        {"entry_date": dates[0], "exit_date": dates[1], "interval": 1},
        {"entry_date": dates[3], "exit_date": dates[4], "interval": 2},
    ]

    universe = DataFramePointInTimeUniverse(daily)
    assert universe.get_members(dates[1]) == ["600000.SH"]
    assert universe.get_members(dates[2]) == ["000001.SZ"]
    with pytest.raises(PointInTimeUniverseError, match="no snapshot"):
        universe.get_members(dates[-1] + pd.offsets.BDay())


def test_filter_flags_use_only_past_windows_and_current_status():
    dates = pd.bdate_range("2024-01-02", periods=6)
    symbols = ["600000.SH", "000001.SZ"]
    rows = []
    for date in dates:
        for symbol in symbols:
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "open": 10.0,
                    "high": 11.0,
                    "low": 9.0,
                    "close": 10.0,
                    "volume": 100.0,
                }
            )
    bars = pd.DataFrame(rows)
    # A future missing observation must not affect an earlier day's flag.
    bars.loc[(bars["date"] == dates[4]) & (bars["symbol"] == "600000.SH"), "close"] = None
    # Two consecutive zero-volume observations invalidate only when both are in-window.
    bars.loc[(bars["date"].isin(dates[3:5])) & (bars["symbol"] == "000001.SZ"), "volume"] = 0.0
    status = pd.DataFrame(
        [
            {
                "date": date,
                "symbol": symbol,
                "trade_status": 1,
                "is_st": False,
            }
            for date in dates
            for symbol in symbols
        ]
    )
    status.loc[(status["date"] == dates[3]) & (status["symbol"] == "600000.SH"), "is_st"] = True
    status.loc[(status["date"] == dates[5]) & (status["symbol"] == "000001.SZ"), "trade_status"] = 0
    listings = pd.DataFrame(
        {"symbol": symbols, "listing_date": [dates[0], dates[0]]}
    )
    config = UniverseFilterConfig(
        min_listed_days=2,
        zero_volume_window=2,
        quality_window=3,
        min_quality_ratio=2.0 / 3.0,
    )

    flags = build_filter_flags(bars, status, listings, dates, config).set_index(
        ["date", "symbol"]
    )
    assert not flags.loc[(dates[0], "600000.SH"), "eligible"]
    assert flags.loc[(dates[2], "600000.SH"), "eligible"]
    assert not flags.loc[(dates[3], "600000.SH"), "eligible"]  # current ST
    assert flags.loc[(dates[4], "600000.SH"), "eligible"]  # 2/3 valid, no future use
    assert not flags.loc[(dates[4], "000001.SZ"), "eligible"]  # last two volumes zero
    assert not flags.loc[(dates[5], "000001.SZ"), "eligible"]  # suspended today


def test_filters_are_applied_after_strict_pit_validation():
    dates = pd.to_datetime(["2024-01-02"])
    membership = _membership(dates, [["600000.SH", "000001.SZ"]])
    flags = pd.DataFrame(
        {
            "date": [dates[0], dates[0]],
            "symbol": ["600000.SH", "000001.SZ"],
            "eligible": [True, False],
        }
    )
    filtered = apply_universe_filters(membership, flags, dates, expected_member_count=2)
    assert filtered["symbol"].tolist() == ["600000.SH"]

    with pytest.raises(PointInTimeUniverseError, match="expected 2 unique members"):
        apply_universe_filters(membership.iloc[:1], flags.iloc[:1], dates, 2)

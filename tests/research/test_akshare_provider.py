import pandas as pd
import pytest

from qbot.research.data.providers.akshare import AKShareProvider, ProviderError


def _vendor_frame(multiplier=1.0, include_turnover=True):
    values = {
        "日期": ["2024-01-02", "2024-01-03"],
        "开盘": [10.0 * multiplier, 11.0 * multiplier],
        "最高": [11.0 * multiplier, 12.0 * multiplier],
        "最低": [9.0 * multiplier, 10.0 * multiplier],
        "收盘": [10.5 * multiplier, 11.5 * multiplier],
        "成交量": [12.0, 15.0],
        "成交额": [12_600.0, 17_250.0],
    }
    if include_turnover:
        values["换手率"] = [2.0, 2.5]
    return pd.DataFrame(values)


class FakeAKShare:
    __version__ = "test"

    def __init__(self):
        self.stock_calls = []

    def stock_zh_a_hist(self, **kwargs):
        self.stock_calls.append(kwargs)
        multiplier = 2.0 if kwargs["adjust"] == "hfq" else 1.0
        return _vendor_frame(multiplier=multiplier)

    def index_zh_a_hist(self, **kwargs):
        return _vendor_frame(include_turnover=False)

    def index_stock_cons(self, **kwargs):
        return pd.DataFrame({"品种代码": ["600000", "000001", "600000"]})


def test_stock_bars_join_raw_and_hfq_and_convert_units():
    fake = FakeAKShare()
    provider = AKShareProvider(
        akshare_module=fake, retry_count=0, request_interval=0
    )
    bars = provider.get_daily_bars("600000.SH", "2024-01-01", "2024-01-04")

    assert [call["adjust"] for call in fake.stock_calls] == ["", "hfq"]
    assert all(call["symbol"] == "600000" for call in fake.stock_calls)
    assert bars["symbol"].unique().tolist() == ["600000.SH"]
    assert bars.loc[0, "open"] == bars.loc[0, "raw_open"] == 10.0
    assert bars.loc[0, "adj_open"] == 20.0
    assert bars.loc[0, "volume"] == 1_200.0
    assert bars.loc[0, "amount"] == 12_600.0
    assert bars.loc[0, "turnover"] == pytest.approx(0.02)
    assert bars.loc[0, "adj_factor"] == pytest.approx(2.0)


def test_index_bars_are_unadjusted_and_drive_calendar():
    provider = AKShareProvider(
        akshare_module=FakeAKShare(), retry_count=0, request_interval=0
    )
    bars = provider.get_index_bars("000905.SH", "2024-01-01", "2024-01-04")
    assert bars["adj_factor"].eq(1.0).all()
    assert bars["adj_close"].equals(bars["raw_close"])
    calendar = provider.get_trade_calendar("2024-01-01", "2024-01-04")
    assert calendar.tolist() == [
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-03"),
    ]


def test_historical_constituent_request_never_falls_back_to_current_snapshot():
    provider = AKShareProvider(
        akshare_module=FakeAKShare(), retry_count=0, request_interval=0
    )
    with pytest.raises(ProviderError, match="POINT-IN-TIME UNIVERSE REQUIRED"):
        provider.get_index_constituents("000905.SH", as_of="2022-01-01")


def test_current_constituent_snapshot_is_explicitly_marked():
    provider = AKShareProvider(
        akshare_module=FakeAKShare(), retry_count=0, request_interval=0
    )
    result = provider.get_index_constituents("000905.SH")
    assert result["symbol"].tolist() == ["000001.SZ", "600000.SH"]
    assert result["is_current_snapshot"].all()


def test_retry_uses_injected_backoff_without_network():
    sleeps = []

    class FlakyAK(FakeAKShare):
        def __init__(self):
            super().__init__()
            self.failures = 1

        def index_zh_a_hist(self, **kwargs):
            if self.failures:
                self.failures -= 1
                raise ConnectionError("temporary")
            return _vendor_frame(include_turnover=False)

    provider = AKShareProvider(
        akshare_module=FlakyAK(),
        retry_count=1,
        backoff_seconds=(0.5,),
        request_interval=0,
        sleep_fn=sleeps.append,
    )
    assert not provider.get_index_bars(
        "000905.SH", "2024-01-01", "2024-01-04"
    ).empty
    assert sleeps == [0.5]


def test_index_provider_uses_alternate_only_when_primary_attribute_is_absent():
    class AlternateOnlyAK:
        __version__ = "test"

        def __init__(self):
            self.fallback_calls = []

        def stock_zh_index_daily(self, **kwargs):
            self.fallback_calls.append(kwargs)
            return _vendor_frame(include_turnover=False)

    fake = AlternateOnlyAK()
    provider = AKShareProvider(
        akshare_module=fake,
        retry_count=0,
        request_interval=0,
    )

    bars = provider.get_index_bars(
        "000905.SH", "2024-01-01", "2024-01-04"
    )

    assert fake.fallback_calls == [{"symbol": "sh000905"}]
    assert bars["date"].tolist() == [
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-03"),
    ]
    assert bars.loc[0, "volume"] == 12.0

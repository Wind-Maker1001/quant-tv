"""Deterministic BaoStock status/listing retry and pacing contracts."""

import pandas as pd

from qbot.research.universe.csi500 import BaoStockPointInTimeProvider


class FakeQuery:
    def __init__(self, fields=(), rows=(), error_code="0", error_msg=""):
        self.fields = list(fields)
        self._rows = [list(row) for row in rows]
        self.error_code = error_code
        self.error_msg = error_msg
        self._position = -1

    def next(self):
        self._position += 1
        return self._position < len(self._rows)

    def get_row_data(self):
        return self._rows[self._position]


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(float(seconds))
        self.now += float(seconds)


def _basic_success(code):
    return FakeQuery(
        fields=("code", "ipoDate"),
        rows=((code, "1999-11-10"),),
    )


def _history_success(code):
    return FakeQuery(
        fields=("date", "code", "tradestatus", "isST"),
        rows=(
            ("2024-01-02", code, "1", "0"),
            ("2024-01-03", code, "0", "1"),
        ),
    )


def test_status_and_listing_queries_retry_and_share_one_rate_limiter():
    class FlakyClient:
        def __init__(self):
            self.basic_calls = 0
            self.history_calls = 0

        def query_stock_basic(self, code):
            self.basic_calls += 1
            if self.basic_calls == 1:
                return FakeQuery(error_code="100", error_msg="temporary basic failure")
            return _basic_success(code)

        def query_history_k_data_plus(self, code, fields, **kwargs):
            self.history_calls += 1
            if self.history_calls == 1:
                return FakeQuery(error_code="200", error_msg="temporary status failure")
            return _history_success(code)

    client = FlakyClient()
    clock = FakeClock()
    provider = BaoStockPointInTimeProvider(
        client=client,
        retry_count=1,
        backoff_seconds=(1.0,),
        request_interval=0.25,
        sleep_fn=clock.sleep,
        monotonic_fn=clock.monotonic,
    )

    status, listings, failures = provider.get_security_history(
        ["600000.SH"], "2024-01-02", "2024-01-03"
    )

    assert client.basic_calls == 2
    assert client.history_calls == 2
    assert clock.sleeps == [1.0, 0.25, 1.0]
    assert failures == []
    assert listings.to_dict("records") == [
        {"symbol": "600000.SH", "listing_date": pd.Timestamp("1999-11-10")}
    ]
    assert status["trade_status"].tolist() == [1, 0]
    assert status["is_st"].tolist() == [False, True]


def test_exhausted_symbol_failure_does_not_abort_remaining_symbols():
    class PartlyBrokenClient:
        def __init__(self):
            self.history_calls = {}

        def query_stock_basic(self, code):
            return _basic_success(code)

        def query_history_k_data_plus(self, code, fields, **kwargs):
            self.history_calls[code] = self.history_calls.get(code, 0) + 1
            if code == "sz.000001":
                return FakeQuery(error_code="300", error_msg="persistent failure")
            return _history_success(code)

    client = PartlyBrokenClient()
    provider = BaoStockPointInTimeProvider(
        client=client,
        retry_count=1,
        backoff_seconds=(0.0,),
        request_interval=0.0,
        sleep_fn=lambda seconds: None,
    )

    status, listings, failures = provider.get_security_history(
        ["600000.SH", "000001.SZ"], "2024-01-02", "2024-01-03"
    )

    assert client.history_calls == {"sz.000001": 2, "sh.600000": 1}
    assert failures == ["000001.SZ"]
    assert status["symbol"].unique().tolist() == ["600000.SH"]
    assert listings["symbol"].tolist() == ["600000.SH"]

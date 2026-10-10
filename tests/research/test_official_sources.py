"""Artificial API contracts; no claim that fixtures prove real PIT membership."""

import io
import json
import urllib.error

import pytest

from qbot.research.errors import CacheError, ProviderError, ProviderNetworkError
from qbot.research.universe.official_sources import OfficialAccessDeniedError, OfficialNoticeSource


class Response(io.BytesIO):
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, url, data):
        self.url = url
        super().__init__(data if isinstance(data, bytes) else json.dumps(data).encode("utf-8"))

    def geturl(self):
        return self.url


def detail(notice_id=13716):
    return {"success": True, "code": "200", "data": {
        "id": notice_id, "title": "SYNTHETIC NOTICE", "publishDate": "2021-09-08",
        "content": "SYNTHETIC CONTENT", "enclosureList": [{
            "noticeId": notice_id, "fileName": "synthetic.xlsx",
            "fileUrl": "https://oss-ch.csindex.com.cn/notice/synthetic.xlsx",
        }],
    }}


def source(tmp_path, responses, sleeps=None):
    calls = []
    def opener(request, timeout):
        calls.append((request.full_url, request.method, request.data, timeout))
        value = responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return Response(request.full_url, value)
    result = OfficialNoticeSource(tmp_path, opener=opener, sleeper=(sleeps if sleeps is not None else []).append)
    return result, calls


def test_raw_bytes_cache_binding_and_no_pit(tmp_path):
    client, calls = source(tmp_path, [detail(), b"PK SYNTHETIC NOT A REAL WORKBOOK"])
    row, notice = client.notice(13716)
    item = client.attachment(row["enclosureList"][0]["fileUrl"])
    assert item.receipt["point_in_time_universe_verified"] is False
    assert len(calls) == 2
    assert calls[0][1] == "GET"
    assert notice.json() == detail()
    assert not list(tmp_path.glob("*.tmp-*"))
    client.notice(13716)
    client.attachment(row["enclosureList"][0]["fileUrl"])
    assert len(calls) == 2
    assert not hasattr(client, "get_constituents") and not hasattr(client, "get_members")


def test_corrupt_bytes_fail_without_network(tmp_path):
    client, calls = source(tmp_path, [detail()])
    _, artifact = client.notice(13716)
    artifact.path.write_bytes(b"tampered")
    with pytest.raises(CacheError, match="hash mismatch"):
        client.notice(13716)
    assert len(calls) == 1


@pytest.mark.parametrize("field,value", [
    ("point_in_time_universe_verified", True), ("schema_version", True),
    ("bytes", True), ("file", "../escape.json"), ("http_status", 404),
])
def test_corrupt_receipt_is_not_repaired_or_used(tmp_path, field, value):
    client, calls = source(tmp_path, [detail()])
    client.notice(13716)
    path = next(tmp_path.glob("*.receipt.json"))
    receipt = json.loads(path.read_text(encoding="utf-8"))
    receipt[field] = value
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(CacheError):
        client.notice(13716)
    assert len(calls) == 1


@pytest.mark.parametrize("url", [
    "http://oss-ch.csindex.com.cn/notice/test.xlsx", "https://evil.com/notice/test.xlsx",
    "https://oss-ch.csindex.com.cn.evil.com/notice/test.xlsx",
    "https://user:password@oss-ch.csindex.com.cn/notice/test.xlsx",
    "https://oss-ch.csindex.com.cn:invalid/notice/test.xlsx",
    "https://oss-ch.csindex.com.cn/notice/test.xlsx#fragment",
    "https://oss-ch.csindex.com.cn/other/test.xlsx",
    "https://www.csindex.com.cn/unobserved-endpoint",
    "https://oss-ch.csindex.com.cn/notice/test.exe",
])
def test_only_observed_public_hosts_paths_and_formats(tmp_path, url):
    client, calls = source(tmp_path, [])
    with pytest.raises(ProviderError):
        client.attachment(url)
    assert calls == []


def test_transient_retry_and_backoff(tmp_path):
    sleeps = []
    client, calls = source(tmp_path, [TimeoutError(), TimeoutError(), detail()], sleeps)
    client.notice(13716)
    assert len(calls) == 3 and 1 in sleeps and 2 in sleeps
    assert all(call[3] == 30.0 for call in calls)


def test_unicode_attachment_url_encoded_without_double_encoding(tmp_path):
    client, calls = source(tmp_path, [b"PK artificial", b"PK artificial"])
    first = client.attachment("https://oss-ch.csindex.com.cn/notice/调整 名单.xlsx")
    assert calls[0][0] == "https://oss-ch.csindex.com.cn/notice/%E8%B0%83%E6%95%B4%20%E5%90%8D%E5%8D%95.xlsx"
    client.attachment(calls[0][0])
    assert calls[0][0] == calls[1][0]
    assert "调整" in first.receipt["request"]["url"]


def test_transport_exhaustion(tmp_path):
    client, calls = source(tmp_path, [TimeoutError()] * 4)
    with pytest.raises(ProviderNetworkError):
        client.notice(13716)
    assert len(calls) == 4
    assert not list(tmp_path.glob("*.receipt.json"))


def test_permanent_http_error_is_not_retried(tmp_path):
    client, calls = source(tmp_path, [urllib.error.HTTPError("u", 404, "not found", {}, None)])
    with pytest.raises(ProviderError, match="404"):
        client.notice(13716)
    assert len(calls) == 1


def test_site_denial_stops_all_further_requests_but_not_verified_cache_reads(tmp_path):
    client, calls = source(tmp_path, [detail(), urllib.error.HTTPError("u", 403, "forbidden", {}, None)])
    client.notice(13716)
    with pytest.raises(OfficialAccessDeniedError) as initial:
        client.notice(13420)
    assert initial.value.request_performed is True
    with pytest.raises(OfficialAccessDeniedError) as skipped:
        client.notice(13888)
    assert skipped.value.request_performed is False
    client.notice(13716)
    assert len(calls) == 2 and client.network_requests == 2 and client.cache_reads == 1


def test_cache_only_never_opens_network(tmp_path):
    client, _ = source(tmp_path, [detail()])
    client.notice(13716)
    def forbidden(*args, **kwargs):
        raise AssertionError("cache-only opened network")
    offline = OfficialNoticeSource(tmp_path, cache_only=True, opener=forbidden)
    offline.notice(13716)
    with pytest.raises(ProviderError, match="absent from the verified cache"):
        offline.notice(13420)
    assert offline.network_requests == 0 and offline.cache_reads == 1


@pytest.mark.parametrize("content", [b"<html>error</html>", b"", b"x" * (20 * 1024 * 1024 + 1)], ids=["html", "empty", "oversized"])
def test_invalid_attachment_not_cached(tmp_path, content):
    client, _ = source(tmp_path, [content])
    with pytest.raises(ProviderError):
        client.attachment("https://oss-ch.csindex.com.cn/notice/test.xlsx")
    assert not list(tmp_path.glob("*.receipt.json"))


@pytest.mark.parametrize("change", [
    {"success": False}, {"code": 200}, {"data": []},
])
def test_invalid_api_contract(tmp_path, change):
    value = detail()
    value.update(change)
    client, _ = source(tmp_path, [value])
    with pytest.raises(ProviderError):
        client.notice(13716)


def page(number, ids, total=3):
    return {"success": True, "code": "200", "total": total, "currentPage": number,
            "pageSize": 2, "data": [{"id": i, "title": "SYNTHETIC", "publishDate": "2021-09-08"} for i in ids]}


def test_complete_pagination_same_query_no_current_members(tmp_path):
    client, calls = source(tmp_path, [page(1, [1, 2]), page(2, [3])])
    rows, artifacts = client.catalogue(page_size=2)
    assert [row["id"] for row in rows] == [1, 2, 3] and len(artifacts) == 2
    queries = [json.loads(call[2]) for call in calls]
    assert [query["page"]["page"] for query in queries] == [1, 2]
    assert all(query["indexList"] == ["csi_index"] and query["searchInput"] == "" for query in queries)


@pytest.mark.parametrize("second", [page(2, [2]), page(2, []), page(2, [3], 4), page(1, [3])])
def test_changed_duplicate_or_truncated_page_rejected(tmp_path, second):
    client, _ = source(tmp_path, [page(1, [1, 2]), second])
    with pytest.raises(ProviderError):
        client.catalogue(page_size=2)


@pytest.mark.parametrize("field,value", [
    ("id", True), ("id", 999), ("title", ""), ("publishDate", "2021-9-08"),
    ("publishDate", "2021-02-30"), ("content", None), ("enclosureList", None),
    ("enclosureList", [{"noticeId": 999, "fileName": "a.xlsx", "fileUrl": "https://oss-ch.csindex.com.cn/notice/a.xlsx"}]),
])
def test_bad_notice_identity_dates_content_enclosures(tmp_path, field, value):
    payload = detail()
    payload["data"][field] = value
    client, _ = source(tmp_path, [payload])
    with pytest.raises(ProviderError):
        client.notice(13716)


@pytest.mark.parametrize("kwargs", [
    {"timeout_seconds": True}, {"timeout_seconds": 0}, {"timeout_seconds": float("nan")},
    {"request_interval_seconds": -1}, {"max_retries": 4}, {"max_retries": True},
])
def test_invalid_network_controls(tmp_path, kwargs):
    with pytest.raises(ProviderError):
        OfficialNoticeSource(tmp_path, **kwargs)

"""Assemble append-only evidence registers and a mapping proposal, not PIT data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path.cwd().resolve()
PUBLIC = ROOT / "docs/research/evidence/pit-phase1-20261018-v1"
PRIVATE = ROOT / "data/research/diagnostics/pit-phase1/20261018-v1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    stamp = datetime.now(timezone.utc).isoformat()
    event_data = load(PUBLIC / "candidate-events.json")["events"]
    existing_sources = load(PUBLIC / "source-index.json")["sources"]
    records = []
    for ev in event_data:
        r = ev["matrix"]
        for role, sid in [("NOTICE_BODY", ev["body_source_id"])] + [("NOTICE_ATTACHMENT", s) for s in ev["attachment_source_ids"]]:
            source = next(s for s in existing_sources if s["source_id"] == sid)
            records.append({"evidence_id": "%s-%s" % (r["notice_id"], role), "notice_id": r["notice_id"], "role": role,
                "source_url": source["source_url"], "local_path": source["path"], "local_file_sha256": source["sha256"],
                "publisher_original_response_sha256": (r["body_original_response_sha256"] if role == "NOTICE_BODY" else r["attachment_original_sha256"]),
                "body_response_text_utf8_sha256": r["body_response_text_sha256"] if role == "NOTICE_BODY" else "NOT_APPLICABLE",
                "representation": source["representation"], "publication_date": r["announcement_publish_date"] if role == "NOTICE_BODY" else "UNKNOWN",
                "publication_date_basis": "Current official body publishDate, not historical authentication" if role == "NOTICE_BODY" else "Attachment createAt and URL date are not established first publication dates",
                "parent_announcement_publish_date": r["announcement_publish_date"], "planned_after_close_date": r["planned_after_close_date"],
                "planned_explicit_start_date": r["planned_explicit_start_date"], "condition": r["condition"],
                "actual_effective_date": "UNKNOWN", "historical_known_at": "UNKNOWN", "retrieved_at_utc": r["retrieved_at_utc"] if role == "NOTICE_BODY" else "SEE_ORIGINAL_RECEIPT",
                "confidence": {"current_source_statement": "HIGH", "historical_availability": "INSUFFICIENT", "actual_index_implementation": "INSUFFICIENT"},
                "formal_admission": False})
    index = load(ROOT / "docs/research/evidence/five-year-data-feasibility-v1/pit-source-index.json")
    issuer_hash = "dd68049c48df826848f361fd9e7b23dd20b6805144a2e5bc36e54db638611488"
    issuer_entry = next(e for e in index["local_artifacts_rechecked"] if e["sha256"] == issuer_hash)
    issuer_path = ROOT / issuer_entry["local_relative_path"]
    assert digest(issuer_path) == issuer_hash
    original_receipt = load(issuer_path.with_suffix(".receipt.json"))
    successful = [p for p in (PRIVATE / "raw").glob("*/avic-2025-supervision-adviser.receipt.json") if load(p)["status"] == "SOURCE_BYTES_AVAILABLE"]
    assert len(successful) == 1
    rp = successful[0]; receipt = load(rp); adviser_path = rp.parent / receipt["file"]
    assert digest(adviser_path) == receipt["source_response_bytes_sha256"]
    common = {"notice_id": "NOT_INDEX_EVENT", "role": "SECURITY_CODE_TRANSITION", "publication_date": "UNKNOWN",
              "publication_date_basis": "Signature date, URL directory date, retrieval date and first publication are distinct",
              "actual_index_effective_date": "UNKNOWN", "historical_known_at": "UNKNOWN", "formal_admission": False}
    records.append(dict(common, evidence_id="identity-issuer-2025-028", source_url=original_receipt["source_url"], local_path=str(issuer_path.relative_to(ROOT)).replace("\\", "/"),
        local_file_sha256=issuer_hash, publisher_original_response_sha256=issuer_hash, representation="Previously acquired issuer PDF bytes, re-read; not a fresh network acquisition",
        document_signed_date="2025-02-14", url_directory_date="2025-02-15", declared_code_change_date="2025-02-17", actual_effective_date="UNKNOWN_EXCHANGE_OPERATIONAL_TIMESTAMP",
        retrieved_at_utc=original_receipt["completed_at_utc"], confidence={"announced_transition": "HIGH", "complete_identity_history": "INSUFFICIENT", "historical_availability": "INSUFFICIENT"}))
    records.append(dict(common, evidence_id="identity-adviser-2025-supervision", source_url=receipt["source_url"], local_path=str(adviser_path.relative_to(ROOT)).replace("\\", "/"),
        local_file_sha256=digest(adviser_path), publisher_original_response_sha256=digest(adviser_path), representation="Newly acquired publisher-hosted original PDF response bytes",
        document_signed_date="2026-05-08", signature_date_basis="Actual visual inspection of physical page 14 handwritten date", url_directory_date="2026-05-11",
        retrospectively_reported_code_change_date="2025-02-17", actual_effective_date="UNKNOWN_EXCHANGE_OPERATIONAL_TIMESTAMP",
        verified_pages=[1, 9, 14], retrieved_at_utc=receipt["completed_at_utc"], receipt_path=str(rp.relative_to(ROOT)).replace("\\", "/"), receipt_sha256=digest(rp),
        confidence={"retrospective_transition_statement": "HIGH", "historical_2025_availability": "INSUFFICIENT", "independent_upstream_fact_lineage": "UNKNOWN"}))
    write(PUBLIC / "evidence-register.json", {"schema": "PIT_PHASE1_EVIDENCE_REGISTER_V1", "created_at_utc": stamp, "evidence": records,
        "confidence_definition": "HIGH describes directly verified source wording and byte binding only; it does not authenticate historical availability or formally qualify membership.",
        "publisher_hash_unknown_rule": "Browser tool/container hashes are never substituted for missing original publisher response-byte hashes."})
    tools_path = PRIVATE / "tool-responses.json"; tools = load(tools_path)
    discovery = []
    for operation in tools["operations"]:
        if operation["id"] == "identity-adviser-pdf-scrape":
            continue
        result = operation["result"]
        if result.get("status") == "fulfilled":
            result = result["value"]
        value = result.get("structuredContent")
        if value is None:
            value = json.loads(result["content"][0]["text"])
        web = value.get("data", {}).get("web", [])
        discovery.append({"operation": operation["id"], "role": "IDENTITY_DISCOVERY" if operation["id"] == "search-5" else "BASELINE_DISCOVERY",
            "tool_result_id": value.get("id"), "returned_results": [{"url": w["url"], "title": w.get("title"), "source_original_sha256": "UNKNOWN", "publication_date": "UNKNOWN", "actual_effective_date": "UNKNOWN", "confidence": "DISCOVERY_ONLY"} for w in web],
            "complete_20210913_official_baseline_found": False})
    queries = {
        "search-1": 'site:csindex.com.cn "中证500" "2021-09" "成分"',
        "search-2": '"中证500" "2021年9月" "样本" site:csindex.com.cn OR site:oss-ch.csindex.com.cn',
        "search-3": '"000905" "20210913" 成分',
        "search-4": '"CSI 500" "September" "2021" constituents',
        "search-5": 'site:szse.cn "302132" "2025年2月17日"',
        "search-6": 'site:oss-ch.csindex.com.cn "中证500" "2021" "样本名单"',
        "search-7": '"中证500" "2021年9月13日" "名单"',
    }
    for d in discovery:d["query"] = queries[d["operation"]]
    prior_paths = [
        "data/research/diagnostics/pit-effective-membership-evidence/baseline-20261015-ciis-bounded/public-observations.json",
        "data/research/diagnostics/pit-effective-membership-evidence/regular-20261015-bounded-search/regular-review.draft.json",
        "data/research/diagnostics/pit-effective-membership-evidence/conditional-20261015T122346Z/conditional-review.draft.json",
        "docs/research/evidence/five-year-data-feasibility-v1/pit-gaps.json",
    ]
    prior_inputs = [{"path": s, "sha256": digest(ROOT / s)} for s in prior_paths]
    baseline = {"schema": "PIT_PHASE1_BASELINE_RESULT_V1", "target_index": "000905 / CSI500", "target_trading_date": "2021-09-13", "required_count": 500,
        "result": "BLOCKED_AUTHORITY_BASELINE_NOT_OBTAINED", "verified_complete_baselines": 0, "verified_members_from_authoritative_baseline": "UNKNOWN",
        "no_member_list_generated": True, "not_an_exhaustive_web_unavailability_proof": True, "new_baseline_search_count": 6, "all_new_search_count": 7,
        "new_scrape_count": 1, "direct_http_attempts": 2, "successful_original_downloads": 1,
        "direct_http_note": "First original-PDF fetch failed with URLError in sandbox; approved outside-sandbox retry succeeded. Neither request targeted CSI notice bodies.",
        "csi_notice_body_requests": 0, "csi_denied_workflow_reopened": False, "search_archive": str(tools_path.relative_to(ROOT)).replace("\\", "/"), "search_archive_sha256": digest(tools_path),
        "archive_timestamp_is_not_per_call_timestamp": True, "queries": discovery, "reused_prior_inputs": prior_inputs,
        "rejected_substitutes": ["Current 500 constituents", "BaoStock 499 query-date snapshot plus one guessed member", "000510 A500 or 000852 CSI1000 fact sheets", "ETF holdings/PCF baskets", "Adjustment add/remove lists as a baseline", "2021-labelled backtested performance in a current document"],
        "critical_boundary": {"notice_13716": "2021-09-10 after-close plan, one addition/removal only; actual and historical attachment availability UNKNOWN",
                             "notice_13420": "Listing-triggered China Energy change; source addition code '-' retained; 2021-09-13 transition membership UNKNOWN"},
        "formal_admission": False, "no_live_money": True}
    write(PUBLIC / "baseline-result.json", baseline)
    mapping = {"schema": "PIT_PHASE1_IDENTITY_MAPPING_PROPOSAL_V1", "proposal_only": True, "formal_identity_snapshot_eligible": False,
        "stable_security_id": "LOCAL-PROPOSED-AVIC-LISTING-001", "stable_id_authority": "Local design proposal; not an exchange identifier or ISIN", "master_identity_verified": False,
        "layers": ["Immutable supplier symbol and original row key", "Evidence-versioned supplier alias to stable security identity", "Historical exchange trading-symbol intervals", "Independent index-membership events linked through identity"],
        "transition": {"old_exchange_symbol": "300114.SZ", "new_exchange_symbol": "302132.SZ", "source_stated_code_change_date": "2025-02-17",
            "date_evidence_status": "ISSUER_IMPLEMENTATION_ANNOUNCEMENT_AND_LATER_ADVISER_RETROSPECTIVE_STATEMENT_AGREE", "effective_boundary_text": "2025-02-17 market open, as declared by issuer",
            "actual_exchange_operational_timestamp": "UNKNOWN", "first_historically_known_at": "UNKNOWN", "issuer_signature_date": "2025-02-14", "issuer_first_publication_date": "UNKNOWN",
            "listing_date": "UNKNOWN", "old_interval_start": "UNKNOWN", "old_inclusive_exit_session": "UNKNOWN", "new_interval_end": "UNKNOWN",
            "same_listed_entity_basis": "Issuer source states listed entity continues; full security-master and capital/reorganization history remain unqualified",
            "evidence_ids": ["identity-issuer-2025-028", "identity-adviser-2025-supervision"]},
        "supplier_alias": {"namespace": "YHH_LOCAL_DELIVERY_REVIEW_20261017", "namespace_is_local_audit_label": True, "original_supplier_identifier": "302132.SZ",
            "observed_delivery_range": ["2021-01-04", "2026-09-30"], "upstream_vendor_identity": "UNKNOWN", "alias_validity_contract": "UNKNOWN",
            "historical_code_conflict": "New exchange symbol used in pre-2025-02-17 delivered history; retain raw label and stage a separate mapping, never overwrite rows",
            "observation_evidence": "docs/research/evidence/independent-data-review-20261017-v1/security-observations.csv"},
        "required_fields_for_future_rows": ["supplier_namespace", "supplier_security_id", "stable_security_id", "exchange_symbol", "effective_start", "effective_end_inclusive", "relationship", "source_evidence_sha256", "available_at", "retrieved_at", "revision_id", "evidence_status"],
        "projection_to_existing_contract": "IdentitySnapshot accepts explicit inclusive intervals and available_at. UNKNOWN bounds/availability are not converted into a formal snapshot; do not invent a previous trading day.",
        "rejection_rules": ["Reject ambiguous/many-to-many identity matches", "Reject a PIT symbol not valid for its date", "Reject unavailable_at or unknown original listing identity", "Reject automatic merger/predecessor price splices", "Do not infer CSI500 membership from a code transition"],
        "formal_admission": False, "no_live_money": True}
    alias_path = ROOT / mapping["supplier_alias"]["observation_evidence"]
    aliases = pd.read_csv(alias_path)
    assert aliases.loc[aliases.symbol.eq("302132.SZ"), "observed_days"].iloc[0] == 1393
    assert not aliases.symbol.eq("300114.SZ").any()
    mapping["supplier_alias"]["observation_evidence_sha256"] = digest(alias_path)
    write(PUBLIC / "identity-mapping-proposal.json", mapping)
    gaps = []
    for e in event_data:
        r = e["matrix"]
        special = {
            13716: "Need original full membership files for 2021-09-10 close and 2021-09-13 open; attachment createAt 2021-09-23 is later than announcement.",
            13420: "Need official Gezhouba/China Energy transition handling and historical identity. IPO occurrence is not index implementation; retain '-'.",
            3006027: "Need original effective member snapshots/implementation for ST Renfu removal and Xinyuanwei addition; no next-Monday inference.",
            3006227: "CSI500 row concerns 601198.SH Dongxing removal and 603083.SH Cambridge addition. 601059 Cinda's event does not establish Dongxing's trigger or CSI500 implementation. Attachment is dated after research cutoff.",
        }
        gaps.append({"notice_id": r["notice_id"], "announcement_publish_date": r["announcement_publish_date"], "planned_after_close_date": r["planned_after_close_date"],
            "condition": r["condition"], "actual_effective_date": "UNKNOWN", "historical_known_at": "UNKNOWN", "confidence": "INSUFFICIENT_FOR_ACTUAL_IMPLEMENTATION",
            "missing_evidence": special.get(r["notice_id"], "Need publisher implementation confirmation, explicit before/after member snapshots, corrections and historical availability; date arithmetic is insufficient."),
            "complete_chain_asserted": False, "formal_admission": False})
    with (PUBLIC / "actual-effective-gaps.csv").open("x", encoding="utf-8", newline="") as stream:pd.DataFrame(gaps).to_csv(stream,index=False)
    visual = {"verified_at_utc": stamp, "method": "Human-visible image inspection through view_image, not inferred from extracted PDF text", "sources": [
        {"source_sha256": digest(adviser_path), "physical_pages": [9,14], "image_files": [{"path": str((PRIVATE/("adviser-p%d.png"%n)).relative_to(ROOT)).replace("\\", "/"), "sha256": digest(PRIVATE/("adviser-p%d.png"%n))} for n in [9,14]],
         "observations": ["Page 9 prints the old/new codes and 2025-02-17 transition", "Page 14 handwritten signature date reads 2026-05-08; not a first-publication timestamp"], "publication_date": "UNKNOWN"},
        {"source_sha256": issuer_hash, "physical_pages": [1], "image_path": str(issuer_path.parent.relative_to(ROOT)).replace("\\", "/")+"/code-change-p1.png", "observations": ["Issuer declares 2025-02-17 market-open use of 302132; listing entity continues"], "publication_date": "UNKNOWN"}]}
    write(PRIVATE / "visual-review.json", visual)
    write(PUBLIC / "delivery-assembly-receipt.json", {"created_at_utc": stamp, "script_sha256": digest(Path(__file__).resolve()), "network_requests": 0,
        "new_original_sha256": digest(adviser_path), "new_original_bytes": adviser_path.stat().st_size, "new_original_path": str(adviser_path.relative_to(ROOT)).replace("\\", "/"),
        "reused_issuer_path": str(issuer_path.relative_to(ROOT)).replace("\\", "/"), "reused_issuer_sha256": issuer_hash,
        "evidence_register_records": len(records), "market_price_files_opened": 0, "formal_admission": False, "no_live_money": True})
    print(json.dumps({"evidence_records":len(records),"baseline":"UNKNOWN / BLOCKED","identity_fact":"2025-02-17 transition retrospectively corroborated; historical availability UNKNOWN","new_original_sha256":digest(adviser_path)},ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Historical STATUS candidate integration. NO LIVE MONEY.

The reviewed reconciler produces retrospective, explicitly dated field facts.
Its contract cannot establish historical knowledge time. Decision-time status
therefore stays unknown, including when retrospective ST or halt facts exist.
This module uses existing SourceArtifact and security-data contracts; it cannot
publish a qualification package or register a new financial source.
"""

from dataclasses import dataclass

import pandas as pd

from qbot.research.data.evidence import SourceArtifact, timestamp
from qbot.research.universe.status import STATUS_COLUMNS
from qbot.research.universe.status_candidate import Adapter, EvidenceError
from qbot.research.universe.status_candidate.adapter import ROLE_STATUS
from qbot.research.universe.status_candidate.model import day, security


@dataclass(frozen=True)
class HistoricalStatus:
    """A pinned partial source, separate from certified security-data bundles."""

    source: SourceArtifact
    candidate: Adapter

    @classmethod
    def load(cls, source: SourceArtifact, *, allow_synthetic=False):
        if type(source) is not SourceArtifact:
            raise EvidenceError("TYPED_SOURCE_ARTIFACT_REQUIRED")
        source.read()
        candidate = Adapter.load(source.path, source.sha256,
                                 allow_synthetic=allow_synthetic)
        source.read()
        return cls(source, candidate)

    def query(self, symbol, trading_date, *, decision_at):
        """Return field facts plus a conservative research-decision projection.

        Announcement, effective interval, event/source record date, publication
        and retrieval dates remain distinct in ``facts.official_evidence``.
        None substitutes for unsupported first-availability/vintage evidence.
        Conflicting facts remain UNKNOWN with explicit SOURCE_CONFLICT.
        """
        cutoff = timestamp(decision_at)
        security(symbol)
        day(trading_date)
        self.source.read()
        if self.source.sha256 != self.candidate.bundle_sha256:
            raise EvidenceError("SOURCE_ARTIFACT_BUNDLE_IDENTITY_MISMATCH")
        facts = self.candidate.evaluate(symbol, trading_date)
        self.source.read()
        return {
            "symbol": symbol, "date": trading_date,
            "decision_at": cutoff.isoformat(),
            "source_id": self.source.source_id,
            "source_version": "historical-status-candidate:" + self.source.sha256,
            "source_sha256": self.source.sha256,
            "facts": facts,
            "decision_status": {"listing_status": "UNKNOWN",
                                "st_risk_status": "UNKNOWN",
                                "suspension_status": "UNKNOWN"},
            "historical_known_at": "UNKNOWN",
            "role_statuses": dict(ROLE_STATUS),
            "execution_admission": False,
            "no_live_money": True,
        }

    def status_frame(self, keys, *, decision_at):
        """Use the existing table shape with explicit nulls, never false defaults.

        validate_security_data and actual qualification replay reject these nulls.
        ST risk and suspension never imply each other's values. No filling,
        listing-date fabrication or event extrapolation is performed.
        """
        if (not isinstance(keys, pd.DataFrame)
                or set(keys.columns) != {"date", "symbol"}
                or keys.empty or keys.duplicated(["date", "symbol"]).any()):
            raise EvidenceError("EXPLICIT_UNIQUE_STATUS_KEYS_REQUIRED")
        rows = []
        for row in keys.sort_values(["date", "symbol"]).itertuples(index=False):
            # Column order is caller-controlled; always address named fields.
            value = row.date
            if not isinstance(value, str):
                if not isinstance(value, pd.Timestamp) or value.tzinfo is not None or value != value.normalize():
                    raise EvidenceError("CANONICAL_STATUS_DATE_REQUIRED")
                value = value.date().isoformat()
            self.query(row.symbol, value, decision_at=decision_at)
            rows.append({"date": pd.Timestamp(value), "symbol": row.symbol,
                         "trade_status": pd.NA, "is_st": pd.NA})
        result = pd.DataFrame(rows, columns=STATUS_COLUMNS)
        result["trade_status"] = result.trade_status.astype("Int64")
        result["is_st"] = result.is_st.astype("boolean")
        return result

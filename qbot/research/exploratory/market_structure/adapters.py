"""Read-only market context and explicit future research view interfaces."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from qbot.research.market.regime import build_market_regime_features

from .contracts import ContractError, MARKERS


def market_context(store, sessions, request):
    records = store.snapshot("benchmark", request.as_of, request.as_of)
    complete = {s.session_id: s for s in sessions if s.segments[-1][1] <= request.as_of}
    selected = {}
    for record in records:
        p = record.payload
        day = p["session_id"]
        price = p.get("adj_close")
        if (
            day in complete
            and record.observation_end == complete[day].segments[-1][1]
            and record.observation_end <= request.as_of
            and p.get("complete") is True
            and isinstance(price, (int, float))
            and not isinstance(price, bool)
            and np.isfinite(price)
            and price > 0
        ):
            if day in selected:
                raise ContractError("duplicate benchmark session")
            selected[day] = record
    if not selected:
        return dict(status="MARKET_CONTEXT_UNAVAILABLE"), ()
    last = max(selected, key=lambda day: complete[day].segments[-1][1])
    ordered = sorted(
        (
            s
            for s in complete.values()
            if s.segments[-1][1] <= complete[last].segments[-1][1]
        ),
        key=lambda s: s.segments[-1][1],
    )
    rows = []
    for session in ordered:
        rec = selected.get(session.session_id)
        rows.append(
            dict(
                date=pd.Timestamp(session.session_id),
                symbol="000905.SH",
                adj_close=rec.payload.get("adj_close") if rec else None,
            )
        )
    frame = pd.DataFrame(rows)
    frame["adj_close"] = pd.to_numeric(frame["adj_close"], errors="raise")
    computed = build_market_regime_features(frame)
    rec = selected[last]
    result = dict(
        status="OK",
        benchmark_session=last,
        revision=rec.revision,
        published_at=rec.published_at.isoformat(),
        available_at=rec.known_at.isoformat(),
        benchmark_observation_end=rec.observation_end.isoformat(),
        source_sha256=rec.sha256,
        age_seconds=(request.as_of - rec.observation_end).total_seconds(),
        missing_session_count=int(frame["adj_close"].isna().sum()),
    )
    result.update(computed.iloc[-1].drop(labels=["date"]).to_dict())
    return result, tuple(selected.values())


@dataclass(frozen=True)
class FutureModelInterface:
    model: str
    input_kind: str = "explicit numeric pandas.DataFrame; exact key alignment"
    feature_selection: str = "explicit opt-in only; separate from production registry"
    training: str = "NOT_IMPLEMENTED; no fit/predict calls in this PR"
    missing_values: str = (
        "existing model accepts NaN at validation; future training-only imputation must retain model policy"
    )
    labels: str = "supplied separately, training period only; no labels in this MVP"


class ResearchFeatureAdapter:
    """An explicit security view, never production DatasetBuilder admission."""

    model_interfaces = tuple(
        FutureModelInterface(m) for m in ("FactorScore", "Ridge", "LightGBM", "XGBoost")
    )

    def build_view(self, values, feature_ids, *, broadcast_market=False):
        if not feature_ids or len(set(feature_ids)) != len(feature_ids):
            raise ContractError("explicit unique features required")
        selected = values[values.feature_id.isin(feature_ids)].copy()
        if set(selected.feature_id) != set(feature_ids):
            raise ContractError("missing selected feature")
        if selected.grain.isin(["industry", "concept"]).any():
            raise ContractError(
                "group projection requires future explicit historical membership adapter"
            )
        if (selected.grain == "market").any() and not broadcast_market:
            raise ContractError("market broadcast requires explicit opt-in")
        keys = ["scenario", "frequency", "observation_end", "as_of", "decision_time"]
        stocks = values[values.grain == "security"][
            keys + ["entity_id"]
        ].drop_duplicates()
        pieces = stocks.copy()
        for name in feature_ids:
            f = selected[selected.feature_id == name]
            join = keys if f.grain.eq("market").all() else keys + ["entity_id"]
            if f.duplicated(join).any():
                raise ContractError("ambiguous feature view keys")
            pieces = pieces.merge(
                f[join + ["value"]].rename(columns={"value": name}),
                on=join,
                how="left",
                validate="many_to_one",
            )
        pieces.attrs.update(
            MARKERS,
            production_dataset_adapter="NOT_CONNECTED",
            group_projection="NOT_IMPLEMENTED",
            market_broadcast=bool(broadcast_market),
        )
        return pieces

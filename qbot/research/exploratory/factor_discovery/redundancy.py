"""Pairwise daily cross-section redundancy, never pooled across dates."""

from itertools import combinations
import time

import numpy as np
import pandas as pd

from .contracts import DiscoveryConfig, DiscoveryError, ErrorCode


def original_structure_hashes(config=DiscoveryConfig()):
    """Read-only documented translations; AMIHU needs unavailable Abs/scale."""
    from .contracts import Node
    from .engine import compile_expression

    close, ret, volume, turn = [
        Node("Field", value=name)
        for name in ("adj_close", "RET1", "volume", "turnover")
    ]
    one, zero = Node("Const", value=1), Node("Const", value=0)

    def mean(node, n):
        return Node("RollingMean", (node,), param=n)

    def ratio(a, b):
        return Node("SafeDiv", (a, b))

    def excess(a, b):
        return Node("Sub", (ratio(a, b), one))

    nodes = {
        "MOM%d" % n: excess(close, Node("Lag", (close,), param=n)) for n in (20, 60)
    }
    nodes.update(
        {
            "REV%d"
            % n: Node("Sub", (zero, excess(close, Node("Lag", (close,), param=n))))
            for n in (1, 5)
        }
    )
    nodes.update(
        {"VOL%d" % n: Node("RollingStd", (ret,), param=n) for n in (5, 20, 60)}
    )
    nodes.update({"TURN%d" % n: mean(turn, n) for n in (5, 20)})
    nodes.update(
        {
            "VOLUME_RATIO": ratio(mean(volume, 5), mean(volume, 20)),
            "PRICE_MA20": excess(close, mean(close, 20)),
            "MA5_MA20": excess(mean(close, 5), mean(close, 20)),
            "MA20_MA60": excess(mean(close, 20), mean(close, 60)),
        }
    )
    hashes = {}
    for name, node in nodes.items():
        try:
            hashes[name] = compile_expression(node, config).expression_sha256
        except DiscoveryError:
            # Narrow whitelists may make a documented old expression unavailable.
            pass
    return hashes


def diagnose_redundancy(
    frame, candidates, originals, config=DiscoveryConfig(), deadline=None
):
    names = list(candidates) + list(originals)
    if len(names) != len(set(names)) or not set(["date", "symbol"] + names).issubset(
        frame
    ):
        raise DiscoveryError(
            ErrorCode.INVALID_INPUT, "unique redundancy fields required"
        )
    if frame.duplicated(["date", "symbol"]).any():
        raise DiscoveryError(ErrorCode.INVALID_INPUT, "duplicate redundancy keys")
    local = frame.loc[
        frame["date"].between(
            pd.Timestamp(config.development_start), pd.Timestamp(config.development_end)
        )
    ]
    pairs = [
        (i, j) for i, j in combinations(range(len(names)), 2) if i < len(candidates)
    ]
    count = len(pairs)
    if local["date"].nunique() * count > config.max_diagnostic_records:
        raise DiscoveryError(
            ErrorCode.BUDGET_EXCEEDED, "redundancy diagnostic record limit"
        )
    valid_dates = np.zeros(count, dtype=int)
    total_pairs = np.zeros(count, dtype=int)
    signed = np.zeros(count)
    absolute = np.zeros(count)
    coverage_sum = np.zeros(count)
    identical = np.ones(count, dtype=bool)
    daily_rows = []
    for date, cross in local.groupby("date", sort=True):
        if deadline is not None and time.perf_counter() >= deadline:
            raise DiscoveryError(ErrorCode.BUDGET_EXCEEDED, "redundancy runtime budget")
        values = cross[names].to_numpy(dtype=float)
        finite = np.isfinite(values)
        # Scale by column max before covariance to contain legitimate extremes.
        scale = np.max(np.where(finite, np.abs(values), 0), axis=0)
        scale[scale == 0] = 1
        scaled = np.where(finite, values / scale, 0)
        mask = finite.astype(float)
        n = mask.T @ mask
        sums = scaled.T @ mask
        squares = (scaled * scaled).T @ mask
        with np.errstate(invalid="ignore", divide="ignore"):
            covariance = scaled.T @ scaled - sums * sums.T / n
            variance = np.maximum(squares - sums * sums / n, 0)
            corr = covariance / np.sqrt(variance * variance.T)
        corr = np.clip(corr, -1, 1)
        for index, (i, j) in enumerate(pairs):
            paired = int(n[i, j])
            coverage = paired / len(cross)
            coverage_sum[index] += coverage
            total_pairs[index] += paired
            pair_mask = finite[:, i] & finite[:, j]
            same = np.array_equal(finite[:, i], finite[:, j]) and np.array_equal(
                values[pair_mask, i], values[pair_mask, j]
            )
            identical[index] &= same
            value = corr[i, j] if paired >= config.minimum_cross_section else np.nan
            if np.isfinite(value):
                valid_dates[index] += 1
                signed[index] += value
                absolute[index] += abs(value)
            daily_rows.append(
                {
                    "date": date,
                    "left": names[i],
                    "right": names[j],
                    "observations": paired,
                    "pair_coverage": coverage,
                    "pearson": value,
                    "same_values_and_missing_mask": bool(same),
                }
            )
    dates = local["date"].nunique()
    summary = []
    for index, (i, j) in enumerate(pairs):
        days = int(valid_dates[index])
        coverage = coverage_sum[index] / dates if dates else 0
        enough = (
            days >= config.minimum_evaluation_dates
            and coverage >= config.minimum_pair_coverage
        )
        mean_abs = absolute[index] / days if days else np.nan
        status = "UNDETERMINED"
        if enough:
            if identical[index]:
                status = "NUMERIC_DUPLICATE"
            elif mean_abs >= config.redundancy_threshold:
                status = "HIGHLY_REDUNDANT"
            else:
                status = "NON_REDUNDANT"
        summary.append(
            {
                "left": names[i],
                "right": names[j],
                "comparison": "ORIGINAL14" if j >= len(candidates) else "CANDIDATE",
                "status": status,
                "valid_dates": days,
                "development_dates": int(dates),
                "mean_pair_coverage": coverage,
                "mean_pearson": signed[index] / days if days else np.nan,
                "mean_abs_pearson": mean_abs,
                "paired_observations": int(total_pairs[index]),
                "exact_values_and_missing_mask": bool(identical[index]),
            }
        )
    return pd.DataFrame(summary), pd.DataFrame(daily_rows)

"""Paired-design mathematics. No world, model, network, entropy or experiment code."""
from functools import lru_cache
from math import fsum, nextafter


def valid_counts(x, n):
    if type(n) is not int or type(x) is not int or not 0 <= x <= n:
        raise ValueError("integer counts with 0<=x<=n required")


def masses(n, p):
    valid_counts(0, n)
    if not 0 <= p <= 1:
        raise ValueError("probability")
    if p == 0:
        return [1.0] + [0.0] * n
    if p == 1:
        return [0.0] * n + [1.0]
    mode = min(n, int((n + 1) * p))
    a = [0.0] * (n + 1)
    a[mode] = 1.0
    for k in range(mode, 0, -1):
        a[k-1] = a[k] * k / (n-k+1) * (1-p) / p
    for k in range(mode, n):
        a[k+1] = a[k] * (n-k) / (k+1) * p / (1-p)
    total = fsum(a)
    return [v / total for v in a]


@lru_cache(maxsize=None)
def lower_critical(m):
    """Largest k with P(Bin(m,1/2)<=k)<1/80, exact integer comparison.

    Equality is impossible: 1/80 is not dyadic. Thus this also implements <=.
    Positive support occurs when candidate wins >= m-k.
    """
    valid_counts(0, m)
    term, cumulative, cutoff, denominator = 1, 0, -1, 1 << m
    for k in range(m // 2 + 1):
        cumulative += term
        if 80 * cumulative < denominator:
            cutoff = k
        else:
            break
        term = term * (m-k) // (k+1)
    return cutoff


@lru_cache(maxsize=4096)
def cp_interval(x, n):
    """Central97.5% Clopper-Pearson; outward numerical display bounds.

    Exact sign decisions are computed separately using integers. Endpoints use
    mode-centred binomial sums and 64 bisections. Empty conditional sample ->[0,1].
    """
    valid_counts(x, n)
    if n == 0:
        return [0.0, 1.0]
    alpha = 1 / 80
    lower, upper = 0.0, 1.0
    if x:
        lo, hi = 0.0, 1.0
        for _ in range(64):
            mid = (lo + hi) / 2
            if fsum(masses(n, mid)[x:]) < alpha:
                lo = mid
            else:
                hi = mid
        lower = max(0.0, nextafter(lo, 0.0))
    if x < n:
        lo, hi = 0.0, 1.0
        for _ in range(64):
            mid = (lo + hi) / 2
            if fsum(masses(n, mid)[:x+1]) > alpha:
                lo = mid
            else:
                hi = mid
        upper = min(1.0, nextafter(hi, 1.0))
    return [lower, upper]


def paired_interval(n, gain, loss):
    valid_counts(gain, n)
    valid_counts(loss, n)
    if n == 0 or gain + loss > n:
        raise ValueError("positive N and disjoint paired outcome counts required")
    m = gain + loss
    theta = cp_interval(m, n)
    beta = cp_interval(gain, m)
    corners = [t * (2*b-1) for t in theta for b in beta]
    return {"estimate": (gain-loss)/n, "theta": theta, "beta": beta,
            "delta": [min(corners), max(corners)], "coverage_at_least": 0.95}


def directional_status(gain, loss):
    valid_counts(gain, gain+loss)
    valid_counts(loss, gain+loss)
    m = gain+loss
    k = lower_critical(m)
    if k >= 0 and gain >= m-k:
        return "supported_positive"
    if k >= 0 and gain <= k:
        return "refuted_positive_supported_negative"
    return "inconclusive"


def decision(n, n11, n10, n01, n00, technical_missing=0, wrong_certificates=0,
             integrity_ok=True, resource_contract_ok=True):
    for x in (n11, n10, n01, n00, technical_missing, wrong_certificates):
        valid_counts(x, n)
    if n == 0 or n11+n10+n01+n00+technical_missing != n:
        raise ValueError("fixed planned denominator must be accounted for")
    if wrong_certificates:
        return {"status": "invalid_certificate_hold", "inferential_claim": False}
    if not integrity_ok or not resource_contract_ok:
        return {"status": "contract_or_integrity_hold", "inferential_claim": False}
    if technical_missing:
        return {"status": "technical_incomplete", "inferential_claim": False,
                "delta_identification_bounds": [(n10-n01-technical_missing)/n,
                                                 (n10-n01+technical_missing)/n]}
    interval = paired_interval(n, n10, n01)
    status = directional_status(n10, n01)
    lo, hi = interval["delta"]
    if (lo > 0) != (status == "supported_positive") or (hi < 0) != status.startswith("refuted"):
        raise ArithmeticError("numeric interval and exact sign decision disagree")
    magnitude = ("at_least_interest_threshold" if lo >= 0.02 else
                 "below_interest_threshold" if hi < 0.02 else "interest_threshold_unresolved")
    return {"status": status, "inferential_claim": True, "interval": interval,
            "magnitude_status": magnitude,
            "cost_utility": "separate measured structural counters; no automatic deployment verdict"}


def extra_work_per_net_certificate(extra_work, gain, loss):
    if extra_work < 0:
        # A saving is permitted and must stay signed.
        pass
    return extra_work/(gain-loss) if gain > loss else None


def positive_power(n, gain_probability, loss_probability):
    """Numerical finite binomial mixture for the SAME positive interval decision.

    Negligible outer masses <=1e-18 may be skipped; their full sum is a reported
    absolute bound on omitted contribution. No Monte Carlo draws are made.
    """
    valid_counts(0, n)
    if n == 0 or min(gain_probability, loss_probability) < 0:
        raise ValueError("positive N and nonnegative probabilities")
    theta = gain_probability + loss_probability
    if theta > 1:
        raise ValueError("disjoint probabilities")
    if theta == 0:
        return {"positive": 0.0, "negative": 0.0, "omitted_mass_bound": 0.0}
    beta = gain_probability/theta
    outer = masses(n, theta)
    positive, negative, omitted = [], [], []
    for m, weight in enumerate(outer):
        if weight <= 1e-18:
            omitted.append(weight)
            continue
        k = lower_critical(m)
        if k < 0:
            continue
        inner = masses(m, beta)
        positive.append(weight * fsum(inner[m-k:]))
        negative.append(weight * fsum(inner[:k+1]))
    return {"positive": fsum(positive), "negative": fsum(negative),
            "omitted_mass_bound": fsum(omitted)}

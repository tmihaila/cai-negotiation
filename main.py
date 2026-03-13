import plotly.io as pio
from negmas import SAOMechanism, TimeBasedConcedingNegotiator, make_issue
from negmas.preferences import LinearAdditiveUtilityFunction as LUFun
from negmas.preferences.value_fun import LinearFun, IdentityFun, AffineFun

from negotiators.boa_negociator import BOANegotiator
from analysis.metrics import (
    compute_pareto_frontier,
    compute_nash_point,
    compute_social_welfare,
)

pio.renderers.default = "browser"

# ─── Issues ─────────────────────────────────────────────────────────────────

issues = [
    make_issue(name="price",    values=10),
    make_issue(name="delivery", values=5),
    make_issue(name="quality",  values=3),
]

N_STEPS = 100

# ─── Opposing utility functions ──────────────────────────────────────────────
# Agent  = BUYER:  wants low price, fast delivery, high quality
# Opponent = SELLER: wants high price, slow delivery, high quality

def make_ufuns():
    from negmas.preferences import LinearAdditiveUtilityFunction as LUFun
    from negmas.outcomes import make_issue

    # Buyer: price low = good (value 0 = best), delivery low = good, quality high = good
    ufun_buyer = LUFun(
        values={
            "price":    lambda v: 1.0 - v / 9.0,   # price 0 → 1.0, price 9 → 0.0
            "delivery": lambda v: 1.0 - v / 4.0,   # delivery 0 → 1.0, delivery 4 → 0.0
            "quality":  lambda v: v / 2.0,          # quality 0 → 0.0, quality 2 → 1.0
        },
        weights={"price": 0.6, "delivery": 0.2, "quality": 0.2},
        issues=issues,
        reserved_value=0.0,
    )

    # Seller: price high = good, delivery slow = ok, quality high = good
    ufun_seller = LUFun(
        values={
            "price":    lambda v: v / 9.0,          # price 9 → 1.0, price 0 → 0.0
            "delivery": lambda v: v / 4.0,          # delivery 4 → 1.0, delivery 0 → 0.0
            "quality":  lambda v: v / 2.0,
        },
        weights={"price": 0.6, "delivery": 0.2, "quality": 0.2},
        issues=issues,
        reserved_value=0.0,
    )

    return ufun_buyer.scale_max(1.0), ufun_seller.scale_max(1.0)

# ─── Combos ──────────────────────────────────────────────────────────────────

COMBOS = [
    ("adaptive",  "acnext", "bayesian",  "Adaptive + ACnext + Bayesian"),
    ("adaptive",  "acasp",  "frequency", "Adaptive + ACasp + Frequency"),
    ("timebased", "aclow",  "gp",        "TimeBased + AClow + GP"),
    ("titfortat", "acnext", "bayesian",  "TitForTat + ACnext + Bayesian"),
    ("micro",     "acasp",  "frequency", "MiCRO + ACasp + Frequency"),
]

# ─── Runner ──────────────────────────────────────────────────────────────────

def run_session(bidding, acceptance, opponent_model, label):
    session = SAOMechanism(issues=issues, n_steps=N_STEPS)

    ufun_agent, ufun_opponent = make_ufuns()

    opponent = TimeBasedConcedingNegotiator(name="seller")
    agent    = BOANegotiator(
        bidding_strategy=bidding,
        acceptance_strategy=acceptance,
        opponent_model=opponent_model,
        name=label,
    )

    session.add(opponent, ufun=ufun_opponent)
    session.add(agent,    ufun=ufun_agent)

    result    = session.run()
    agreement = result.agreement

    u_agent    = float(ufun_agent(agreement))    if agreement else 0.0
    u_opponent = float(ufun_opponent(agreement)) if agreement else 0.0

    util_sw, egal_sw = compute_social_welfare(agreement, ufun_agent, ufun_opponent)

    all_outcomes = list(session.outcome_space.enumerate_or_sample(300))
    pareto = compute_pareto_frontier(all_outcomes, ufun_agent, ufun_opponent)
    nash   = compute_nash_point(pareto, ufun_agent.reserved_value, ufun_opponent.reserved_value)

    nash_u1 = nash[1] if nash else None
    nash_u2 = nash[2] if nash else None
    nash_distance = None
    if nash and agreement:
        nash_distance = ((u_agent - nash_u1) ** 2 + (u_opponent - nash_u2) ** 2) ** 0.5

    return {
        "label":         label,
        "agreed":        agreement is not None,
        "rounds":        result.step,
        "u_agent":       round(u_agent, 4),
        "u_opponent":    round(u_opponent, 4),
        "util_welfare":  round(util_sw, 4) if util_sw else None,
        "egal_welfare":  round(egal_sw, 4) if egal_sw else None,
        "pareto_size":   len(pareto),
        "nash_u1":       round(nash_u1, 4) if nash_u1 else None,
        "nash_u2":       round(nash_u2, 4) if nash_u2 else None,
        "nash_distance": round(nash_distance, 4) if nash_distance else None,
    }

# ─── Print ───────────────────────────────────────────────────────────────────

def print_table(results):
    headers = ["Label", "Agreed", "Rounds", "U(agent)", "U(opp)", "Util SW", "Egal SW", "Nash Dist"]
    col_w   = [36, 7, 7, 10, 10, 9, 9, 10]

    header_row = "  ".join(h.ljust(w) for h, w in zip(headers, col_w))
    print("\n" + "=" * len(header_row))
    print(header_row)
    print("=" * len(header_row))

    for r in results:
        row = [
            r["label"],
            "✓" if r["agreed"] else "✗",
            str(r["rounds"]),
            str(r["u_agent"]),
            str(r["u_opponent"]),
            str(r["util_welfare"]) if r["util_welfare"] else "—",
            str(r["egal_welfare"]) if r["egal_welfare"] else "—",
            str(r["nash_distance"]) if r["nash_distance"] else "—",
        ]
        print("  ".join(str(v).ljust(w) for v, w in zip(row, col_w)))

    print("=" * len(header_row))

    agreed = [r for r in results if r["agreed"]]
    print(f"\nAgreement rate: {len(agreed)}/{len(results)}")
    if agreed:
        avg_u  = sum(r["u_agent"] for r in agreed) / len(agreed)
        avg_sw = sum(r["util_welfare"] for r in agreed if r["util_welfare"]) / len(agreed)
        best   = max(agreed, key=lambda r: r["u_agent"])
        print(f"Avg agent utility (when agreed): {avg_u:.4f}")
        print(f"Avg utilitarian welfare:         {avg_sw:.4f}")
        print(f"Best strategy (agent utility):   {best['label']} → {best['u_agent']}")

# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running BOA strategy tournament...\n")
    results = []
    for (bidding, acceptance, opp_model, label) in COMBOS:
        print(f"  Running: {label}...")
        try:
            r = run_session(bidding, acceptance, opp_model, label)
            results.append(r)
        except Exception as e:
            import traceback
            print(f"    ERROR: {e}")
            traceback.print_exc()

    print_table(results)
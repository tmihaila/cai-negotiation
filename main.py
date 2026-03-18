import plotly.io as pio
from negmas import SAOMechanism, TimeBasedConcedingNegotiator
import importlib

from negotiators.boa_negotiator import BOANegotiator
from analysis.metrics import (
    compute_pareto_frontier,
    compute_nash_point,
    compute_kalai_smorodinsky_point,
    compute_social_welfare,
    compute_pareto_distance,
)

pio.renderers.default = "browser"

N_STEPS = 100
N_RUNS_PER_STRATEGY = 1
N_DOMAINS = 20

# ─── Combos ──────────────────────────────────────────────────────────────────

COMBOS = [
    ("timebased", "aclow",  "gp",        "TimeBased + AClow + GP"),
    ("adaptive",  "acnext", "bayesian",  "Adaptive + ACnext + Bayesian"),
    ("adaptive",  "acnew",  "frequency", "Adaptive + ACnew + Frequency"),
    ("titfortat", "acnew",  "bayesian",  "TitForTat + ACnew + Bayesian 🥹"),
    ("titfortat", "acnext", "bayesian",  "TitForTat + ACnext + Bayesian"),
    ("titfortat", "acasp",  "bayesian", "TitForTat + ACasp + Bayesian"),
    ("micro",     "acasp",  "frequency", "MiCRO + ACasp + Frequency"),
    ("predictive_titfortat", "acnext", "gp", "PredictiveTfT+ACnext+GP"),
]

# ─── Runner ──────────────────────────────────────────────────────────────────

def run_session(bidding, acceptance, opponent_model, label, domain_num):
    """Run a single negotiation session on a specific domain."""
    domain_module = importlib.import_module(f'domains_python.domain{domain_num:02d}')
    issues = domain_module.issues
    ufun_agent = domain_module.ufun_a
    ufun_opponent = domain_module.ufun_b
    
    session = SAOMechanism(issues=issues, n_steps=N_STEPS)

    opponent = BOANegotiator(
        bidding_strategy="micro",
        acceptance_strategy="acasp",
        opponent_model="frequency",
        name="Opponent",
    )
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
    ks     = compute_kalai_smorodinsky_point(pareto, ufun_agent.reserved_value, ufun_opponent.reserved_value)
    
    nash_u1 = nash[1] if nash else None
    nash_u2 = nash[2] if nash else None
    nash_distance = None
    if nash and agreement:
        nash_distance = ((u_agent - nash_u1) ** 2 + (u_opponent - nash_u2) ** 2) ** 0.5
    
    ks_u1 = ks[1] if ks else None
    ks_u2 = ks[2] if ks else None
    ks_distance = None
    if ks and agreement:
        ks_distance = ((u_agent - ks_u1) ** 2 + (u_opponent - ks_u2) ** 2) ** 0.5
    
    pareto_distance = compute_pareto_distance(agreement, pareto, ufun_agent, ufun_opponent)

    return {
        "label":          label,
        "domain":         domain_num,
        "agreed":         agreement is not None,
        "rounds":         result.step,
        "u_agent":        u_agent,
        "u_opponent":     u_opponent,
        "util_welfare":   util_sw,
        "egal_welfare":   egal_sw,
        "pareto_size":    len(pareto),
        "nash_distance":  nash_distance,
        "ks_distance":    ks_distance,
        "pareto_distance": pareto_distance,
    }

# ─── Aggregation ────────────────────────────────────────────────────────────

def aggregate_results(all_results):
    """Aggregate results by strategy label, averaging across domains and runs."""
    from collections import defaultdict
    
    aggregated = defaultdict(lambda: {
        "agreed_count": 0,
        "total_runs": 0,
        "u_agent_sum": 0.0,
        "u_opponent_sum": 0.0,
        "util_welfare_sum": 0.0,
        "egal_welfare_sum": 0.0,
        "nash_distance_sum": 0.0,
        "ks_distance_sum": 0.0,
        "pareto_distance_sum": 0.0,
        "rounds_sum": 0,
        "nash_count": 0,
        "ks_count": 0,
        "pareto_count": 0,
    })
    
    for r in all_results:
        label = r["label"]
        agg = aggregated[label]
        
        agg["total_runs"] += 1
        if r["agreed"]:
            agg["agreed_count"] += 1
            agg["u_agent_sum"] += r["u_agent"]
            agg["u_opponent_sum"] += r["u_opponent"]
            if r["util_welfare"] is not None:
                agg["util_welfare_sum"] += r["util_welfare"]
            if r["egal_welfare"] is not None:
                agg["egal_welfare_sum"] += r["egal_welfare"]
            agg["rounds_sum"] += r["rounds"]
        
        if r["nash_distance"] is not None:
            agg["nash_distance_sum"] += r["nash_distance"]
            agg["nash_count"] += 1
        if r["ks_distance"] is not None:
            agg["ks_distance_sum"] += r["ks_distance"]
            agg["ks_count"] += 1
        if r["pareto_distance"] is not None:
            agg["pareto_distance_sum"] += r["pareto_distance"]
            agg["pareto_count"] += 1
    
    results = []
    for label, agg in aggregated.items():
        agreed_count = agg["agreed_count"]
        total_runs = agg["total_runs"]
        
        results.append({
            "label": label,
            "agreement_rate": f"{agreed_count}/{total_runs}",
            "avg_rounds": round(agg["rounds_sum"] / agreed_count, 2) if agreed_count > 0 else None,
            "avg_u_agent": round(agg["u_agent_sum"] / agreed_count, 4) if agreed_count > 0 else None,
            "avg_u_opponent": round(agg["u_opponent_sum"] / agreed_count, 4) if agreed_count > 0 else None,
            "avg_util_welfare": round(agg["util_welfare_sum"] / agreed_count, 4) if agreed_count > 0 else None,
            "avg_egal_welfare": round(agg["egal_welfare_sum"] / agreed_count, 4) if agreed_count > 0 else None,
            "avg_nash_distance": round(agg["nash_distance_sum"] / agg["nash_count"], 4) if agg["nash_count"] > 0 else None,
            "avg_ks_distance": round(agg["ks_distance_sum"] / agg["ks_count"], 4) if agg["ks_count"] > 0 else None,
            "avg_pareto_distance": round(agg["pareto_distance_sum"] / agg["pareto_count"], 4) if agg["pareto_count"] > 0 else None,
        })
    
    return results

# ─── Print ───────────────────────────────────────────────────────────────────

def print_table(results):
    headers = ["Label", "Agreement", "Rounds", "U(agent)", "U(opp)", "Util SW", "Egal SW", "Nash Dist", "KS Dist", "Pareto Dist"]
    col_w   = [36, 11, 8, 10, 10, 10, 10, 11, 11, 12]

    header_row = "  ".join(h.ljust(w) for h, w in zip(headers, col_w))
    print("\n" + "=" * len(header_row))
    print(header_row)
    print("=" * len(header_row))

    for r in results:
        row = [
            r["label"],
            r["agreement_rate"],
            str(r["avg_rounds"]) if r["avg_rounds"] is not None else "—",
            str(r["avg_u_agent"]) if r["avg_u_agent"] is not None else "—",
            str(r["avg_u_opponent"]) if r["avg_u_opponent"] is not None else "—",
            str(r["avg_util_welfare"]) if r["avg_util_welfare"] is not None else "—",
            str(r["avg_egal_welfare"]) if r["avg_egal_welfare"] is not None else "—",
            str(r["avg_nash_distance"]) if r["avg_nash_distance"] is not None else "—",
            str(r["avg_ks_distance"]) if r["avg_ks_distance"] is not None else "—",
            str(r["avg_pareto_distance"]) if r["avg_pareto_distance"] is not None else "—",
        ]
        print("  ".join(str(v).ljust(w) for v, w in zip(row, col_w)))

    print("=" * len(header_row))
    
    best = max(results, key=lambda r: r["avg_u_agent"] if r["avg_u_agent"] is not None else 0)
    print(f"\nBest strategy (avg agent utility): {best['label']} → {best['avg_u_agent']}")

# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Running BOA strategy evaluation on {N_DOMAINS} domains with {N_RUNS_PER_STRATEGY} runs per strategy...\n")
    
    all_results = []
    total_experiments = len(COMBOS) * N_DOMAINS * N_RUNS_PER_STRATEGY
    completed = 0
    
    for (bidding, acceptance, opp_model, label) in COMBOS:
        print(f"Strategy: {label}")
        for domain_num in range(N_DOMAINS):
            print(f"  Domain {domain_num:02d}: ", end="", flush=True)
            for run in range(N_RUNS_PER_STRATEGY):
                try:
                    r = run_session(bidding, acceptance, opp_model, label, domain_num)
                    all_results.append(r)
                    completed += 1
                    if (run + 1) % 2 == 0:
                        print(".", end="", flush=True)
                except Exception as e:
                    print(f"E", end="", flush=True)
                    import traceback
                    traceback.print_exc()
            print(f" ✓ ({completed}/{total_experiments})")
        print()
    
    print("\n" + "="*120)
    print("AGGREGATED RESULTS (Averaged across all domains and runs)")
    print("="*120)
    
    aggregated = aggregate_results(all_results)
    print_table(aggregated)
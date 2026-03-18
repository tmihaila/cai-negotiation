import plotly.io as pio
from negmas import SAOMechanism, TimeBasedConcedingNegotiator
from negotiators.boa_negotiator import BOANegotiator
from analysis.metrics import compute_pareto_frontier, compute_nash_point, compute_social_welfare
from domains import get_all_domains

pio.renderers.default = "browser"

N_STEPS = 500

COMBOS = [
    ("adaptive",  "acnext", "bayesian",  "Adaptive+ACnext+Bayes"),
    ("adaptive",  "acasp",  "frequency", "Adaptive+ACasp+Freq"),
    ("timebased", "aclow",  "gp",        "TimeBased+AClow+GP"),
    ("titfortat", "acnext", "bayesian",  "TitForTat+ACnext+Bayes"),
    ("micro", "acnext", "frequency", "MiCRO+ACnext+Freq"),
]


def run_session(domain, bidding, acceptance, opponent_model, label):
    issues      = domain["issues"]
    ufun_agent  = domain["ufun_buyer"]
    ufun_opp    = domain["ufun_seller"]

    session  = SAOMechanism(issues=issues, n_steps=N_STEPS)
    opponent = BOANegotiator(
        bidding_strategy="titfortat",
        acceptance_strategy="aclow",
        opponent_model="frequency",
        name="Opponent:TimeBased",
    )
    agent    = BOANegotiator(
        bidding_strategy=bidding,
        acceptance_strategy=acceptance,
        opponent_model=opponent_model,
        name=label,
    )
    session.add(agent,    ufun=ufun_agent)
    session.add(opponent, ufun=ufun_opp)

    result    = session.run()
    agreement = result.agreement

    u_agent = float(ufun_agent(agreement)) if agreement else 0.0
    u_opp   = float(ufun_opp(agreement))   if agreement else 0.0
    util_sw, egal_sw = compute_social_welfare(agreement, ufun_agent, ufun_opp)

    all_outcomes = list(session.outcome_space.enumerate_or_sample(300))
    pareto = compute_pareto_frontier(all_outcomes, ufun_agent, ufun_opp)
    nash   = compute_nash_point(pareto, ufun_agent.reserved_value, ufun_opp.reserved_value)

    nash_u1 = nash[1] if nash else None
    nash_u2 = nash[2] if nash else None
    nash_dist = None
    if nash and agreement:
        nash_dist = ((u_agent - nash_u1) ** 2 + (u_opp - nash_u2) ** 2) ** 0.5

    return {
        "domain":       domain["name"],
        "strategy":     label,
        "agreed":       agreement is not None,
        "rounds":       result.step,
        "u_agent":      round(u_agent, 4),
        "u_opp":        round(u_opp, 4),
        "util_sw":      round(util_sw, 4) if util_sw else None,
        "egal_sw":      round(egal_sw, 4) if egal_sw else None,
        "nash_dist":    round(nash_dist, 4) if nash_dist else None,
    }


def print_table(results):
    headers = ["Domain", "Strategy", "Agreed", "Rounds", "U(agent)", "U(opp)", "Util SW", "Egal SW", "Nash Dist"]
    col_w   = [20, 26, 7, 7, 10, 10, 9, 9, 10]

    sep = "  ".join("-" * w for w in col_w)
    header_row = "  ".join(h.ljust(w) for h, w in zip(headers, col_w))
    print("\n" + "=" * len(header_row))
    print(header_row)
    print("=" * len(header_row))

    current_domain = None
    for r in results:
        if r["domain"] != current_domain:
            if current_domain is not None:
                print(sep)
            current_domain = r["domain"]

        row = [
            r["domain"],
            r["strategy"],
            "✓" if r["agreed"] else "✗",
            str(r["rounds"]),
            str(r["u_agent"]),
            str(r["u_opp"]),
            str(r["util_sw"])   if r["util_sw"]   else "—",
            str(r["egal_sw"])   if r["egal_sw"]   else "—",
            str(r["nash_dist"]) if r["nash_dist"] else "—",
        ]
        print("  ".join(str(v).ljust(w) for v, w in zip(row, col_w)))

    print("=" * len(header_row))

    # Summary: average agent utility per strategy across all domains
    print("\n── Average agent utility per strategy (across all domains) ──")
    for (_, _, _, label) in COMBOS:
        rows = [r for r in results if r["strategy"] == label and r["agreed"]]
        if rows:
            avg = sum(r["u_agent"] for r in rows) / len(rows)
            print(f"  {label.ljust(28)} {avg:.4f}  ({len(rows)}/{len(get_all_domains())} agreed)")
        else:
            print(f"  {label.ljust(28)} no agreements")


if __name__ == "__main__":
    domains = get_all_domains()
    results = []

    for domain in domains:
        # print(f"\nDomain: {domain['name']}")
        for (bidding, acceptance, opp_model, label) in COMBOS:
            # print(f"  Running: {label}...")
            try:
                r = run_session(domain, bidding, acceptance, opp_model, label)
                results.append(r)
            except Exception as e:
                import traceback
                print(f"    ERROR: {e}")
                traceback.print_exc()

    print_table(results)
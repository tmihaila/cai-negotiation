import importlib
from collections import defaultdict
from itertools import combinations
from negmas import SAOMechanism

from negotiators.boa_negotiator import BOANegotiator

N_STEPS = 100
N_DOMAINS = 10

COMBOS = [
    ("adaptive",  "acnext", "bayesian",  "Adaptive+ACnext+Bayesian"),
    ("adaptive",  "acasp",  "frequency", "Adaptive+ACasp+Frequency"),
    ("timebased", "aclow",  "gp",        "TimeBased+AClow+GP"),
    ("titfortat", "acnext", "bayesian",  "TitForTat+ACnext+Bayesian"),
    ("micro",     "acasp",  "frequency", "MiCRO+ACasp+Frequency"),
    ("predictive_titfortat", "acnext", "gp", "PredictiveTfT+ACnext+GP"),
    ("predictive_titfortat", "acnew", "gp", "PredictiveTfT+ACnew+GP"),
]


def run_negotiation(agent1_config, agent2_config, domain_num):
    """Run a single negotiation between two agents."""
    domain_module = importlib.import_module(f'domains_python.domain{domain_num:02d}')
    issues = domain_module.issues
    ufun_a = domain_module.ufun_a
    ufun_b = domain_module.ufun_b
    
    session = SAOMechanism(issues=issues, n_steps=N_STEPS)
    
    bidding1, acceptance1, opp_model1, label1 = agent1_config
    bidding2, acceptance2, opp_model2, label2 = agent2_config
    
    agent1 = BOANegotiator(
        bidding_strategy=bidding1,
        acceptance_strategy=acceptance1,
        opponent_model=opp_model1,
        name=label1,
    )
    
    agent2 = BOANegotiator(
        bidding_strategy=bidding2,
        acceptance_strategy=acceptance2,
        opponent_model=opp_model2,
        name=label2,
    )
    
    session.add(agent1, ufun=ufun_a)
    session.add(agent2, ufun=ufun_b)
    
    result = session.run()
    agreement = result.agreement
    
    u1 = float(ufun_a(agreement)) if agreement else 0.0
    u2 = float(ufun_b(agreement)) if agreement else 0.0
    
    return {
        "agent1": label1,
        "agent2": label2,
        "agreed": agreement is not None,
        "u1": u1,
        "u2": u2,
        "welfare": u1 + u2 if agreement else 0.0,
        "advantage": u1 - u2,
        "fairness": min(u1, u2) / max(u1, u2) if agreement and max(u1, u2) > 0 else 0.0,
    }


def run_tournament():
    """Run round-robin tournament."""
    print(f"Running tournament with {len(COMBOS)} strategies on {N_DOMAINS} domains...\n")
    
    for i, (_, _, _, label) in enumerate(COMBOS, 1):
        print(f"  {i}. {label}")
    
    all_matchups = list(combinations(range(len(COMBOS)), 2))
    total_negotiations = len(all_matchups) * N_DOMAINS
    
    print(f"\nTotal matchups: {len(all_matchups)}")
    print(f"Total negotiations: {total_negotiations}")
    print(f"\nRunning negotiations...\n")
    
    results = []
    completed = 0
    
    for i, j in all_matchups:
        agent1_config = COMBOS[i]
        agent2_config = COMBOS[j]
        label1 = agent1_config[3]
        label2 = agent2_config[3]
        
        print(f"Matchup: {label1} vs {label2}")
        
        for domain_num in range(N_DOMAINS):
            try:
                result = run_negotiation(agent1_config, agent2_config, domain_num)
                results.append(result)
                completed += 1
                
                if (completed % 10) == 0:
                    print(f"  Progress: {completed}/{total_negotiations} ({100*completed/total_negotiations:.1f}%)")
            except Exception as e:
                print(f"  Error on domain {domain_num}: {e}")
        
        print()
    
    print(f"\nCompleted {completed}/{total_negotiations} negotiations\n")
    
    return aggregate_results(results)


def aggregate_results(results):
    """Aggregate results by agent."""
    stats = defaultdict(lambda: {
        "negotiations": 0,
        "agreements": 0,
        "total_utility": 0.0,
        "total_advantage": 0.0,
        "total_welfare": 0.0,
        "total_fairness": 0.0,
    })
    
    for r in results:
        for agent_key, u_key, adv_sign in [("agent1", "u1", 1), ("agent2", "u2", -1)]:
            agent = r[agent_key]
            stats[agent]["negotiations"] += 1
            
            if r["agreed"]:
                stats[agent]["agreements"] += 1
                stats[agent]["total_utility"] += r[u_key]
                stats[agent]["total_advantage"] += r["advantage"] * adv_sign
                stats[agent]["total_welfare"] += r["welfare"]
                stats[agent]["total_fairness"] += r["fairness"]
    
    summary = {}
    for agent, s in stats.items():
        n_negs = s["negotiations"]
        n_agree = s["agreements"]
        
        summary[agent] = {
            "agreement_rate": n_agree / n_negs if n_negs > 0 else 0.0,
            "avg_utility": s["total_utility"] / n_agree if n_agree > 0 else 0.0,
            "avg_advantage": s["total_advantage"] / n_negs if n_negs > 0 else 0.0,
            "avg_welfare": s["total_welfare"] / n_agree if n_agree > 0 else 0.0,
            "avg_fairness": s["total_fairness"] / n_agree if n_agree > 0 else 0.0,
        }
    
    return summary


def print_results(summary):
    """Print tournament results."""
    print("="*120)
    print("TOURNAMENT RESULTS")
    print("="*120)
    
    print("\n=== Final Scores (by Average Advantage) ===")
    sorted_agents = sorted(summary.items(), key=lambda x: x[1]["avg_advantage"], reverse=True)
    for rank, (agent, stats) in enumerate(sorted_agents, 1):
        print(f"{rank}. {agent:40s}: {stats['avg_advantage']:+.4f}")
    
    print("\n=== Detailed Metrics ===\n")
    
    print("1. Agreement Rate:")
    sorted_by_agreement = sorted(summary.items(), key=lambda x: x[1]["agreement_rate"], reverse=True)
    for agent, stats in sorted_by_agreement:
        print(f"   {agent:40s}: {stats['agreement_rate']:.2%}")
    
    print("\n2. Average Utility:")
    sorted_by_utility = sorted(summary.items(), key=lambda x: x[1]["avg_utility"], reverse=True)
    for agent, stats in sorted_by_utility:
        print(f"   {agent:40s}: {stats['avg_utility']:.4f}")
    
    print("\n3. Average Welfare:")
    sorted_by_welfare = sorted(summary.items(), key=lambda x: x[1]["avg_welfare"], reverse=True)
    for agent, stats in sorted_by_welfare:
        print(f"   {agent:40s}: {stats['avg_welfare']:.4f}")
    
    print("\n4. Average Fairness:")
    sorted_by_fairness = sorted(summary.items(), key=lambda x: x[1]["avg_fairness"], reverse=True)
    for agent, stats in sorted_by_fairness:
        print(f"   {agent:40s}: {stats['avg_fairness']:.4f}")
    
    print("\n" + "="*120)


if __name__ == "__main__":
    summary = run_tournament()
    print_results(summary)
"""
Outcome and process analysis tools for negotiation results.
"""


def compute_pareto_frontier(outcomes, ufun1, ufun2):
    """
    Compute the Pareto frontier from a list of outcomes.
    Returns a list of (outcome, u1, u2) that are Pareto-optimal (non-dominated).
    """
    scored = [(o, float(ufun1(o)), float(ufun2(o))) for o in outcomes]
    pareto = []
    for i, (o1, u1, v1) in enumerate(scored):
        dominated = False
        for j, (o2, u2, v2) in enumerate(scored):
            if i != j and u2 >= u1 and v2 >= v1 and (u2 > u1 or v2 > v1):
                dominated = True
                break
        if not dominated:
            pareto.append((o1, u1, v1))
    return pareto


def compute_nash_point(pareto_frontier, reservation1=0.0, reservation2=0.0):
    """
    Nash Bargaining Solution: maximizes (u1 - r1) * (u2 - r2) over Pareto-optimal outcomes.
    Returns (outcome, u1, u2) or None if no valid point exists.
    """
    best = None
    best_product = -1
    for (outcome, u1, u2) in pareto_frontier:
        product = (u1 - reservation1) * (u2 - reservation2)
        if product > best_product:
            best_product = product
            best = (outcome, u1, u2)
    return best


def compute_social_welfare(agreement, ufun1, ufun2):
    """
    Utilitarian social welfare: u1 + u2
    Egalitarian social welfare: min(u1, u2)
    Returns (utilitarian, egalitarian)
    """
    if agreement is None:
        return None, None
    u1 = float(ufun1(agreement))
    u2 = float(ufun2(agreement))
    return u1 + u2, min(u1, u2)


def classify_step(u1_before, u2_before, u1_after, u2_after, epsilon=1e-4):
    """
    Classify a negotiation step based on utility changes for both agents.

    Step types:
    - Fortunate:  both gain (u1 up, u2 up)
    - Concession: self loses, opponent gains
    - Selfish:    self gains, opponent loses
    - Nice:       self neutral, opponent gains
    - Silent:     both stay (no change)
    - Unfortunate: both lose
    """
    d1 = u1_after - u1_before
    d2 = u2_after - u2_before

    if d1 > epsilon and d2 > epsilon:
        return "Fortunate"
    elif d1 < -epsilon and d2 > epsilon:
        return "Concession"
    elif d1 > epsilon and d2 < -epsilon:
        return "Selfish"
    elif abs(d1) <= epsilon and d2 > epsilon:
        return "Nice"
    elif abs(d1) <= epsilon and abs(d2) <= epsilon:
        return "Silent"
    else:
        return "Unfortunate"


def compute_sensitivity(step_types):
    """
    Sensitivity = cooperative_steps / total_steps
    Cooperative = Fortunate + Nice + Concession
    Non-cooperative = Selfish + Silent + Unfortunate
    """
    if not step_types:
        return 0.0
    cooperative = {"Fortunate", "Nice", "Concession"}
    n_coop = sum(1 for s in step_types if s in cooperative)
    return n_coop / len(step_types)


def analyze_trace(offer_history_agent1, offer_history_agent2, ufun1, ufun2):
    """
    Analyze the negotiation trace for agent 1.
    offer_history_agent1: list of offers proposed by agent 1 over time
    offer_history_agent2: list of offers proposed by agent 2 over time

    Returns a dict with step classifications and sensitivity.
    """
    steps = []
    n = min(len(offer_history_agent1), len(offer_history_agent2))

    for i in range(1, n):
        prev1 = offer_history_agent1[i - 1]
        curr1 = offer_history_agent1[i]
        prev2 = offer_history_agent2[i - 1]
        curr2 = offer_history_agent2[i]

        u1_before = float(ufun1(prev1))
        u1_after = float(ufun1(curr1))
        u2_before = float(ufun2(prev2))
        u2_after = float(ufun2(curr2))

        step_type = classify_step(u1_before, u2_before, u1_after, u2_after)
        steps.append(step_type)

    sensitivity = compute_sensitivity(steps)
    return {"steps": steps, "sensitivity": sensitivity}
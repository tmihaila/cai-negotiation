class TitForTatBidding:
    """
    Tit-for-Tat (imitative) bidding strategy.
    Mirrors the opponent's concession size.

    - If opponent makes a large concession (increases utility for us), we do the same.
    - If opponent makes no concession, we don't either.
    - Starts by proposing our best bid; concedes proportionally to opponent.

    Note: "concession" in TfT terms means the opponent offered us more utility
    than they did previously.
    """

    def __init__(self, ufun, sensitivity=1.0):
        self.ufun = ufun
        self.sensitivity = sensitivity  # How much we mirror the opponent (1.0 = equal)
        self._opponent_utility_history = []
        self._my_last_utility = 1.0  # Start at our best

    def update_opponent_history(self, offer):
        if offer is not None:
            u = self.ufun(offer)
            self._opponent_utility_history.append(u)

    def _opponent_last_concession(self):
        """
        Compute the opponent's most recent concession as delta in their utility to us.
        A positive concession means they moved toward an offer that's better for us.
        """
        if len(self._opponent_utility_history) < 2:
            return 0.0
        delta = (
            self._opponent_utility_history[-1]
            - self._opponent_utility_history[-2]
        )
        return delta  # Positive = they gave us more utility (they conceded)

    def target_utility(self, t):
        """
        We decrease our target by the same amount the opponent recently conceded to us.
        If they gave us 0.05 more utility, we lower our target by 0.05 * sensitivity.
        """
        concession = self._opponent_last_concession()
        self._my_last_utility = max(
            self.ufun.reserved_value,
            self._my_last_utility - self.sensitivity * concession
        )
        return self._my_last_utility

    def generate_bid(self, outcome_space, t):
        target = self.target_utility(t)
        best_bid = None
        best_diff = float("inf")
        for bid in outcome_space.enumerate_or_sample(200):
            u = self.ufun(bid)
            diff = abs(u - target)
            if diff < best_diff:
                best_bid = bid
                best_diff = diff
        if best_bid is None:
            best_bid = outcome_space.random_outcome()
        return best_bid
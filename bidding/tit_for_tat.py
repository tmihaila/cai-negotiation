class TitForTatBidding:
    """
    Tit-for-Tat (imitative) bidding strategy.
    Mirrors the opponent's concession size.

    Fix: target_utility() no longer mutates state on every call.
    State is only updated in update_opponent_history(), which is called
    once per round from the negotiator. generate_bid() and acceptance
    checks can call target_utility() freely without side effects.
    """

    def __init__(self, ufun, sensitivity=1.0):
        self.ufun = ufun
        self.sensitivity = sensitivity
        self._opponent_utility_history = []
        self._my_last_utility = 1.0  # Start at our best

    def update_opponent_history(self, offer):
        """
        Called once per round when opponent makes an offer.
        This is the only place we update _my_last_utility.
        """
        if offer is None:
            return
        u = self.ufun(offer)
        self._opponent_utility_history.append(u)

        # Compute concession and update our target
        if len(self._opponent_utility_history) >= 2:
            delta = (
                self._opponent_utility_history[-1]
                - self._opponent_utility_history[-2]
            )
            # Positive delta = opponent gave us more utility = they conceded
            # We mirror by lowering our own target by the same amount
            self._my_last_utility = max(
                self.ufun.reserved_value,
                self._my_last_utility - self.sensitivity * delta
            )

    def target_utility(self, t):
        """
        Read-only: returns current target utility without mutating state.
        Safe to call multiple times per round.
        """
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
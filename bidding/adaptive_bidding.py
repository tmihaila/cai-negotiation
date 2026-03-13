class AdaptiveBidding:
    """
    Adaptive bidding strategy.
    Uses opponent model to estimate the opponent's concession limit (beta)
    and adjusts its own target utility to exploit that limit.

    If opponent seems to be conceding toward a low utility, we can be tougher.
    If opponent seems stuck at high utility, we concede more to avoid deadlock.
    """

    def __init__(self, ufun, opponent_model, e=1.2):
        self.ufun = ufun
        self.opponent_model = opponent_model
        self.e = e
        self._opponent_utility_history = []

    def update_opponent_history(self, offer):
        if offer is not None:
            u = self.ufun(offer)
            self._opponent_utility_history.append(u)

    def _estimate_opponent_limit(self):
        """
        Linear extrapolation of the opponent's utility offers to predict
        where they'll end up (their reservation/limit value).
        """
        history = self._opponent_utility_history
        if len(history) < 3:
            return 0.5  # Default assumption: opponent targets ~50% utility

        # Fit a simple linear trend to the last few offers
        n = min(len(history), 10)
        recent = history[-n:]
        xs = list(range(n))
        x_mean = sum(xs) / n
        y_mean = sum(recent) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, recent))
        denominator = sum((x - x_mean) ** 2 for x in xs)

        if denominator == 0:
            return y_mean

        slope = numerator / denominator
        # Extrapolate to the end of the negotiation
        predicted_end = y_mean + slope * (100 - len(history))
        return max(0.0, min(1.0, predicted_end))

    def target_utility(self, t):
        reservation = self.ufun.reserved_value

        # Estimate opponent's concession limit and adapt beta accordingly
        opponent_limit = self._estimate_opponent_limit()

        # If opponent will concede a lot, be tougher (higher beta target)
        # If opponent is tough, concede more to avoid deadlock
        adaptive_reservation = max(reservation, opponent_limit * 0.9)
        beta = max(reservation, min(0.9, adaptive_reservation))

        return 1.0 - (1.0 - beta) * (t ** (1.0 / self.e))

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
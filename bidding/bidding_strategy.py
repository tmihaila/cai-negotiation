class TimeBasedBidding:
    """
    Time-based concession strategy.
    Starts at max utility and concedes toward reservation value over time.
    Concession shape controlled by e (e < 1 = Boulware, e = 1 = linear, e > 1 = Conceder).
    """

    def __init__(self, ufun, e=1.2):
        self.ufun = ufun
        self.e = e

    def target_utility(self, t):
        reservation = self.ufun.reserved_value
        return 1.0 - (1.0 - reservation) * (t ** (1.0 / self.e))

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
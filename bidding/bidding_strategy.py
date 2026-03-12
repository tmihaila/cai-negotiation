class BiddingStrategy:

    def __init__(self, ufun):
        self.ufun = ufun

    def target_utility(self, t):
        reservation = self.ufun.reserved_value

        # Concession Parameter
        e = 1.2

        return 1 - (1 - reservation) * (t ** (1/e))

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
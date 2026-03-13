class AcceptanceStrategy:

    def __init__(self, ufun, bidding_strategy):
        self.ufun = ufun
        self.bidding_strategy = bidding_strategy

    def should_accept(self, offer, time):
        if offer is None:
            return False

        utility = self.ufun(offer)
        target = self.bidding_strategy.target_utility(time)

        return utility >= target
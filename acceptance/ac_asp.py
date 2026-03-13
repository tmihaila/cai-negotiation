class ACasp:
    def __init__(self, ufun, bidding_strategy):
        self.ufun = ufun
        self.bidding = bidding_strategy
 
    def should_accept(self, offer, time, outcome_space):
        if offer is None:
            return False
        offer_utility = self.ufun(offer)
        aspiration = self.bidding.target_utility(time)
        return offer_utility >= aspiration
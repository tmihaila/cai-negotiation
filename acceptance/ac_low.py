class AClow:
    def __init__(self, ufun, bidding_strategy):
        self.ufun = ufun
        self.bidding = bidding_strategy
        self._my_bid_utilities = []
 
    def record_my_bid(self, bid):
        if bid is not None:
            self._my_bid_utilities.append(self.ufun(bid))
 
    def should_accept(self, offer, time, outcome_space):
        if offer is None:
            return False
        offer_utility = self.ufun(offer)
 
        next_bid = self.bidding.generate_bid(outcome_space, time)
        if offer_utility >= self.ufun(next_bid):
            return True
 
        if self._my_bid_utilities:
            if offer_utility >= min(self._my_bid_utilities):
                return True
 
        return False
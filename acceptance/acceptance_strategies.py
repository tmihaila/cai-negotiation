class ACnext:
    """
    ACnext: Accept if opponent's offer utility >= utility of our next planned bid.
    Uses target_utility() directly instead of calling generate_bid(),
    which avoids side effects and double-computation issues.
    """

    def __init__(self, ufun, bidding_strategy):
        self.ufun = ufun
        self.bidding = bidding_strategy

    def should_accept(self, offer, time, outcome_space):
        if offer is None:
            return False
        offer_utility = self.ufun(offer)
        next_utility = self.bidding.target_utility(time)
        return offer_utility >= next_utility


class ACasp:
    """
    ACasp: Accept if opponent's offer utility >= current aspiration level.
    """

    def __init__(self, ufun, bidding_strategy):
        self.ufun = ufun
        self.bidding = bidding_strategy

    def should_accept(self, offer, time, outcome_space):
        if offer is None:
            return False
        offer_utility = self.ufun(offer)
        aspiration = self.bidding.target_utility(time)
        return offer_utility >= aspiration


class AClow:
    """
    AClow: Accept if offer >= next planned bid OR >= any bid we've previously proposed.
    """

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

        # Check against next planned utility target
        if offer_utility >= self.bidding.target_utility(time):
            return True

        # Check against lowest utility we've ever offered
        if self._my_bid_utilities:
            if offer_utility >= min(self._my_bid_utilities):
                return True

        return False
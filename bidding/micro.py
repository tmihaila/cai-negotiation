class MiCROBidding:
    """
    MiCRO: Minimal Concession Strategy.
    Makes the smallest possible concession for each new opponent offer.
    """

    def __init__(self, ufun, opponent_model=None):
        self.ufun = ufun
        self.opponent_model = opponent_model
        self._last_opponent_offer = None
        self._my_bids = []
        self._all_outcomes = None
        self._cached_bid = None

    def update_opponent_offer(self, offer):
        self._last_opponent_offer = offer
        self._cached_bid = None

    def target_utility(self, t):
        if self._my_bids:
            return float(self.ufun(self._my_bids[-1]))
        return 1.0

    def _sorted_outcomes(self, outcome_space):
        if self._all_outcomes is None:
            outcomes = list(outcome_space.enumerate_or_sample(500))
            self._all_outcomes = sorted(
                outcomes,
                key=lambda o: float(self.ufun(o)),
                reverse=True
            )
        return self._all_outcomes

    def _opp_rank(self, offer, all_outcomes):
        """Higher rank = better for opponent (worse for us)."""
        for i, o in enumerate(all_outcomes):
            if o == offer:
                return i / max(1, len(all_outcomes) - 1)
        return 0.5

    def _opp_utility(self, offer, all_outcomes):
        if (self.opponent_model is not None
                and hasattr(self.opponent_model, "total_offers")
                and self.opponent_model.total_offers >= 5):
            return self.opponent_model.estimate_utility(offer)
        return self._opp_rank(offer, all_outcomes)

    def generate_bid(self, outcome_space, t):
        if self._cached_bid is not None:
            return self._cached_bid

        outcomes = self._sorted_outcomes(outcome_space)

        # First move: propose our best outcome
        if self._last_opponent_offer is None:
            bid = outcomes[0]
            self._my_bids.append(bid)
            self._cached_bid = bid
            return bid

        # Find index of opponent's last offer in our sorted list
        opp_idx = None
        for i, o in enumerate(outcomes):
            if o == self._last_opponent_offer:
                opp_idx = i
                break

        if opp_idx is None:
            # Opponent offer not in our list — stay at last bid
            last = self._my_bids[-1] if self._my_bids else outcomes[0]
            self._cached_bid = last
            return last

        # MiCRO: find the outcome at the SAME index as the opponent's offer
        # in our sorted list — this is the minimal concession.
        # i.e. if opponent offered the 300th best outcome for us,
        # we offer the 300th best outcome for them (which is the 300th
        # from the END of our list = index len-300).
        n = len(outcomes)
        mirror_idx = n - 1 - opp_idx  # mirror position
        mirror_idx = max(0, min(n - 1, mirror_idx))

        # Find the best outcome for us that is at least as good for
        # the opponent as the mirrored position
        target_opp_rank = mirror_idx / max(1, n - 1)

        # Walk from best-for-us, find first that meets opponent threshold
        for outcome in outcomes:
            opp_u = self._opp_rank(outcome, outcomes)
            if opp_u >= target_opp_rank:
                self._my_bids.append(outcome)
                self._cached_bid = outcome
                return outcome

        last = self._my_bids[-1] if self._my_bids else outcomes[0]
        self._cached_bid = last
        return last
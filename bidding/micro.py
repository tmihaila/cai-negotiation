class MiCROBidding:
    """
    MiCRO (Minimal Concession with Randomized Offers) Strategy.

    Algorithm:
    1. Maintain a sorted list of our own bids by descending utility.
    2. When opponent sends a new offer, make the MINIMAL concession:
       - If we can find a bid in our list that the opponent would prefer to their
         last offer, propose the highest-utility such bid (minimal concession).
       - Otherwise, stay at our current best bid (no concession needed yet).
    3. This is game-theoretically optimal in self-play and requires no opponent model.

    Simplified version:
    - Track all our proposed bids.
    - On each round, propose the bid with the highest self-utility that is
      at least as good for the opponent as their last offer to us.
    - If no such bid exists, propose our current best (no concession).
    """

    def __init__(self, ufun, opponent_model=None):
        self.ufun = ufun
        self.opponent_model = opponent_model  # Used if available to estimate opponent utility
        self._last_opponent_offer = None
        self._my_bids = []        # All bids we've made, sorted by our utility
        self._outcome_space = None
        self._all_outcomes = None

    def update_opponent_offer(self, offer):
        self._last_opponent_offer = offer

    def _build_outcome_list(self, outcome_space):
        """Build and cache a sorted list of all outcomes by our utility (descending)."""
        if self._all_outcomes is None:
            outcomes = list(outcome_space.enumerate_or_sample(500))
            self._all_outcomes = sorted(outcomes, key=lambda o: self.ufun(o), reverse=True)
        return self._all_outcomes

    def _opponent_utility_of(self, offer):
        """
        Estimate opponent's utility for an offer.
        Uses opponent model if available; falls back to our own ufun as proxy.
        """
        if self.opponent_model is not None:
            return self.opponent_model.estimate_utility(offer)
        # Without opponent model, use a uniform proxy: prefer outcomes where
        # our utility is lower (Pareto assumption: lower for us = better for them)
        return 1.0 - float(self.ufun(offer))

    def target_utility(self, t):
        # MiCRO doesn't use a target utility in the traditional sense
        return self.ufun.reserved_value

    def generate_bid(self, outcome_space, t):
        outcomes = self._build_outcome_list(outcome_space)

        if self._last_opponent_offer is None:
            # First move: propose our best offer
            best = outcomes[0] if outcomes else outcome_space.random_outcome()
            self._my_bids.append(best)
            return best

        # Estimate how good our last opponent offer is FOR THEM
        opp_threshold = self._opponent_utility_of(self._last_opponent_offer)

        # Find the highest-utility bid for us that the opponent would prefer
        # (i.e., their utility >= threshold from their last offer)
        best_for_us_acceptable = None
        for outcome in outcomes:
            if self._opponent_utility_of(outcome) >= opp_threshold:
                best_for_us_acceptable = outcome
                break  # outcomes sorted by our utility descending, so first match is best

        if best_for_us_acceptable is not None:
            self._my_bids.append(best_for_us_acceptable)
            return best_for_us_acceptable

        # No minimal concession possible: stay at current best bid
        if self._my_bids:
            return self._my_bids[-1]
        return outcomes[0] if outcomes else outcome_space.random_outcome()
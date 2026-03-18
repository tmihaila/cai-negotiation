from bidding.adaptive_bidding import AdaptiveBidding
from bidding.tit_for_tat import TitForTatBidding


class HybridBidding:
    """
    Deadline-Aware Hybrid Bidding Strategy.

    - First 80% of rounds: Adaptive bidding
      Exploits opponent's estimated concession limit to stay tough.
    - Last 20% of rounds: TitForTat bidding
      Mirrors opponent's concessions near deadline to converge faster.

    Motivated by:
    - Faratin et al. (1998): time-based concession functions
    - Baarslag (2014): deadline pressure and agreement failure analysis
    """

    def __init__(self, ufun, opponent_model, switch_time=0.8):
        self.ufun = ufun
        self.switch_time = switch_time
        self.adaptive = AdaptiveBidding(ufun, opponent_model)
        self.titfortat = TitForTatBidding(ufun)

    def update_opponent_history(self, offer):
        """Update both strategies — TitForTat needs history for when it kicks in."""
        self.adaptive.update_opponent_history(offer)
        self.titfortat.update_opponent_history(offer)

    def target_utility(self, t):
        if t < self.switch_time:
            return self.adaptive.target_utility(t)
        else:
            return self.titfortat.target_utility(t)

    def generate_bid(self, outcome_space, t):
        if t < self.switch_time:
            return self.adaptive.generate_bid(outcome_space, t)
        else:
            return self.titfortat.generate_bid(outcome_space, t)
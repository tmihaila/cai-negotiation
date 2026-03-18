import math


class PredictiveTitForTatBidding:
    """
    Predictive Tit-for-Tat Bidding Strategy.

    Instead of mirroring the opponent's LAST concession (reactive),
    uses a Gaussian Process to predict the opponent's NEXT concession
    and mirrors that instead (proactive).

    This addresses the known weakness of standard TitForTat described
    in Baarslag et al. (2014): being one step behind the opponent.

    Cite: Williams et al. (2012) - IAMhaggler2011 for GP prediction
          Baarslag et al. (2014) - for TitForTat limitation
    """

    def __init__(self, ufun, gp_model, sensitivity=1.0):
        self.ufun = ufun
        self.gp = gp_model               # GaussianProcessModel instance
        self.sensitivity = sensitivity
        self._my_last_utility = 1.0      # start at our best
        self._opponent_utility_history = []
        self._current_step = 0

    def update_opponent_history(self, offer, t):
        """
        Called once per round. Records opponent offer and updates GP model.
        Also updates our target utility based on predicted next concession.
        """
        if offer is None:
            return

        u = float(self.ufun(offer))
        self._opponent_utility_history.append(u)
        self._current_step = t

        # Update GP with this observation
        self.gp.update(offer, t)

        # Predict opponent's next concession using GP
        predicted_concession = self._predict_next_concession(t)

        # Mirror the predicted concession
        self._my_last_utility = max(
            self.ufun.reserved_value,
            self._my_last_utility - self.sensitivity * predicted_concession
        )

    def _predict_next_concession(self, t):
        """
        Predict how much the opponent will concede next round.

        Uses GP to predict opponent utility at t + delta,
        then computes the expected change from current utility.
        Falls back to last actual concession if GP has insufficient data.
        """
        history = self._opponent_utility_history

        # Need at least 3 points for GP to be meaningful
        if len(history) < 3:
            # Fall back to last actual concession (standard TfT)
            if len(history) >= 2:
                return history[-2] - history[-1]  # positive = they conceded
            return 0.0

        # Predict opponent utility one step ahead
        t_next = t + (1.0 / 100)  # one step ahead in normalized time
        predicted_u_next = self.gp.predict_next(t_next)

        if predicted_u_next is None:
            # GP failed — fall back to last concession
            return history[-2] - history[-1]

        # Predicted concession = current utility - predicted next utility
        # (positive means opponent is expected to give us more utility)
        current_u = history[-1]
        predicted_concession = current_u - predicted_u_next

        # Clamp to reasonable range — don't over-concede based on bad predictions
        return max(-0.1, min(0.2, predicted_concession))

    def target_utility(self, t):
        """Read-only. Returns current target utility."""
        return self._my_last_utility

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
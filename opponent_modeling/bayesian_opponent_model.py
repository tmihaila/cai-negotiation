import math
import random


class BayesianOpponentModel:
    """
    Bayesian Opponent Modeling.

    Maintains a set of hypothesis utility functions for the opponent.
    Each hypothesis H_i is a weight vector over issues.
    We update P(H_i | observations) using Bayes' rule.

    P(H_i | offer) ∝ P(offer | H_i) * P(H_i)

    P(offer | H_i) is modeled as proportional to exp(U_Hi(offer)),
    i.e., higher-utility offers under H_i are more likely to be proposed.
    """

    def __init__(self, issues, n_hypotheses=20, seed=42):
        self.issues = issues
        self.issue_names = [issue.name for issue in issues]
        rng = random.Random(seed)

        # Generate random weight vectors as hypotheses
        self.hypotheses = []
        for _ in range(n_hypotheses):
            weights = [rng.random() for _ in issues]
            total = sum(weights)
            weights = [w / total for w in weights]
            self.hypotheses.append(weights)

        # Uniform prior
        self.priors = [1.0 / n_hypotheses] * n_hypotheses
        self._offer_history = []

    def _utility_under_hypothesis(self, offer, hypothesis_weights):
        """
        Compute a simple weighted sum utility for a given offer under hypothesis H.
        Uses relative value position within the issue range.
        """
        utility = 0.0
        for i, (issue, value) in enumerate(zip(self.issues, offer)):
            # Normalize value to [0, 1] within issue range
            try:
                vals = list(issue.all)
                if len(vals) > 1:
                    idx = vals.index(value)
                    norm = idx / (len(vals) - 1)
                else:
                    norm = 1.0
            except (AttributeError, ValueError):
                norm = 0.5
            utility += hypothesis_weights[i] * norm
        return utility

    def update(self, offer):
        """Update posterior after observing the opponent's offer."""
        if offer is None:
            return
        self._offer_history.append(offer)

        # Compute likelihoods: P(offer | H_i) = softmax-like score
        likelihoods = []
        for weights in self.hypotheses:
            u = self._utility_under_hypothesis(offer, weights)
            likelihoods.append(math.exp(u))  # Higher-utility offers more likely

        # Bayes update
        new_priors = []
        for p, l in zip(self.priors, likelihoods):
            new_priors.append(p * l)

        total = sum(new_priors)
        if total > 0:
            self.priors = [p / total for p in new_priors]
        # else: keep old priors (numerical stability)

    def _expected_weights(self):
        """
        Compute expected issue weights over all hypotheses weighted by posterior.
        E[w_i] = sum_H P(H) * w_i(H)
        """
        n_issues = len(self.issues)
        expected = [0.0] * n_issues
        for h_idx, weights in enumerate(self.hypotheses):
            for i in range(n_issues):
                expected[i] += self.priors[h_idx] * weights[i]
        return expected

    def estimate_utility(self, offer):
        """
        Estimate opponent utility for an offer using expected weights.
        """
        expected_w = self._expected_weights()
        return self._utility_under_hypothesis(offer, expected_w)

    def most_likely_hypothesis(self):
        """Return the hypothesis with the highest posterior probability."""
        best_idx = max(range(len(self.priors)), key=lambda i: self.priors[i])
        return self.hypotheses[best_idx]
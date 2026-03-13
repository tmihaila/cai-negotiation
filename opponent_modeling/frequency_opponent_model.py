class FrequencyOpponentModel:
    """
    Frequency Analysis Opponent Model.

    Assumes:
    1. An agent values options it proposes more often (value frequency → weight).
    2. Issues with many different proposed values have lower importance (issue weight).

    Provides:
    - estimate_value_weight(issue, value): How much the opponent prefers this value.
    - estimate_issue_weight(issue): How important this issue is to the opponent.
    - estimate_utility(offer): Full utility estimate for an offer.
    """

    def __init__(self, issues):
        self.issues = issues
        self.issue_names = [issue.name for issue in issues]
        self.value_counts = {issue.name: {} for issue in issues}
        self.total_offers = 0

    def update(self, offer):
        if offer is None:
            return
        self.total_offers += 1
        for issue, value in zip(self.issues, offer):
            name = issue.name
            self.value_counts[name][value] = self.value_counts[name].get(value, 0) + 1

    def estimate_value_weight(self, issue_name, value):
        """
        Frequency of this value / total offers for this issue.
        Higher frequency = opponent prefers this value.
        """
        counts = self.value_counts.get(issue_name, {})
        total = sum(counts.values())
        if total == 0:
            return 0.0
        return counts.get(value, 0) / total

    def estimate_issue_weight(self, issue_name):
        """
        Issues where the opponent always proposes the SAME value are highly important.
        Issues where they vary a lot are less important.
        Weight = 1 / number_of_distinct_values_proposed (normalized).
        """
        counts = self.value_counts.get(issue_name, {})
        n_distinct = max(1, len(counts))
        raw = 1.0 / n_distinct
        return raw

    def _normalized_issue_weights(self):
        raws = {name: self.estimate_issue_weight(name) for name in self.issue_names}
        total = sum(raws.values())
        if total == 0:
            n = len(self.issue_names)
            return {name: 1.0 / n for name in self.issue_names}
        return {name: v / total for name, v in raws.items()}

    def estimate_utility(self, offer):
        """
        Estimate the opponent's utility for a given offer.
        U(offer) = sum over issues of: issue_weight * value_weight
        """
        if self.total_offers == 0:
            return 0.5  # No data yet
        weights = self._normalized_issue_weights()
        utility = 0.0
        for issue, value in zip(self.issues, offer):
            name = issue.name
            vw = self.estimate_value_weight(name, value)
            utility += weights[name] * vw
        return utility

    def estimate_preference(self, issue_name, value):
        """Backwards-compat alias."""
        return self.estimate_value_weight(issue_name, value)
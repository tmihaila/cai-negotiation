class OpponentModel:

    def __init__(self, issues):
        self.issues = issues
        self.value_counts = {issue.name: {} for issue in issues}

    def update(self, offer):
        for issue, value in offer.items():
            if value not in self.value_counts[issue]:
                self.value_counts[issue][value] = 0
            self.value_counts[issue][value] += 1

    def estimate_preference(self, issue, value):
        return self.value_counts.get(issue, {}).get(value, 0)
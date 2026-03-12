class OpponentModel:

    def __init__(self, issues):
        self.issues = issues
        self.value_counts = {issue.name: {} for issue in issues}

    def update(self, offer):

        for issue, value in zip(self.issues, offer):

            issue_name = issue.name

            if value not in self.value_counts[issue_name]:
                self.value_counts[issue_name][value] = 0

            self.value_counts[issue_name][value] += 1


    def estimate_preference(self, issue, value):
        return self.value_counts.get(issue, {}).get(value, 0)
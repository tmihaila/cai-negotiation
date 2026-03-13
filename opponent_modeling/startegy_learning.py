import math
import random


class LinearExtrapolationModel:
    """
    Strategy Learning via Linear Extrapolation.

    Predicts the opponent's NEXT offer utility by fitting a linear trend
    to their recent utility history (from our perspective).

    Use case: helps adaptive and TfT strategies anticipate where the
    opponent is heading so we can respond accordingly.
    """

    def __init__(self, ufun):
        self.ufun = ufun
        self._history = []  # Utility of opponent offers over time

    def update(self, offer):
        if offer is not None:
            self._history.append(self.ufun(offer))

    def predict_next(self):
        """
        Predict the next opponent offer utility via linear regression on history.
        Returns None if insufficient data.
        """
        n = len(self._history)
        if n < 2:
            return None

        xs = list(range(n))
        ys = self._history
        x_mean = sum(xs) / n
        y_mean = sum(ys) / n

        num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
        den = sum((x - x_mean) ** 2 for x in xs)

        slope = num / den if den != 0 else 0
        intercept = y_mean - slope * x_mean

        predicted = slope * n + intercept  # Predict at step n (next step)
        return max(0.0, min(1.0, predicted))

    def estimate_utility(self, offer):
        """Fallback: use our own ufun as proxy (no direct utility model)."""
        return float(self.ufun(offer))


class GaussianProcessModel:
    """
    Strategy Learning via Gaussian Process Regression.

    Models opponent utility over time as a GP and predicts future offers.
    Uses a simple RBF kernel with noise.

    Note: Pure Python implementation (no scipy/sklearn) for portability.
    This is a simplified version; for production, use sklearn.gaussian_process.
    """

    def __init__(self, ufun, length_scale=5.0, noise=0.01):
        self.ufun = ufun
        self.length_scale = length_scale
        self.noise = noise
        self._X = []  # Time steps
        self._y = []  # Utility values

    def _rbf_kernel(self, x1, x2):
        return math.exp(-((x1 - x2) ** 2) / (2 * self.length_scale ** 2))

    def _kernel_matrix(self, X):
        n = len(X)
        K = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                K[i][j] = self._rbf_kernel(X[i], X[j])
                if i == j:
                    K[i][j] += self.noise
        return K

    def _solve(self, K, y):
        """Solve K * alpha = y using simple Gaussian elimination (no numpy)."""
        n = len(y)
        # Augmented matrix [K | y]
        aug = [row[:] + [y[i]] for i, row in enumerate(K)]

        for col in range(n):
            # Find pivot
            max_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
            aug[col], aug[max_row] = aug[max_row], aug[col]

            pivot = aug[col][col]
            if abs(pivot) < 1e-10:
                continue

            for row in range(n):
                if row != col:
                    factor = aug[row][col] / pivot
                    for k in range(col, n + 1):
                        aug[row][k] -= factor * aug[col][k]

            for k in range(col, n + 1):
                aug[col][k] /= pivot

        return [aug[i][n] for i in range(n)]

    def update(self, offer, t):
        """Record opponent offer at timestep t."""
        if offer is not None:
            self._X.append(float(t))
            self._y.append(float(self.ufun(offer)))

    def predict_next(self, t_next):
        """
        Predict opponent utility at time t_next using GP posterior mean.
        """
        if len(self._X) < 2:
            return None

        K = self._kernel_matrix(self._X)
        try:
            alpha = self._solve(K, self._y)
        except Exception:
            return None

        # Compute k* (kernel between training points and t_next)
        k_star = [self._rbf_kernel(x, t_next) for x in self._X]

        prediction = sum(a * k for a, k in zip(alpha, k_star))
        return max(0.0, min(1.0, prediction))

    def estimate_utility(self, offer):
        return float(self.ufun(offer))
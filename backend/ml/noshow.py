import numpy as np
from sklearn.linear_model import LogisticRegression

# Synthetic bootstrap data: [attendance_rate, missed_count, days_since_last_visit]
# Replace with real appointment history once enough data exists.
_rng = np.random.default_rng(42)
_X = np.column_stack([_rng.uniform(0, 1, 600), _rng.integers(0, 8, 600), _rng.integers(1, 365, 600)])
_p = 1 / (1 + np.exp(-(-1.5 - 4 * _X[:, 0] + 1.2 * _X[:, 1] + 0.004 * _X[:, 2])))
_y = (_rng.uniform(0, 1, 600) < _p).astype(int)
_model = LogisticRegression().fit(_X, _y)

def predict_noshow(attendance_rate: float, missed: int, days_since_last: int) -> float:
    """Return probability (0-1) that the patient misses the appointment."""
    return float(_model.predict_proba([[attendance_rate, missed, days_since_last]])[0][1])

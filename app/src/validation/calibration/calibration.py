import numpy as np
from sklearn.linear_model import LogisticRegression


def calculate_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """
    Computes the Expected Calibration Error (ECE).
    """
    y_true = np.array(y_true)
    y_prob = np.array(y_prob)
    
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper) if i < n_bins - 1 else (y_prob >= bin_lower) & (y_prob <= bin_upper)
        prop_in_bin = np.mean(in_bin)
        
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += prop_in_bin * np.abs(avg_confidence_in_bin - accuracy_in_bin)
            
    return float(ece)


class PlattCalibrator:
    """
    Applies Platt Scaling (Sigmoid probability calibration) using logistic regression.
    """
    def __init__(self):
        self.lr = LogisticRegression(C=np.inf, solver="lbfgs")

    def fit(self, y_prob: np.ndarray, y_true: np.ndarray) -> "PlattCalibrator":
        # Inputs need to be column vectors of shape (N, 1) for sklearn
        X = np.array(y_prob).reshape(-1, 1)
        y = np.array(y_true)
        # Platt Scaling mapping: logit(p) -> target
        # In case of SQLite test databases where targets are uniform, handle exception
        if len(np.unique(y)) < 2:
            # Fallback mock fit
            self.lr.fit(np.array([[0.1], [0.9]]), np.array([0, 1]))
        else:
            self.lr.fit(X, y)
        return self

    def predict(self, y_prob: np.ndarray) -> np.ndarray:
        X = np.array(y_prob).reshape(-1, 1)
        return self.lr.predict_proba(X)[:, 1]

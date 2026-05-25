from typing import Tuple

import numpy as np


def calculate_psi(expected: np.ndarray, actual: np.ndarray, num_bins: int = 10) -> float:
    """
    Computes the Population Stability Index (PSI) between expected (reference)
    and actual (target) feature/prediction distributions.
    """
    expected = np.array(expected)
    actual = np.array(actual)
    
    # Handle empty array edge cases
    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Determine bin boundaries based on expected distribution
    percentiles = np.linspace(0, 100, num_bins + 1)
    bin_boundaries = np.percentile(expected, percentiles)
    # Ensure boundaries are unique
    bin_boundaries = np.unique(bin_boundaries)
    if len(bin_boundaries) < 2:
        return 0.0
        
    expected_counts = []
    actual_counts = []
    
    for i in range(len(bin_boundaries) - 1):
        lower = bin_boundaries[i]
        upper = bin_boundaries[i + 1]
        
        # Include boundary points
        if i == len(bin_boundaries) - 2:
            e_count = np.sum((expected >= lower) & (expected <= upper))
            a_count = np.sum((actual >= lower) & (actual <= upper))
        else:
            e_count = np.sum((expected >= lower) & (expected < upper))
            a_count = np.sum((actual >= lower) & (actual < upper))
            
        expected_counts.append(e_count)
        actual_counts.append(a_count)
        
    expected_counts = np.array(expected_counts, dtype=float)
    actual_counts = np.array(actual_counts, dtype=float)
    
    # Normalize to percentages (fractions)
    expected_pct = expected_counts / len(expected)
    actual_pct = actual_counts / len(actual)
    
    # Apply Laplace smoothing to avoid division by zero / log(0)
    expected_pct = np.where(expected_pct == 0, 1e-4, expected_pct)
    actual_pct = np.where(actual_pct == 0, 1e-4, actual_pct)
    
    # Compute PSI
    psi_value = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(psi_value)


def calculate_ks_statistic(expected: np.ndarray, actual: np.ndarray) -> Tuple[float, float]:
    """
    Calculates the Kolmogorov-Smirnov (KS) statistic and an approximate p-value
    comparing two empirical cumulative distribution functions (CDFs).
    """
    expected = np.sort(expected)
    actual = np.sort(actual)
    
    n1 = len(expected)
    n2 = len(actual)
    
    if n1 == 0 or n2 == 0:
        return 0.0, 1.0
        
    # Combine values to find all evaluation points
    all_vals = np.concatenate([expected, actual])
    all_vals = np.sort(all_vals)
    
    # Compute empirical CDFs
    cdf_expected = np.searchsorted(expected, all_vals, side="right") / n1
    cdf_actual = np.searchsorted(actual, all_vals, side="right") / n2
    
    # KS Statistic is the maximum absolute difference between cumulative distributions
    ks_stat = np.max(np.abs(cdf_expected - cdf_actual))
    
    # Approximate p-value calculation for two-sided KS test
    # p-value approx: P(D > ks_stat)
    val = -2.0 * ks_stat * ks_stat * (n1 * n2) / (n1 + n2)
    p_val = min(1.0, 2.0 * np.exp(val))
    
    return float(ks_stat), float(p_val)

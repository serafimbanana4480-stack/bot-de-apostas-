import logging
import os
import sys
from typing import Any, Dict

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss

# Append parent path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("test_stationarity")

def perform_stationarity_tests(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Performs ADF and KPSS tests on each feature column in the dataframe.
    Returns a dictionary summarizing p-values and test results.
    """
    results = {}
    
    # Only test numeric columns with sufficient variance
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    print("\n=== FEATURE STATIONARITY TEST REPORT ===")
    print(f"Testing {len(numeric_cols)} numeric features for stationarity...")
    print(f"{'Feature Name':<35} | {'ADF p-value':<12} | {'KPSS p-value':<13} | {'Status':<10}")
    print("-" * 80)
    
    for col in numeric_cols:
        series = df[col].dropna()
        
        # Skip constant columns or very short series
        if series.nunique() <= 1 or len(series) < 10:
            continue
            
        try:
            # ADF Test: H0 = has unit root (non-stationary)
            adf_res = adfuller(series, maxlag=None, regression='c', autolag='AIC')
            adf_p = adf_res[1]
            
            # KPSS Test: H0 = is trend/level stationary
            # We suppress warnings from kpss since short series might trigger p-value interpolation warnings
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                kpss_res = kpss(series, regression='c', nlags='auto')
            kpss_p = kpss_res[1]
            
            # Criteria:
            # ADF rejects H0 (p < 0.05) => Stationary
            # KPSS fails to reject H0 (p > 0.05) => Stationary
            is_adf_stationary = adf_p < 0.05
            is_kpss_stationary = kpss_p > 0.05
            
            status = "STATIONARY" if (is_adf_stationary and is_kpss_stationary) else "DRIFTING"
            
            results[col] = {
                "adf_p": adf_p,
                "kpss_p": kpss_p,
                "status": status
            }
            
            print(f"{col:<35} | {adf_p:<12.4f} | {kpss_p:<13.4f} | {status:<10}")
            
        except Exception as e:
            logger.debug(f"Could not test stationarity for {col}: {e}")
            
    return results

if __name__ == "__main__":
    
    # Quick execution fallback: run stationarity check on synthetic historical data if database is empty
    # Set up some dummy time-series features
    np.random.seed(42)
    n_days = 100
    dates = pd.date_range("2026-01-01", periods=n_days)
    
    dummy_data = pd.DataFrame({
        "elo_diff": np.random.normal(0, 15, size=n_days).cumsum(), # Drifting/Random Walk
        "win_rate_5_diff": np.random.normal(0, 0.1, size=n_days), # Stationary (returns/differenced)
        "rest_diff": np.random.randint(-3, 4, size=n_days), # Stationary
        "market_overround": np.random.normal(0.04, 0.005, size=n_days) # Stationary
    }, index=dates)
    
    perform_stationarity_tests(dummy_data)

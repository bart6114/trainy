"""Morton's 3-parameter critical power model for eFTP estimation."""

from typing import Optional

import numpy as np
from scipy.optimize import curve_fit


def morton_3p_model(t: np.ndarray, cp: float, w_prime: float, tau: float) -> np.ndarray:
    """Morton's 3-parameter critical power model.

    P(t) = CP + W' / (t - τ)
    """
    return cp + w_prime / (t - tau)


def fit_critical_power(
    durations: list[float],  # seconds
    powers: list[float],  # watts
) -> Optional[dict]:
    """Fit Morton's 3-parameter model to power-duration data.

    Returns dict with cp, w_prime, tau, r_squared or None if fitting fails.
    """
    if len(durations) < 3 or len(powers) < 3:
        return None

    t = np.array(durations, dtype=float)
    p = np.array(powers, dtype=float)

    # Initial guesses
    cp_guess = min(powers) * 0.9  # CP should be below shortest effort
    w_prime_guess = 20000  # ~20 kJ typical
    tau_guess = -5  # Small negative value

    try:
        params, covariance = curve_fit(
            morton_3p_model,
            t,
            p,
            p0=[cp_guess, w_prime_guess, tau_guess],
            bounds=([50, 1000, -60], [500, 50000, 0]),  # Reasonable bounds
            maxfev=5000,
        )

        cp, w_prime, tau = params

        # Calculate R²
        predicted = morton_3p_model(t, cp, w_prime, tau)
        ss_res = np.sum((p - predicted) ** 2)
        ss_tot = np.sum((p - np.mean(p)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        return {
            "cp": round(cp, 1),
            "w_prime": round(w_prime, 0),
            "tau": round(tau, 2),
            "r_squared": round(r_squared, 4),
        }
    except Exception:
        return None


def estimate_ftp_with_fallback(
    durations: list[float],
    powers: list[float],
    best_20min: Optional[float] = None,
) -> tuple[Optional[int], Optional[int], str]:
    """Estimate FTP using CP model with fallback to 95% method.

    Returns: (eftp, w_prime, method_used)
    """
    # Try Morton 3-parameter model first
    result = fit_critical_power(durations, powers)

    if result and result["r_squared"] > 0.95:
        return int(result["cp"]), int(result["w_prime"]), "morton_3p"

    # Fallback to 95% of 20-min power
    if best_20min:
        return int(best_20min * 0.95), None, "20min_95pct"

    return None, None, "none"

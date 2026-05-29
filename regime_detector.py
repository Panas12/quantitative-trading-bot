"""
Regime Detection Module - Hidden Markov Model

Uses HMM to detect market regimes and filter trading signals.
Only trades during mean-reverting regimes, stays in cash during trending/volatile periods.

Regimes:
1. MEAN_REVERTING - Spread oscillates around mean (TRADE)
2. TRENDING - Spread drifts in one direction (NO TRADE)
3. VOLATILE - Explosive moves (NO TRADE)
"""

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    Detect market regimes using Hidden Markov Model.
    
    Uses 3-state HMM to classify spread behavior:
    - Low volatility, zero mean = MEAN_REVERTING
    - Non-zero mean = TRENDING  
    - High volatility = VOLATILE
    """
    
    def __init__(self, n_regimes: int = 3, random_state: int = 42):
        """
        Initialize regime detector.
        
        Args:
            n_regimes: Number of hidden states (default: 3)
            random_state: Random seed for reproducibility
        """
        self.n_regimes = n_regimes
        self.model = GaussianHMM(
            n_components=n_regimes,
            covariance_type="full",
            n_iter=1000,
            random_state=random_state,
            verbose=False
        )
        self.regime_names = {}
        self.fitted = False
        
    def train(self, spread_returns: pd.Series, min_samples: int = 100):
        """
        Train HMM on historical spread returns.
        
        Args:
            spread_returns: Spread return series (pct_change)
            min_samples: Minimum samples required for training
        """
        if len(spread_returns) < min_samples:
            raise ValueError(f"Need at least {min_samples} samples, got {len(spread_returns)}")
        
        # Remove NaN and infinite values
        clean_returns = spread_returns.dropna().replace([np.inf, -np.inf], np.nan).dropna()
        
        if len(clean_returns) < min_samples:
            raise ValueError(f"After cleaning, only {len(clean_returns)} samples remain")
        
        # Reshape for HMM (needs 2D array)
        X = clean_returns.values.reshape(-1, 1)
        
        logger.info(f"Training HMM on {len(X)} samples...")
        
        # Fit model
        self.model.fit(X)
        
        # Classify regimes based on learned parameters
        self._classify_regimes()
        
        self.fitted = True
        logger.info("HMM training complete")
        logger.info(f"Regime classification: {self.regime_names}")
        
    def _classify_regimes(self):
        """
        Classify the learned hidden states into regime types.
        
        Based on:
        - Mean (μ) - trending if |μ| is large
        - Variance (σ²) - volatile if σ² is large
        - Mean-reverting if low variance and μ ≈ 0
        """
        means = self.model.means_.flatten()
        variances = self.model.covars_.flatten()
        
        # Calculate z-scores for means (how far from zero)
        mean_magnitude = np.abs(means)
        
        # Identify regimes
        regime_chars = []
        
        for i in range(self.n_regimes):
            if variances[i] > np.median(variances) * 2:
                # High volatility
                regime_chars.append(('VOLATILE', i, means[i], variances[i]))
            elif mean_magnitude[i] > np.std(means):
                # Non-zero mean = trending
                regime_chars.append(('TRENDING', i, means[i], variances[i]))
            else:
                # Low variance, zero mean = mean-reverting
                regime_chars.append(('MEAN_REVERTING', i, means[i], variances[i]))
        
        # Map state indices to regime names
        self.regime_names = {char[1]: char[0] for char in regime_chars}
        
        # Log regime characteristics
        for name, idx, mean, var in regime_chars:
            logger.info(f"  State {idx} ({name}): μ={mean:.6f}, σ²={var:.6f}")
    
    def predict_regime(self, recent_returns: pd.Series) -> str:
        """
        Predict current regime based on recent returns.
        
        Args:
            recent_returns: Recent spread returns (last 20-30 observations)
            
        Returns:
            Regime name ('MEAN_REVERTING', 'TRENDING', or 'VOLATILE')
        """
        if not self.fitted:
            raise RuntimeError("Model not fitted. Call train() first.")
        
        # Clean data
        clean_returns = recent_returns.dropna().replace([np.inf, -np.inf], np.nan).dropna()
        
        if len(clean_returns) == 0:
            logger.warning("No valid data for regime prediction, defaulting to VOLATILE")
            return 'VOLATILE'
        
        # Reshape for prediction
        X = clean_returns.values.reshape(-1, 1)
        
        # Predict hidden state
        predicted_states = self.model.predict(X)
        
        # Get most recent state
        current_state = predicted_states[-1]
        
        # Map to regime name
        regime = self.regime_names.get(current_state, 'UNKNOWN')
        
        return regime
    
    def predict_regime_probabilities(self, recent_returns: pd.Series) -> Dict[str, float]:
        """
        Get probability distribution over regimes.
        
        Args:
            recent_returns: Recent spread returns
            
        Returns:
            Dictionary mapping regime names to probabilities
        """
        if not self.fitted:
            raise RuntimeError("Model not fitted. Call train() first.")
        
        # Clean data
        clean_returns = recent_returns.dropna().replace([np.inf, -np.inf], np.nan).dropna()
        
        if len(clean_returns) == 0:
            return {'MEAN_REVERTING': 0.0, 'TRENDING': 0.0, 'VOLATILE': 1.0}
        
        # Reshape
        X = clean_returns.values.reshape(-1, 1)
        
        # Get state probabilities (posterior)
        posteriors = self.model.predict_proba(X)
        
        # Use most recent observation
        current_probs = posteriors[-1]
        
        # Map to regime names
        regime_probs = {}
        for state_idx, prob in enumerate(current_probs):
            regime_name = self.regime_names.get(state_idx, f'STATE_{state_idx}')
            regime_probs[regime_name] = prob
        
        return regime_probs
    
    def should_trade(self, recent_returns: pd.Series, 
                     threshold: float = 0.6) -> bool:
        """
        Determine if we should trade based on current regime.
        
        Args:
            recent_returns: Recent spread returns
            threshold: Minimum probability of MEAN_REVERTING to trade
            
        Returns:
            True if should trade, False otherwise
        """
        regime_probs = self.predict_regime_probabilities(recent_returns)
        
        mean_rev_prob = regime_probs.get('MEAN_REVERTING', 0.0)
        
        logger.debug(f"Regime probabilities: {regime_probs}")
        logger.debug(f"Mean-reverting probability: {mean_rev_prob:.2%}")
        
        return mean_rev_prob >= threshold
    
    def get_regime_history(self, spread_returns: pd.Series) -> pd.DataFrame:
        """
        Get full regime classification history.
        
        Useful for backtesting and visualization.
        
        Args:
            spread_returns: Full spread return series
            
        Returns:
            DataFrame with columns: date, regime, probabilities
        """
        if not self.fitted:
            raise RuntimeError("Model not fitted. Call train() first.")
        
        # Clean data
        clean_returns = spread_returns.dropna().replace([np.inf, -np.inf], np.nan).dropna()
        
        # Reshape
        X = clean_returns.values.reshape(-1, 1)
        
        # Predict states
        states = self.model.predict(X)
        posteriors = self.model.predict_proba(X)
        
        # Create DataFrame
        results = pd.DataFrame(index=clean_returns.index)
        results['regime'] = [self.regime_names.get(s, 'UNKNOWN') for s in states]
        
        # Add probabilities for each regime type
        for regime_type in ['MEAN_REVERTING', 'TRENDING', 'VOLATILE']:
            # Find state index for this regime
            state_idx = [k for k, v in self.regime_names.items() if v == regime_type]
            if state_idx:
                results[f'{regime_type}_prob'] = posteriors[:, state_idx[0]]
            else:
                results[f'{regime_type}_prob'] = 0.0
        
        return results


if __name__ == '__main__':
    # Test the regime detector
    from data_fetcher import DataFetcher
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    print("\n" + "="*70)
    print("TESTING REGIME DETECTOR")
    print("="*70 + "\n")
    
    # Fetch data
    print("1. Fetching USO-XLE data...")
    fetcher = DataFetcher('USO', 'XLE')
    data1, data2 = fetcher.fetch_data(start_date='2023-01-01')
    
    # Calculate spread
    print("2. Calculating spread...")
    from statsmodels.regression.linear_model import OLS
    X = data2['close'].values.reshape(-1, 1)
    y = data1['close'].values
    model = OLS(y, X).fit()
    hedge_ratio = model.params[0]
    
    spread = data1['close'] - hedge_ratio * data2['close']
    spread_returns = spread.pct_change().dropna()
    
    print(f"   Hedge ratio: {hedge_ratio:.4f}")
    print(f"   Spread samples: {len(spread)}")
    
    # Train regime detector
    print("\n3. Training regime detector...")
    detector = RegimeDetector()
    detector.train(spread_returns)
    
    # Get regime history
    print("\n4. Analyzing regime history...")
    regime_history = detector.get_regime_history(spread_returns)
    
    # Print statistics
    print("\nRegime Distribution:")
    regime_counts = regime_history['regime'].value_counts()
    for regime, count in regime_counts.items():
        pct = 100 * count / len(regime_history)
        print(f"  {regime}: {count} days ({pct:.1f}%)")
    
    # Test recent prediction
    print("\n5. Testing recent regime prediction...")
    recent_returns = spread_returns.tail(30)
    current_regime = detector.predict_regime(recent_returns)
    regime_probs = detector.predict_regime_probabilities(recent_returns)
    
    print(f"\nCurrent Regime: {current_regime}")
    print("Probabilities:")
    for regime, prob in regime_probs.items():
        print(f"  {regime}: {prob:.1%}")
    
    should_trade = detector.should_trade(recent_returns, threshold=0.6)
    print(f"\nShould Trade: {'YES' if should_trade else 'NO'}")
    
    print("\n" + "="*70)
    print("✓ Test complete!")
    print("="*70)

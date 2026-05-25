"""
Ensemble models for combining multiple prediction models.
"""
from src.ml.ensemble.base import EnsembleModel

# Lazy imports — only load if dependencies are available
try:
    from src.ml.ensemble.stacking import StackingEnsemble
    from src.ml.ensemble.voting import VotingEnsemble
    __all__ = ["EnsembleModel", "StackingEnsemble", "VotingEnsemble"]
except ImportError:
    __all__ = ["EnsembleModel"]

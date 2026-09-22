"""Leakage-safe research model implementations.

Phase 2 deliberately starts with an interpretable fixed factor score and a
regularised linear model. The module has no dependency on legacy trading or
GUI packages.
"""

from .base import ModelInputError, ModelNotFittedError, ResearchModel
from .factor_score import FactorScoreModel
from .ridge import RidgeResearchModel

__all__ = [
    "FactorScoreModel",
    "ModelInputError",
    "ModelNotFittedError",
    "ResearchModel",
    "RidgeResearchModel",
]

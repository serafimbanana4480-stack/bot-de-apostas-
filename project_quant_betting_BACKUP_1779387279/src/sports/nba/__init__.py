"""
NBA Implementation.
Migrating the original monolithic logic into the specific NBA domain.
Includes specific feature builders (Form, Context, Market, Lookahead) heavily tied to Basketball.
"""
from src.core.interfaces import BaseSport

class NBASport(BaseSport):
    @property
    def name(self) -> str:
        return "NBA"
        
    def get_ingestion_pipeline(self):
        # NBA API, Betfair, Odds API integrations
        pass
        
    def get_feature_engineer(self):
        # Back-to-backs, points diff, three-point %
        pass
        
    def get_model_trainer(self):
        # XGBoost, LightGBM Ensemble for Moneyline/Spread
        pass

import logging

import pandas as pd
from xgboost import XGBClassifier


class UFCXGBoostModel:
    """
    XGBoost classification model specifically tuned for UFC Moneyline predictions.
    Utilizes high regularization (alpha, lambda) and shallow trees to prevent overfitting 
    on small UFC datasets.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = XGBClassifier(**self.get_params())
        
    def get_params(self):
        """Default conservative params for UFC."""
        return {
            'max_depth': 3,
            'learning_rate': 0.01,
            'n_estimators': 300,
            'reg_alpha': 10.0,
            'reg_lambda': 10.0,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': 'binary:logistic',
            'random_state': 42
        }

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """
        Trains the XGBoost model on historical UFC bouts.
        """
        self.logger.info("Fitting XGBoost model on UFC data...")
        self.model.fit(X, y)

    def predict_proba(self, X: pd.DataFrame):
        """
        Predicts the probability of fighter 1 (Red Corner usually) winning.
        """
        self.logger.info("Predicting probabilities for UFC bouts...")
        return self.model.predict_proba(X)

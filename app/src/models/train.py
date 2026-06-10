import logging
import os

import sys
from typing import Any, Dict, Tuple

import mlflow
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.calibration import IsotonicRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

# Append parent path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.validation.splits import PurgedWalkForwardCV

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("train")

class ModelTrainer:
    """
    Handles training of the primary model (XGBoost), probability calibration (Isotonic),
    and the secondary filtering model (Meta-Labeling).
    Integrates with MLflow for tracking.
    Supports both logloss and CLV-based objectives.
    """
    def __init__(
        self,
        n_splits: int = 5,
        mlflow_tracking_uri: str = "http://localhost:5000",
        objective: str = "logloss",
    ):
        self.n_splits = n_splits
        self.cv = PurgedWalkForwardCV(n_splits=n_splits)
        self.objective = objective  # "logloss" or "clv"
        
        # Configure MLflow
        try:
            mlflow.set_tracking_uri(mlflow_tracking_uri)
            mlflow.set_experiment("nba_value_betting")
        except Exception as e:
            logger.warning(f"Could not connect to MLflow tracking server: {e}. Using local runs.")

    def prepare_data(self, features_df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray, pd.Series]:
        """
        Extracts features matrix (X), target array (y), and metadata columns.
        """
        # Explode the 'features_data' column containing dictionary into individual columns
        feats_list = features_df["features_data"].tolist()
        X = pd.DataFrame(feats_list, index=features_df.index)
        
        # Keep track of game date for validation split
        X["game_date"] = features_df["calculated_at"]
        y = features_df["target"].values
        game_ids = features_df["game_id"]
        
        return X, y, game_ids

    def train_pipeline(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs the full train, calibration, meta-labeling, and log flow.
        """
        logger.info("Initializing Model Training Pipeline...")
        X, y, game_ids = self.prepare_data(features_df)
        
        # Split indexes
        splits = self.cv.split(X)
        
        oof_preds = np.zeros(len(X))
        calibrated_oof_preds = np.zeros(len(X))
        meta_targets = np.zeros(len(X))
        meta_oof_preds = np.zeros(len(X))
        
        models = []
        calibrators = []
        meta_models = []
        
        feature_cols = [c for c in X.columns if c != "game_date"]
        
        with mlflow.start_run():
            # Log primary parameters
            mlflow.log_param("n_splits", self.n_splits)
            mlflow.log_param("primary_model_type", "XGBClassifier")
            mlflow.log_param("secondary_model_type", "Meta-Labeling XGB")
            mlflow.log_param("objective", self.objective)
            
            # Step 1: Walk-forward Cross-Validation Loop
            for fold, (train_idx, val_idx) in enumerate(splits):
                logger.info(f"Training Fold {fold+1} (objective={self.objective})...")
                
                X_train, y_train = X.iloc[train_idx][feature_cols], y[train_idx]
                X_val, y_val = X.iloc[val_idx][feature_cols], y[val_idx]
                
                # Check for missing labels in train/validation
                if len(np.unique(y_train)) < 2:
                    logger.warning(f"Fold {fold+1} skipped due to uniform labels in training split.")
                    continue
                
                # Fit Primary Model — choose objective
                if self.objective == "clv" and "odds_home" in X_train.columns:
                    # CLV objective: use custom XGBoost objective with odds data
                    from src.ml.training.clv_metrics import clv_eval_metric
                    from src.ml.training.clv_objective import clv_xgb_objective
                    
                    # Build DMatrix with odds info for CLV training
                    dtrain = xgb.DMatrix(X_train, label=y_train)
                    dval = xgb.DMatrix(X_val, label=y_val)
                    
                    # Set opening/closing odds as float_info
                    opening_odds_train = X_train["odds_home"].values
                    closing_odds_train = X_train["odds_home"].values
                    if "closing_odds_home" in X_train.columns:
                        closing_odds_train = X_train["closing_odds_home"].values
                    
                    opening_odds_val = X_val["odds_home"].values
                    closing_odds_val = X_val["odds_home"].values
                    if "closing_odds_home" in X_val.columns:
                        closing_odds_val = X_val["closing_odds_home"].values
                    
                    dtrain.set_float_info('opening_odds', opening_odds_train)
                    dtrain.set_float_info('closing_odds', closing_odds_train)
                    dval.set_float_info('opening_odds', opening_odds_val)
                    dval.set_float_info('closing_odds', closing_odds_val)
                    
                    prim_model = xgb.train(
                        params={
                            'tree_method': 'hist',
                            'max_depth': 4,
                            'eta': 0.05,
                            'verbosity': 0,
                        },
                        dtrain=dtrain,
                        num_boost_round=100,
                        obj=clv_xgb_objective,
                        evals=[(dval, 'val')],
                        custom_metric=clv_eval_metric,
                        verbose_eval=False,
                    )
                    
                    # Get predictions from raw model output (apply sigmoid)
                    raw_preds = prim_model.predict(dval)
                    preds = 1.0 / (1.0 + np.exp(-raw_preds))
                    
                    # Store XGBClassifier for meta-model compatibility
                    prim_clf = xgb.XGBClassifier(
                        n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42
                    )
                    prim_clf.fit(X_train, y_train)
                    models.append(prim_clf)
                    
                else:
                    # Standard logloss objective
                    prim_clf = xgb.XGBClassifier(
                        n_estimators=100,
                        max_depth=4,
                        learning_rate=0.05,
                        eval_metric="logloss",
                        random_state=42
                    )
                    prim_clf.fit(X_train, y_train)
                    models.append(prim_clf)
                    preds = prim_clf.predict_proba(X_val)[:, 1]
                
                # Predict OOF probability for the positive class (Home Win = 1)
                preds = prim_clf.predict_proba(X_val)[:, 1]
                oof_preds[val_idx] = preds
                
                # Fit Isotonic Calibrator
                calibrator = IsotonicRegression(out_of_bounds="clip")
                calibrator.fit(preds, y_val)
                calibrators.append(calibrator)
                
                calibrated_preds = calibrator.predict(preds)
                calibrated_oof_preds[val_idx] = calibrated_preds
                
                # Step 2: Meta-Labeling Target Construction
                # H0: Value bet exists when model predicted prob > bookmaker implied prob
                # Target meta-label = 1 if (we bet home & home wins) or (we bet away & away wins)
                # Let's simplify: 1 if we make an edge-based bet and it wins, 0 otherwise
                implied_h = X_val["implied_prob_home"].values
                implied_a = X_val["implied_prob_away"].values
                
                fold_meta_targets = []
                for idx_in_fold, (p, val_y, imp_h, imp_a) in enumerate(zip(calibrated_preds, y_val, implied_h, implied_a)):
                    # If model probability > bookmaker implied home probability, we buy home
                    if p > imp_h and val_y == 1:
                        fold_meta_targets.append(1) # Winning home bet
                    # If model probability < bookmaker implied away probability (which is 1 - model prob), we buy away
                    elif (1.0 - p) > imp_a and val_y == 0:
                        fold_meta_targets.append(1) # Winning away bet
                    else:
                        fold_meta_targets.append(0) # Bet lost or no edge found (no bet made)
                
                meta_targets[val_idx] = fold_meta_targets
                
                # Step 3: Fit Secondary Meta-Model (Filters bad bets)
                # Primary predictions, Elo and context act as features for the meta-model
                meta_feats = ["elo_diff", "rest_diff", "market_overround", "odds_home", "odds_away"]
                X_train_meta = X_train[meta_feats].copy()
                X_train_meta["prim_pred"] = prim_clf.predict_proba(X_train)[:, 1]
                
                X_val_meta = X_val[meta_feats].copy()
                X_val_meta["prim_pred"] = preds
                
                # Fit Meta XGBoost
                # To prevent errors, check if meta-labels contain both 0 and 1
                y_train_meta = []
                for p_t, t_y, im_h, im_a in zip(prim_clf.predict_proba(X_train)[:, 1], y_train, X_train["implied_prob_home"], X_train["implied_prob_away"]):
                    if p_t > im_h and t_y == 1:
                        y_train_meta.append(1)
                    elif (1.0 - p_t) > im_a and t_y == 0:
                        y_train_meta.append(1)
                    else:
                        y_train_meta.append(0)
                        
                y_train_meta = np.array(y_train_meta)
                
                if len(np.unique(y_train_meta)) >= 2:
                    meta_clf = xgb.XGBClassifier(
                        n_estimators=50,
                        max_depth=3,
                        learning_rate=0.05,
                        eval_metric="logloss",
                        random_state=42
                    )
                    meta_clf.fit(X_train_meta, y_train_meta)
                    meta_models.append(meta_clf)
                    
                    # Predict out-of-fold probability of authorization
                    meta_oof_preds[val_idx] = meta_clf.predict_proba(X_val_meta)[:, 1]
                else:
                    logger.warning(f"Meta-model training skipped for Fold {fold+1} due to uniform meta-labels.")
                    meta_oof_preds[val_idx] = 0.5 # Default probability
            
            # Step 4: Calculate final OOF validation metrics
            # Filter validation indices (since first chunks have 0 predictions due to walk-forward splits)
            valid_val_idx = np.where(oof_preds > 0.0)[0]
            
            if len(valid_val_idx) > 0:
                y_val_true = y[valid_val_idx]
                
                brier_raw = brier_score_loss(y_val_true, oof_preds[valid_val_idx])
                brier_cal = brier_score_loss(y_val_true, calibrated_oof_preds[valid_val_idx])
                auc_raw = roc_auc_score(y_val_true, oof_preds[valid_val_idx])
                auc_cal = roc_auc_score(y_val_true, calibrated_oof_preds[valid_val_idx])
                
                logger.info(f"OOF Brier Score (Raw): {brier_raw:.4f}")
                logger.info(f"OOF Brier Score (Calibrated): {brier_cal:.4f}")
                logger.info(f"OOF ROC-AUC (Calibrated): {auc_cal:.4f}")
                
                mlflow.log_metric("brier_raw", brier_raw)
                mlflow.log_metric("brier_calibrated", brier_cal)
                mlflow.log_metric("auc_calibrated", auc_cal)
                
                # CLV metrics (if odds available)
                if "odds_home" in X.columns:
                    from src.ml.training.clv_metrics import evaluate_model_clv
                    opening = X.iloc[valid_val_idx]["odds_home"].values
                    closing = opening.copy()
                    if "closing_odds_home" in X.columns:
                        closing = X.iloc[valid_val_idx]["closing_odds_home"].values
                    clv_metrics = evaluate_model_clv(
                        predictions=calibrated_oof_preds[valid_val_idx],
                        labels=y_val_true,
                        opening_odds=opening,
                        closing_odds=closing,
                    )
                    logger.info(f"CLV Correlation: {clv_metrics['clv_correlation']:.4f}")
                    logger.info(f"Beat Closing Line Rate: {clv_metrics['beat_closing_line_rate']:.4f}")
                    logger.info(f"ROI Top-50: {clv_metrics['roi_top50']:.4f}")
                    logger.info(f"Sharpe: {clv_metrics['sharpe']:.4f}")
                    for k, v in clv_metrics.items():
                        mlflow.log_metric(f"clv_{k}", v)
            
            # Step 5: Save model artifacts
            artifacts = {
                "models": models,
                "calibrators": calibrators,
                "meta_models": meta_models,
                "feature_cols": feature_cols
            }
            
            os.makedirs("models", exist_ok=True)
            model_path = "models/nba_unified_pipeline.joblib"
            from src.ml.safe_io import safe_save
            safe_save(artifacts, model_path)

            mlflow.log_artifact(model_path)
            mlflow.log_artifact(model_path + ".sha256")
            logger.info(f"Pipeline models saved and logged to MLflow successfully at {model_path}.")
            
            return artifacts

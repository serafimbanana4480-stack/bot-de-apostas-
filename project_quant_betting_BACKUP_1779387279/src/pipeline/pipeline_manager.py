"""
Pipeline Manager Module.
Orchestrates the entire ETL -> ML -> Betting -> Settlement flow.
"""
import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PipelineManager:
    """Master orchestrator for the quantitative betting pipeline."""
    
    def __init__(self, config_manager, data_ingestion, feature_pipeline, ml_model, decision_engine, execution_engine):
        self.config = config_manager
        self.ingestion = data_ingestion
        self.features = feature_pipeline
        self.model = ml_model
        self.decision = decision_engine
        self.execution = execution_engine
        
    async def run_cycle(self):
        """Run a single iteration of the betting pipeline."""
        logger.info("Starting pipeline cycle...")
        
        try:
            # 1. Data Ingestion & Sync
            logger.info("Phase 1: Ingestion")
            raw_data = await self.ingestion.fetch_latest()
            
            # 2. Feature Engineering
            logger.info("Phase 2: Feature Engineering")
            feature_vectors = self.features.build_batch(raw_data)
            
            # 3. Model Inference
            logger.info("Phase 3: Model Inference")
            predictions = self.model.predict_batch(feature_vectors)
            
            # 4. Decision Engine
            logger.info("Phase 4: Decision Engine")
            decisions = self.decision.evaluate_batch(predictions)
            
            # 5. Execution
            logger.info("Phase 5: Execution")
            for decision in decisions:
                if decision.get("decision_type") == "BET_NOW":
                    await self.execution.place_order(decision)
                    
            logger.info("Pipeline cycle completed successfully.")
            
        except Exception as e:
            logger.error(f"Critical error in pipeline cycle: {e}", exc_info=True)
            # Would trigger circuit breakers here

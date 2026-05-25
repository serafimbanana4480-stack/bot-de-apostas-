#!/usr/bin/env python3
"""
Train meta-learning model (MAML) across multiple sports, then adapt to new sports.

Phase 1: Meta-train across known sports (NBA, Football, UFC)
Phase 2: Few-shot adapt to a new sport (Tennis, Esports) with 20-30 games

Usage:
    # Meta-train across existing sports
    poetry run python scripts/train_meta_model.py --mode meta-train --sports football,nba,ufc

    # Adapt to a new sport with few-shot data
    poetry run python scripts/train_meta_model.py --mode adapt --sport tennis --samples 25
"""
import argparse
import logging
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ml.meta.maml import MAMLTrainer, MetaBettingNet, MetaTask

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("train_meta_model")


def load_meta_tasks(sports: list, task_dir: str = "data/meta_tasks") -> list:
    """Load pre-prepared meta-learning tasks from disk."""
    tasks = []
    task_path = Path(task_dir)

    for sport in sports:
        path = task_path / f"meta_task_{sport}.npz"
        if path.exists():
            data = np.load(path, allow_pickle=True)
            task = MetaTask(
                name=str(data.get("name", sport)),
                X_support=data["X_support"],
                y_support=data["y_support"],
                X_query=data["X_query"],
                y_query=data["y_query"],
            )
            tasks.append(task)
            logger.info("Loaded task for %s: support=%d, query=%d", sport, len(task.X_support), len(task.X_query))
        else:
            logger.warning("Task file not found: %s — generating synthetic", path)
            task = generate_synthetic_task(sport)
            tasks.append(task)

    return tasks


def generate_synthetic_task(sport: str, seed: int = 42) -> MetaTask:
    """Generate a synthetic meta-learning task."""
    rng = np.random.RandomState(seed)
    n_features = 30
    n_support = 10
    n_query = 50

    X_support = rng.randn(n_support, n_features).astype(np.float32)
    y_support = (X_support[:, 0] > 0).astype(np.float32)
    X_query = rng.randn(n_query, n_features).astype(np.float32)
    y_query = (X_query[:, 0] > 0).astype(np.float32)

    return MetaTask(
        name=sport,
        X_support=X_support,
        y_support=y_support,
        X_query=X_query,
        y_query=y_query,
    )


def meta_train(args: argparse.Namespace) -> None:
    """Meta-train across multiple sports using MAML."""
    sports = [s.strip() for s in args.sports.split(",")]
    n_iterations = args.iterations
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # Load tasks
    tasks = load_meta_tasks(sports, args.task_dir)
    if not tasks:
        logger.error("No tasks available. Run prepare_meta_tasks.py first.")
        return

    # Determine input dimension from first task
    input_dim = tasks[0].X_support.shape[1]
    logger.info("Input dimension: %d", input_dim)

    # Create MAML trainer
    model_fn = lambda: MetaBettingNet(input_dim=input_dim, hidden_dim=64, output_dim=1)
    trainer = MAMLTrainer(
        model_fn=model_fn,
        tasks=tasks,
        inner_lr=0.01,
        outer_lr=0.001,
        inner_steps=5,
        meta_batch_size=min(4, len(tasks)),
    )

    # Meta-train
    logger.info("Starting MAML meta-training: %d tasks, %d iterations", len(tasks), n_iterations)
    result = trainer.meta_train(
        n_iterations=n_iterations,
        eval_every=100,
        verbose=True,
    )

    # Save meta-model
    meta_model_path = save_dir / "meta_model_weights.npz"
    weights = trainer.meta_model.get_weights()
    np.savez(meta_model_path, **weights)
    logger.info("Meta-model saved to %s", meta_model_path)

    # Evaluate: compare MAML vs random initialization
    logger.info("\n--- Evaluation: MAML vs Random Init ---")
    for task in tasks:
        # MAML-adapted
        adapted = trainer.adapt(task.X_support, task.y_support, n_steps=5)
        maml_loss = adapted.loss(task.X_query, task.y_query)

        # Random init (same architecture)
        random_model = model_fn()
        for _ in range(5):
            grads = random_model.gradients(task.X_support, task.y_support)
            for key, grad in grads.items():
                random_model.__dict__[key] -= 0.01 * grad
        random_loss = random_model.loss(task.X_query, task.y_query)

        improvement = (random_loss - maml_loss) / random_loss * 100
        logger.info(
            "%s: MAML loss=%.4f, Random loss=%.4f, improvement=%.1f%%",
            task.name, maml_loss, random_loss, improvement,
        )

    # Log to MLflow
    try:
        import mlflow
        mlflow.set_tracking_uri(f"sqlite:///{PROJECT_ROOT / 'mlflow.db'}")
        with mlflow.start_run(run_name="maml_meta_train"):
            mlflow.log_params({
                "sports": args.sports,
                "n_iterations": n_iterations,
                "input_dim": input_dim,
                "inner_lr": 0.01,
                "outer_lr": 0.001,
            })
            mlflow.log_metrics({
                "final_meta_loss": result.get("final_meta_loss", 0),
            })
            mlflow.log_artifact(str(meta_model_path))
    except ImportError:
        pass


def adapt(args: argparse.Namespace) -> None:
    """Few-shot adapt meta-model to a new sport."""
    sport = args.sport
    n_samples = args.samples
    save_dir = Path(args.save_dir)

    # Load meta-model
    meta_model_path = save_dir / "meta_model_weights.npz"
    if not meta_model_path.exists():
        logger.error("Meta-model not found at %s. Run meta-train first.", meta_model_path)
        return

    # Load weights
    weights_data = np.load(meta_model_path)
    weights = {key: weights_data[key] for key in weights_data.files}

    # Determine input dimension
    input_dim = weights["W1"].shape[0]

    # Create model and load meta-weights
    model = MetaBettingNet(input_dim=input_dim, hidden_dim=64, output_dim=1)
    model.set_weights(weights)

    # Load or generate few-shot data for new sport
    task = load_or_generate_adaptation_task(sport, n_samples, input_dim)

    # Adapt with few gradient steps
    logger.info("Adapting to %s with %d samples...", sport, len(task.X_support))
    trainer = MAMLTrainer(
        model_fn=lambda: MetaBettingNet(input_dim=input_dim, hidden_dim=64, output_dim=1),
        inner_lr=0.01,
        outer_lr=0.001,
        inner_steps=5,
    )
    trainer.meta_model = model

    adapted = trainer.adapt(task.X_support, task.y_support, n_steps=5)

    # Evaluate
    adapt_loss = adapted.loss(task.X_query, task.y_query)
    pre_adapt_loss = model.loss(task.X_query, task.y_query)
    logger.info(
        "%s adaptation: pre-adapt loss=%.4f, post-adapt loss=%.4f, improvement=%.1f%%",
        sport, pre_adapt_loss, adapt_loss,
        (pre_adapt_loss - adapt_loss) / pre_adapt_loss * 100,
    )

    # Save adapted model
    adapt_path = save_dir / f"adapted_{sport}_model.npz"
    adapted_weights = adapted.get_weights()
    np.savez(adapt_path, **adapted_weights)
    logger.info("Adapted model saved to %s", adapt_path)


def load_or_generate_adaptation_task(sport: str, n_samples: int, input_dim: int) -> MetaTask:
    """Load adaptation data or generate synthetic."""
    rng = np.random.RandomState(42)

    # Try to load real data
    try:
        from src.core.config import settings
        from src.data.local_store import LocalDataStore
        store = LocalDataStore(settings.DATA_DIR)
        df = store.load_parquet(f"{sport}_features")
        if df is not None and len(df) >= n_samples:
            import pandas as pd
            exclude = {"actual_outcome", "match_id", "date", "season", "closing_odd"}
            feature_cols = [c for c in df.columns if c not in exclude and df[c].dtype in (np.float64, np.float32, np.int64, np.int32)]
            X = df[feature_cols].values.astype(np.float32)[:n_samples + 50]
            y = df.get("actual_outcome", pd.Series([0.5] * len(df))).values.astype(np.float32)[:n_samples + 50]
            # Pad or truncate features to match input_dim
            if X.shape[1] < input_dim:
                X = np.pad(X, ((0, 0), (0, input_dim - X.shape[1])))
            elif X.shape[1] > input_dim:
                X = X[:, :input_dim]
            support_idx = list(range(min(n_samples, len(X))))
            query_idx = list(range(n_samples, min(n_samples + 50, len(X))))
            return MetaTask(
                name=sport,
                X_support=X[support_idx],
                y_support=y[support_idx],
                X_query=X[query_idx] if query_idx else X[support_idx[:5]],
                y_query=y[query_idx] if query_idx else y[support_idx[:5]],
            )
    except Exception:
        pass

    # Generate synthetic
    logger.info("Generating synthetic adaptation data for %s", sport)
    X_support = rng.randn(n_samples, input_dim).astype(np.float32)
    y_support = (X_support[:, 0] > 0).astype(np.float32)
    X_query = rng.randn(50, input_dim).astype(np.float32)
    y_query = (X_query[:, 0] > 0).astype(np.float32)
    return MetaTask(name=sport, X_support=X_support, y_support=y_support, X_query=X_query, y_query=y_query)


def main():
    parser = argparse.ArgumentParser(description="MAML meta-learning for betting models")
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")

    # Meta-train
    train_parser = subparsers.add_parser("meta-train", help="Meta-train across sports")
    train_parser.add_argument("--sports", type=str, default="football,nba,ufc")
    train_parser.add_argument("--iterations", type=int, default=1000)
    train_parser.add_argument("--task-dir", type=str, default="data/meta_tasks")
    train_parser.add_argument("--save-dir", type=str, default="models/meta")

    # Adapt
    adapt_parser = subparsers.add_parser("adapt", help="Few-shot adapt to new sport")
    adapt_parser.add_argument("--sport", type=str, required=True)
    adapt_parser.add_argument("--samples", type=int, default=25)
    adapt_parser.add_argument("--save-dir", type=str, default="models/meta")

    args = parser.parse_args()

    if args.mode == "meta-train":
        meta_train(args)
    elif args.mode == "adapt":
        adapt(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

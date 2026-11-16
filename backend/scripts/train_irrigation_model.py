#!/usr/bin/env python
"""Reproducible training script for the Verdant irrigation model.

Usage:

    cd backend
    python -m scripts.train_irrigation_model            # train and store
    python -m scripts.train_irrigation_model --dry-run   # evaluate only

The script reads the live PostgreSQL database, builds a supervised data set
from the recorded soil moisture history, compares candidate models with the
transparent baselines on a time-aware split, and writes a versioned model
artifact with full metadata.

It never fabricates data. When the data set is below the production
requirement the artifact is stored but marked as provisional, and the
reason is printed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.ml.models.registry import list_versions  # noqa: E402
from app.ml.training.dataset import build_dataset  # noqa: E402
from app.ml.training.trainer import feature_importance, train_model  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the Verdant irrigation model.")
    parser.add_argument("--model-name", default="soil_moisture_horizon")
    parser.add_argument("--model-version", default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true", help="Evaluate without storing the artifact.")
    parser.add_argument("--user-id", default=None, help="Restrict the data set to one farmer.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        bundle = build_dataset(db, user_id=args.user_id)
        print("Training data set")
        print(f"  samples                : {bundle.sample_count}")
        print(f"  fields                 : {bundle.field_count}")
        print(f"  span (days)            : {bundle.span_days:.2f}")
        if bundle.span_start and bundle.span_end:
            print(f"  period                 : {bundle.span_start.isoformat()} -> {bundle.span_end.isoformat()}")
        print(f"  readings per field     : {bundle.reading_counts}")
        print(f"  missing feature counts : {bundle.missing_feature_counts}")
        print(f"  production requirement : {bundle.requirement_report()}")

        if bundle.sample_count == 0:
            print("\nNo training samples could be built from the recorded data.")
            print("The transparent baseline stays in charge; no model artifact was written.")
            return 2

        artifact = train_model(
            bundle,
            model_name=args.model_name,
            model_version=args.model_version,
            seed=args.seed,
            save=not args.dry_run,
        )
        if artifact is None:
            print("\nNo model could be trained from the available data.")
            return 3

        metadata = artifact.metadata
        print("\nModel selection")
        print(f"  selected model         : {metadata.model_name} {metadata.model_version}")
        print(f"  selection reason       : {metadata.selection_reason}")
        print(f"  training samples       : {metadata.training_samples}")
        print(f"  validation samples     : {metadata.validation_samples}")
        metrics = metadata.metrics or {}
        print(f"  validation MAE/RMSE/R2 : {metrics.get('validation', {}).get('mae')} / "
              f"{metrics.get('validation', {}).get('rmse')} / "
              f"{metrics.get('validation', {}).get('r2')}")
        print(f"  test MAE/RMSE/R2       : {metrics.get('test', {}).get('mae')} / "
              f"{metrics.get('test', {}).get('rmse')} / "
              f"{metrics.get('test', {}).get('r2')}")
        print("\n  Baseline comparison")
        for name, result in (metadata.baseline_metrics or {}).items():
            validation = result.get("validation") or {}
            test = result.get("test") or {}
            print(f"    {name:16s} validation MAE {validation.get('mae')} | test MAE {test.get('mae')}")

        if not args.dry_run:
            print("\nStored artifacts")
            for entry in list_versions(metadata.model_name)[:5]:
                print(f"    {entry['model_name']} {entry['model_version']} "
                      f"(samples {entry.get('training_samples')}, selected {entry.get('selected')})")

        print("\nFeature importance (top 10)")
        for name, value in list(feature_importance(artifact).items())[:10]:
            print(f"    {name:36s} {value:.4f}")

        print("\nLimitations")
        for limitation in metadata.data_limitations:
            print(f"    - {limitation}")

        requirements = metadata.minimum_production_requirements or {}
        if not requirements.get("meets_requirements"):
            print("\nThe data set is below the production requirement.")
            print("Predictions produced with this artifact are marked provisional.")
        else:
            print("\nThe data set meets the production requirement.")

        print("\n" + json.dumps(metadata.to_dict(), indent=2, sort_keys=True))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

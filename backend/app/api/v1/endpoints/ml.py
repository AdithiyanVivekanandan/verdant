"""ML model status and training endpoints.

The status endpoint reports the *real* state of the model registry: what is
trained, on how much data, with which metrics, and whether the production
data requirement is met. It never claims accuracy that was not measured.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.ml.models.registry import list_versions, load_selected_artifact
from app.ml.training.dataset import build_dataset
from app.ml.training.trainer import train_model
from app.models.base import Profile
from app.schemas.irrigation import ModelStatusResponse

router = APIRouter()


@router.get("/models/status", response_model=ModelStatusResponse)
def get_model_status(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Report the active predictor, its metrics and its limitations."""
    artifact = load_selected_artifact()
    bundle = build_dataset(db)

    if artifact is None:
        versions = list_versions()
        return ModelStatusResponse(
            model_name=None,
            model_version=None,
            status="baseline_only",
            active_predictor="baseline",
            provisional=True,
            note=(
                "No model has been promoted for this deployment. Verdant is using the "
                "transparent baseline (recent soil moisture trend plus the soil water "
                "balance). Train a model with the training script to evaluate one."
            ),
            available_versions=versions,
            minimum_production_requirements=bundle.requirement_report(),
            data_limitations=bundle.limitations,
        )

    metadata = artifact.metadata
    requirements = metadata.minimum_production_requirements or {}
    meets = bool(requirements.get("meets_requirements"))
    provisional = not meets

    return ModelStatusResponse(
        model_name=metadata.model_name,
        model_version=metadata.model_version,
        status="validated" if meets else "provisional",
        trained_at=metadata.trained_at,
        training_samples=metadata.training_samples,
        validation_samples=metadata.validation_samples,
        training_period_start=metadata.training_period_start,
        training_period_end=metadata.training_period_end,
        validation_period_start=metadata.validation_period_start,
        validation_period_end=metadata.validation_period_end,
        features=metadata.features,
        metrics=metadata.metrics,
        baseline_metrics=metadata.baseline_metrics,
        comparison=metadata.comparison,
        data_limitations=metadata.data_limitations,
        minimum_production_requirements=requirements,
        active_predictor=metadata.model_name if metadata.selected else "baseline",
        provisional=provisional,
        note=(
            "The model beat the transparent baseline on the time-aware validation split, "
            "but the available data set is still below the production requirement, so its "
            "predictions are reported as provisional."
            if provisional
            else "The model beat the transparent baseline on the time-aware validation split "
            "and the data set meets the production requirement."
        ),
        available_versions=list_versions(),
    )


@router.post("/models/train", response_model=ModelStatusResponse)
def train(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Train a model from the recorded data and report the outcome.

    The training uses the same code path as the reproducible script
    ``python -m scripts.train_irrigation_model``.
    """
    bundle = build_dataset(db)
    if bundle.sample_count == 0:
        raise ValueError("No training samples could be built from the recorded data.")

    artifact = train_model(bundle)
    if artifact is None:
        raise ValueError("No model could be trained from the available data.")

    metadata = artifact.metadata
    requirements = metadata.minimum_production_requirements or {}
    meets = bool(requirements.get("meets_requirements"))
    return ModelStatusResponse(
        model_name=metadata.model_name,
        model_version=metadata.model_version,
        status="validated" if meets else "provisional",
        trained_at=metadata.trained_at,
        training_samples=metadata.training_samples,
        validation_samples=metadata.validation_samples,
        training_period_start=metadata.training_period_start,
        training_period_end=metadata.training_period_end,
        validation_period_start=metadata.validation_period_start,
        validation_period_end=metadata.validation_period_end,
        features=metadata.features,
        metrics=metadata.metrics,
        baseline_metrics=metadata.baseline_metrics,
        comparison=metadata.comparison,
        data_limitations=metadata.data_limitations,
        minimum_production_requirements=requirements,
        active_predictor=metadata.model_name if metadata.selected else "baseline",
        provisional=not meets,
        note=metadata.selection_reason,
        available_versions=list_versions(),
    )

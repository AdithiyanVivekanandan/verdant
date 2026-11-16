"""Preprocessing transformers for the irrigation model.

The only transformation is median imputation of missing numeric features.
The imputation statistics are fitted on the training split only and stored
inside the model artifact, so inference uses exactly the same transformation
as training.

The imputer also fixes the **feature order**: the fitted key order is the
order used for every transformed row, so a training row and an inference row
always produce vectors of the same length and meaning.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import Optional, Sequence


@dataclass
class MedianImputer:
    """Replace missing numeric values with the training median.

    A feature with no observed training value keeps its key (so the vector
    length stays stable) and is filled with ``0.0``; such a feature carries
    no signal and is reported as a limitation of the data set.
    """

    medians: dict[str, float] = dataclass_field(default_factory=dict)
    #: Keys whose training values were entirely missing.
    empty_features: list[str] = dataclass_field(default_factory=list)

    def fit(self, rows: Sequence[dict[str, Optional[float]]]) -> "MedianImputer":
        medians: dict[str, float] = {}
        empty: list[str] = []
        keys = list(rows[0].keys()) if rows else []
        for key in keys:
            values = [row.get(key) for row in rows]
            numbers = sorted(v for v in values if v is not None)
            if numbers:
                mid = len(numbers) // 2
                medians[key] = (
                    numbers[mid] if len(numbers) % 2 else (numbers[mid - 1] + numbers[mid]) / 2.0
                )
            else:
                medians[key] = 0.0
                empty.append(key)
        self.medians = medians
        self.empty_features = empty
        return self

    def transform(self, row: dict[str, Optional[float]]) -> list[float]:
        return [self._value(row.get(key), key) for key in self.medians]

    def transform_many(self, rows: Sequence[dict[str, Optional[float]]]) -> list[list[float]]:
        return [self.transform(row) for row in rows]

    def _value(self, value: Optional[float], key: str) -> float:
        if value is None:
            return float(self.medians.get(key, 0.0))
        return float(value)

    def to_dict(self) -> dict[str, float]:
        return dict(self.medians)

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "MedianImputer":
        return cls(medians=dict(data))

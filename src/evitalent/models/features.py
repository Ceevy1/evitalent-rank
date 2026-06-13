from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel, Field


FeatureValue = Optional[Union[float, int, str, bool, list[str]]]


class ComputedFeatures(BaseModel):
    candidate_id: str
    domain: str
    values: dict[str, FeatureValue] = Field(default_factory=dict)
    evidence_ids: dict[str, list[str]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    def get_number(self, name: str, default: float = 0.0) -> float:
        value = self.values.get(name)
        return float(value) if isinstance(value, (int, float)) else default

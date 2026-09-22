from datetime import datetime
from pydantic import BaseModel, field_validator

from app.services.pack_engine import CATEGORIES, CATEGORY_NORMAL


class RouteOut(BaseModel):
    id: int
    name: str
    max_weight_kg: float
    max_volume_l: float
    model_config = {"from_attributes": True}


class StopOut(BaseModel):
    id: int
    route_id: int
    seq: int
    name: str
    weight_kg: float
    volume_l: float
    category: str = CATEGORY_NORMAL
    model_config = {"from_attributes": True}


class StopCategoryUpdate(BaseModel):
    category: str

    @field_validator("category")
    @classmethod
    def _check_category(cls, v: str) -> str:
        if v not in CATEGORIES:
            raise ValueError(f"品类必须是 {list(CATEGORIES)} 之一")
        return v


class BagItemOut(BaseModel):
    stop_id: int
    stop_name: str
    weight_kg: float
    volume_l: float
    category: str = CATEGORY_NORMAL


class BagOut(BaseModel):
    id: int
    route_id: int
    bag_index: int
    weight_kg: float
    volume_l: float
    items: list[BagItemOut] = []
    model_config = {"from_attributes": True}


class RejectOut(BaseModel):
    id: int
    route_id: int
    stop_id: int
    stop_name: str
    reason: str
    category: str = CATEGORY_NORMAL
    created_at: datetime
    model_config = {"from_attributes": True}


class PackRequest(BaseModel):
    route_id: int


class WeightOut(BaseModel):
    bag_id: int
    bag_index: int
    route_id: int
    weight_kg: float
    volume_l: float
    fill_weight_pct: float
    fill_volume_pct: float

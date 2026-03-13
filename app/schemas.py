from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class IPCModelOut(BaseModel):
    id: int
    name: str
    cpu_model: Optional[str] = None
    ram: Optional[str] = None
    gpu_info: Optional[str] = None
    ssd: Optional[str] = None
    hdd: Optional[str] = None

    class Config:
        from_attributes = True


class TestRecordOut(BaseModel):
    id: int
    ipc_model: IPCModelOut
    software_version: str
    resolution_mp: int
    camera_count: int
    model_count: int
    segments_count: int
    image_count: Optional[int] = None
    save_image: Optional[bool] = None
    measured_perf_mps: float
    ex_perf_mps: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecordSearchRequest(BaseModel):
    ipc_model_ids: Optional[List[int]] = None
    resolution_mp: Optional[int] = None
    camera_count: Optional[int] = None
    model_count: Optional[int] = None
    software_versions: Optional[List[str]] = None


class OptionsOut(BaseModel):
    ipc_models: List[IPCModelOut]
    resolutions: List[int]
    camera_counts: List[int]
    model_counts: List[int]
    software_versions: List[str]


class ImportResult(BaseModel):
    inserted: int
    skipped: int
    errors: Optional[List[str]] = None

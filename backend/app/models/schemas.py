from pydantic import BaseModel


class ViolationOut(BaseModel):
    id: int
    violation_id: str
    vehicle_number: str | None
    violation_type: str
    confidence: float
    status: str
    city: str | None
    location: str | None
    lat: float | None
    lon: float | None
    original_image_path: str | None
    annotated_image_path: str | None
    source: str
    created_at: str


class StatusUpdate(BaseModel):
    status: str


class DetectionResponse(BaseModel):
    vehicle_number: str
    violations: list[ViolationOut]
    annotated_image_url: str
    original_image_url: str
    vehicles_detected: int
    is_compliant: bool

from typing import Literal
from fennec_api.core.schemas import FennecBaseModel


class HealthCheckResponse(FennecBaseModel):
    message: Literal["Healthy"]

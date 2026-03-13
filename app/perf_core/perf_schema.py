from pydantic import BaseModel
from typing import Literal, List

IPC_MODEL_TYPE = Literal["enterprise", "pro", "standard", "core"]
RESOLUTION_MP = Literal[5, 12, 24]
MODEL_COUNT = Literal[2, 3, 4, 5]

class PerfEvalInput(BaseModel):
    ipc_type: IPC_MODEL_TYPE
    resolution_mp: RESOLUTION_MP
    # model_count: MODEL_COUNT


class PerfEvalResult(BaseModel):
    throughput_mps: List[dict[MODEL_COUNT, float]]

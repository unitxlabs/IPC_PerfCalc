from .perf_config import IPC_PROFILE, CAMERA_FRAME_TIME_MS, MODEL_COUNT_LIST
from .perf_schema import PerfEvalInput, PerfEvalResult


def estimate_perf(inp: PerfEvalInput) -> PerfEvalResult:
    profile = IPC_PROFILE[inp.ipc_type.lower()]
    resolution_mp = inp.resolution_mp

    throughput_mps_list = []
    for m in MODEL_COUNT_LIST:
        total_ms = (
            CAMERA_FRAME_TIME_MS[resolution_mp]
            + profile["inference_ms"] * m
            + profile["postprocess_ms"]
        )
        fps = 1000.0 / total_ms
        mps = fps * resolution_mp
        throughput_mps_list.append({m: mps}) 

    return PerfEvalResult(
        throughput_mps=throughput_mps_list,
    )

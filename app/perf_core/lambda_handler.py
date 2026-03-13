import json
from .perf_schema import PerfEvalInput
from .perf_calc import estimate_perf


def handler(event, context):
    body = json.loads(event["body"])
    inp = PerfEvalInput.model_validate(body)
    out = estimate_perf(inp)

    return {
        "statusCode": 200,
        "body": out.model_dump_json(),
        "headers": {"Content-Type": "application/json"},
    }

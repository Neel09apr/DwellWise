"""Run metrics as CloudWatch Embedded Metric Format log lines.

Two metrics with one dimension (the source) keeps the custom-metric count
inside CloudWatch's free ten.
"""

import json
import time


def emit(source: str, succeeded: bool, rows: int) -> None:
    print(  # noqa: T201 - EMF is read from stdout by CloudWatch
        json.dumps(
            {
                "_aws": {
                    "Timestamp": int(time.time() * 1000),
                    "CloudWatchMetrics": [
                        {
                            "Namespace": "DwellWise",
                            "Dimensions": [["Source"]],
                            "Metrics": [
                                {"Name": "RunSucceeded", "Unit": "Count"},
                                {"Name": "RowsLoaded", "Unit": "Count"},
                            ],
                        }
                    ],
                },
                "Source": source,
                "RunSucceeded": int(succeeded),
                "RowsLoaded": rows,
            }
        ),
        flush=True,
    )

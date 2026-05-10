# Perception Upgrade Evaluation

## Goal

Objective 4 keeps the camera focused on delivery support: fixed-route evidence,
trash station or bin cues, obstacle and anomaly records, remote review, and data
collection. Scattered-trash detection is an enhancement until the robot has a
validated manipulator and pickup mechanism.

## Decision Summary

No default detector is shipped in the current MVP. The delivery loop is based on
user-loaded trash, route navigation, and dropoff confirmation. Add a lightweight
YOLO or OpenCV-based perception node only after there is a clear station, anomaly,
or remote-review requirement with representative local route and station images.
Treat RT-DETR and depth cameras as later validation items because they add
compute, cost, and integration risk before the delivery loop is stable.

## Evaluation Matrix

| Option | Development cost | Compute need | Robustness | Production cost | Data need | Landing conditions | Recommended stage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenCV HSV / contour heuristic | Low. Easy to tune on site if reintroduced. | Low. Fits Orange Pi class boards if debug image publishing can be disabled. | Low to medium. Sensitive to lighting, color, shadows, and background clutter. | Low. Uses the existing camera and CPU. | Low. Useful before labels exist. | Fixed route, controlled lighting, station markers or simple color cues, sample saving enabled. | Future optional debug/data-capture module, not part of the current MVP default. |
| YOLO lightweight detector | Medium. Needs dataset labeling, training/export, and runtime packaging. | Medium. Needs careful model size and inference rate control on low-cost boards. | Medium to high after local data training. Better for bins, station markers, bags, and common obstacles. | Medium. May require a faster board or accelerator if real-time FPS is required. | Medium to high. Needs representative local images and negative samples. | At least hundreds of labeled route/station/anomaly samples, stable camera mount, target FPS and latency budget. | Next model upgrade candidate after data collection. |
| RT-DETR | High. More complex model pipeline and tuning. | High. Usually needs stronger GPU/NPU for practical latency. | High in richer scenes when compute is available, but overkill for the current fixed-route MVP. | High. Increases board, thermal, and power requirements. | High. Needs labeled data and validation across scenes. | Clear evidence that YOLO misses critical cases and enough compute budget exists. | Research or premium variant, not default MVP. |
| Depth camera | Medium to high. Requires calibration, mounting, drivers, and fusion logic. | Medium. Depth processing and synchronization add load. | Medium to high for obstacle distance and station geometry, but can fail outdoors or on reflective/transparent objects. | High. Adds sensor BOM, mounting, cable, power, and support cost. | Medium. Needs scenario validation more than class labels. | Obstacle distance or docking/station geometry is a proven blocker, and BOM increase is accepted. | Hardware validation only after delivery reliability metrics justify it. |

## Selection Criteria

- Delivery success impact: Does the option improve arrival, station recognition,
  anomaly review, or recovery?
- Cost fit: Can it ship with the low-cost hardware boundary in `OKR.md`?
- Compute fit: Can it run without starving Nav2, hardware bridge, and behavior
  nodes?
- Data readiness: Is there enough local data to train or validate it?
- Operational risk: Can non-technical users and remote support understand
  failures from the saved samples and task records?

## Current Recommendation

Keep the shipped MVP free of a default scattered-trash detector. If visual
evidence is needed for route learning, fixed-route dry runs, or failure
investigations, add a dedicated perception/data-capture node with an explicit
launch flag, sample manifest contract, and validation plan. Review samples
periodically and promote YOLO only when the local dataset can prove better
station/bin/anomaly detection than simpler heuristics.

The operator gateway diagnostics endpoint may still expose
`vision_sample_manifest_ref`, but it is an optional reference supplied by the
deployment. When a manifest is present, diagnostics now summarizes sample count,
event-type distribution, latest sample metadata, and a bounded review queue for
anomaly, route-keyframe, low-confidence, or unreviewed samples. This queue is an
operator/support review aid, not label truth and not proof that a production
detector is ready.

Depth sensing should not become a default hardware dependency until obstacle
distance or docking accuracy is the measured delivery blocker. RT-DETR should
remain a model benchmark option, not a product dependency, until compute and
latency constraints are resolved.

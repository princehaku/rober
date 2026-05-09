# Perception Upgrade Evaluation

## Goal

Objective 4 keeps the camera focused on delivery support: fixed-route evidence,
trash station or bin cues, obstacle and anomaly records, remote review, and data
collection. Scattered-trash detection is an enhancement until the robot has a
validated manipulator and pickup mechanism.

## Decision Summary

Use the current OpenCV path as the default MVP detector and data recorder. Add a
lightweight YOLO model only after the sample set contains enough local route and
station images. Treat RT-DETR and depth cameras as later validation items because
they add compute, cost, and integration risk before the delivery loop is stable.

## Evaluation Matrix

| Option | Development cost | Compute need | Robustness | Production cost | Data need | Landing conditions | Recommended stage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenCV HSV / contour heuristic | Low. Already implemented and easy to tune on site. | Low. Fits Orange Pi class boards if debug image publishing can be disabled. | Low to medium. Sensitive to lighting, color, shadows, and background clutter. | Low. Uses the existing camera and CPU. | Low. Useful before labels exist. | Fixed route, controlled lighting, station markers or simple color cues, sample saving enabled. | Current MVP default for debug, data capture, and simple station/bin cues. |
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

Keep OpenCV enabled as a parameterized perception and data-capture module. Enable
`save_detection_samples` during route learning, fixed-route dry runs, and failure
investigations. Review samples periodically and promote YOLO only when the local
dataset can prove better station/bin/anomaly detection than the heuristic.

Depth sensing should not become a default hardware dependency until obstacle
distance or docking accuracy is the measured delivery blocker. RT-DETR should
remain a model benchmark option, not a product dependency, until compute and
latency constraints are resolved.

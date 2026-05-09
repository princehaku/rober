# TrashStatus Perception Contract

## Topic

`/trashbot/vision/trash_detected`

This topic is the stable behavior-facing perception contract. The publisher can be
an OpenCV heuristic, a learned detector, or a future sensor-fusion node. The
current delivery MVP does not ship or launch a default publisher for this topic.

## Message Semantics

- `frame_id`: source camera frame from the incoming image header. Current detections are camera/image-relative estimates, not `map` frame object poses.
- `x`: normalized horizontal image offset in the active full image. `0.0` is image center, negative is left, positive is right.
- `y`: normalized vertical image offset in the active full image. `0.0` is image center, negative is above center, positive is below center.
- `z`: range-like estimate in meters when available. Consumers must treat it as approximate unless a future publisher documents a measured-depth source.
- `confidence`: integer percentage from `0` to `100`. The meaning is detector-local but the range is fixed.
- `trash_type`: project-local category id: `0=unknown`, `1=organic`, `2=recyclable`, `3=general`.
- `is_bin`: `true` when the detection is interpreted as a trash bin, trash station marker, or delivery target cue. Bin detections are useful for station recognition; scattered-trash detections are only advisory.
- `timestamp`: source image timestamp in seconds, copied from the incoming image header.

## Consumer Rules

- Behavior-layer success for the current no-arm MVP is based on user-loaded delivery navigation and dropoff confirmation, not scattered-trash pickup.
- Consumers must not infer the concrete detector algorithm from this message. OpenCV, YOLO, RT-DETR, or a depth-camera pipeline must preserve this contract if reintroduced.
- Consumers that need map-frame poses must add an explicit transform/fusion layer instead of treating `x`, `y`, and `z` as map coordinates.

## Current Publisher Status

No default `TrashStatus` publisher is shipped in the MVP. A future perception node
must be explicitly launched, documented, and validated before behavior code relies
on this topic.

## Optional Future Debug Outputs

- `debug_image_topic`: annotated images from a future perception publisher.
- `sample_manifest`: bounded manifest for route, station, or anomaly review samples.
- `roi_x`, `roi_y`, `roi_width`, `roi_height`: optional normalized ROI parameters if the future publisher supports ROI-limited detection.

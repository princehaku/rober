# TrashStatus Perception Contract

## Topic

`/trashbot/vision/trash_detected`

This topic is the stable behavior-facing perception contract. The publisher can be
an OpenCV heuristic, a learned detector, or a future sensor-fusion node, but
behavior code must only depend on the fields below.

## Message Semantics

- `frame_id`: source camera frame from the incoming image header. Current detections are camera/image-relative estimates, not `map` frame object poses.
- `x`: normalized horizontal image offset in the active full image. `0.0` is image center, negative is left, positive is right.
- `y`: normalized vertical image offset in the active full image. `0.0` is image center, negative is above center, positive is below center.
- `z`: range-like estimate in meters when available. The current OpenCV detector derives this from blob size, so consumers must treat it as approximate and not as measured depth.
- `confidence`: integer percentage from `0` to `100`. The meaning is detector-local but the range is fixed.
- `trash_type`: project-local category id: `0=unknown`, `1=organic`, `2=recyclable`, `3=general`.
- `is_bin`: `true` when the detection is interpreted as a trash bin, trash station marker, or delivery target cue. Bin detections are useful for station recognition; scattered-trash detections are only advisory.
- `timestamp`: source image timestamp in seconds, copied from the incoming image header.

## Consumer Rules

- Behavior-layer success for the current no-arm MVP is based on delivery navigation and dropoff confirmation, not scattered-trash pickup.
- Consumers must not infer the concrete detector algorithm from this message. OpenCV, YOLO, RT-DETR, or a depth-camera pipeline must preserve this contract.
- Consumers that need map-frame poses must add an explicit transform/fusion layer instead of treating `x`, `y`, and `z` as map coordinates.

## Current Detector Limits

The current detector is an OpenCV HSV threshold heuristic. It is useful for debug, fixed-route data capture, and building a future dataset, but it is not a reliable grasping or classification model. Behavior-layer MVP success must not depend on scattered-trash detection.

## Debug Outputs

- `debug_image_topic`: publishes annotated images.
- `publish_debug_image`: enables or disables annotated image publishing.
- `save_detection_samples`: when enabled and detections exist, saves raw image, annotated image, and JSON metadata.
- `sample_output_dir`: output directory for saved samples.
- `sample_date_subdirs`: groups samples into `YYYYMMDD` subdirectories.
- `roi_x`, `roi_y`, `roi_width`, `roi_height`: normalized ROI parameters for limiting detection to part of the image.

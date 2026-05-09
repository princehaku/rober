# TrashStatus Perception Contract

## Topic

`/trashbot/vision/trash_detected`

## Message Semantics

- `frame_id`: source camera frame from the incoming image header. Current heuristic detections are image-relative estimates, not map-frame object poses.
- `x`: normalized horizontal image offset. `0.0` is image center, negative is left, positive is right.
- `y`: normalized vertical image offset. `0.0` is image center, negative is above center, positive is below center.
- `z`: crude depth estimate derived from blob size. Treat as a heuristic confidence aid, not measured range.
- `confidence`: integer percentage from `0` to `100`, based on blob area relative to the configured threshold.
- `trash_type`: project-local category id. Current heuristic uses `1` for green organic-like regions, `2` for blue bin-like regions, and `3` for dark bag-like regions.
- `is_bin`: `true` when the detection is interpreted as a trash bin or station marker.
- `timestamp`: source image timestamp in seconds.

## Current Detector Limits

The current detector is an OpenCV HSV threshold heuristic. It is useful for debug, fixed-route data capture, and building a future dataset, but it is not a reliable grasping or classification model. Behavior-layer MVP success must not depend on scattered-trash detection.

## Debug Outputs

- `debug_image_topic`: publishes annotated images.
- `save_detection_samples`: when enabled and detections exist, saves raw image, annotated image, and JSON metadata.
- `sample_output_dir`: output directory for saved samples.
- `roi_x`, `roi_y`, `roi_width`, `roi_height`: normalized ROI parameters for limiting detection to part of the image.

"""视觉检测的结构化数据模型 helper。

TrashDetector 负责 ROS 订阅/发布；本模块只负责把参数、ROI、样本上下文和
检测结果整理成稳定 JSON，方便离线 manifest proof 复用同一字段语义。
"""


DETECTOR_NAME = 'opencv_hsv_heuristic'
VISION_SAMPLE_SCHEMA = 'trashbot.vision_samples.v1'
SAMPLE_URI_PREFIX = 'vision_sample://'


def clamp(value, lower, upper):
    """限制数值范围，避免启动参数把 ROI 或阈值推到不可解释状态。"""
    return max(lower, min(value, upper))


def build_roi_config(roi_x, roi_y, roi_width, roi_height):
    """输出归一化 ROI；字段名与样本 JSON 保持一致。"""
    return {
        'x': roi_x,
        'y': roi_y,
        'width': roi_width,
        'height': roi_height,
    }


def build_detector_config(
    *,
    detection_confidence,
    detect_bins,
    min_blob_area_ratio,
    max_publish_per_frame,
    publish_debug_image,
    save_detection_samples,
    save_empty_detection_samples,
    sample_date_subdirs,
    sample_event_type,
    sample_manifest_name,
):
    """记录 detector 参数快照，让样本可复盘而不是只保存图片。"""
    return {
        'detection_confidence': detection_confidence,
        'detect_bins': detect_bins,
        'min_blob_area_ratio': min_blob_area_ratio,
        'max_publish_per_frame': max_publish_per_frame,
        'publish_debug_image': publish_debug_image,
        'save_detection_samples': save_detection_samples,
        'save_empty_detection_samples': save_empty_detection_samples,
        'sample_date_subdirs': sample_date_subdirs,
        'sample_event_type': sample_event_type,
        'sample_manifest_name': sample_manifest_name,
    }


def build_sample_context(
    *,
    task_id,
    route_id,
    checkpoint_id,
    event_type,
    anomaly_type,
):
    """构造样本上下文，连接任务、路线 checkpoint 和异常类型。"""
    return {
        'task_id': task_id,
        'route_id': route_id,
        'checkpoint_id': checkpoint_id,
        'event_type': event_type,
        'anomaly_type': anomaly_type,
    }


def build_sample_detection_payload(detection):
    """把内部 detection dict 压成 manifest 需要的稳定字段。"""
    return {
        'bbox': detection.get('bbox', []),
        'x': detection['x'],
        'y': detection['y'],
        'z': detection.get('z', 0.0),
        'confidence': detection['confidence'],
        'trash_type': detection['trash_type'],
        'is_bin': detection.get('is_bin', False),
    }

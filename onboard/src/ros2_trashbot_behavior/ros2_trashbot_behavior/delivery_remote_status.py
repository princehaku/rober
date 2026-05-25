def safe_state_text_value(value, sensitive_markers):
    text = str(value)
    lowered = text.lower()
    if any(marker in lowered for marker in sensitive_markers):
        return "[redacted]"
    return text[:240]


def filter_safe_operator_status(operator_status, allowed_keys, sensitive_markers):
    # pending ACK 会落盘并在重启后重放，所以只保留手机可读的安全字段。
    # 这里不保存 token、URL、路径、raw ROS topic 或 traceback，避免状态文件变成泄密面。
    safe_status = {}
    for key in allowed_keys:
        if key not in operator_status:
            continue
        value = operator_status[key]
        if isinstance(value, str):
            safe_status[key] = safe_state_text_value(value, sensitive_markers)
        elif isinstance(value, (bool, int, float)) or value is None:
            safe_status[key] = value
    return safe_status

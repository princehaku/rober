def first_dict_value(*candidates, default=None):
    """按调用方给出的顺序返回第一个 dict 值。"""
    # preserved-source 只接受 dict，因为后续 summarizer 会按证据字段读取。
    for candidate in candidates:
        # alias 优先级是 payload 兼容契约的一部分，必须由调用方显式排序。
        if isinstance(candidate, dict):
            return candidate
    # 没有命中时返回调用方指定默认值，保持旧逻辑的 fail-closed 行为。
    return default


def first_non_empty_dict_value(*candidates, default=None):
    """按顺序返回第一个非空 dict 值。"""
    # 旧的 preserved_source 链路只有“非空 dict”才优先；空 dict 必须继续落到后续诊断来源。
    for candidate in candidates:
        # 这里不能复用 first_dict_value，否则空 preserved_source 会提前命中并改变旧行为。
        if isinstance(candidate, dict) and candidate:
            return candidate
    # 没有任何非空 dict 时返回调用方默认值，通常是字段级安全空对象。
    return default


def first_non_empty_dict_then_first_dict(primary, *fallbacks, default=None):
    """primary 非空 dict 优先，否则按顺序返回第一个 fallback dict。"""
    # 该 helper 专门保留 preserved_source 的旧语义：只有非空 preserved_source 才能抢占。
    if isinstance(primary, dict) and primary:
        return primary
    # 后续 fallback 仍使用 first_dict_value，是因为旧长链对 fallback 的空 dict 也会命中。
    # 这样既不会让空 preserved_source 阻断真实状态，也不会跳过调用方显式给出的空状态。
    return first_dict_value(*fallbacks, default=default)


def first_status_dict(
    latest_status,
    diagnostics_source,
    keys,
    include_diagnostics=True,
    fallback_to_diagnostics_source=False,
    default=None,
):
    """从 latest_status 再到 diagnostics_source 按 alias 顺序取第一个 dict。"""
    # 先看 latest_status，是为了保留运行时状态覆盖外部 diagnostics_source 的旧语义。
    status_candidates = [latest_status.get(key) for key in keys]
    # keys 的顺序不能自动排序；robot_diagnostics_* alias 一直是最优先来源。
    source_candidates = []
    if include_diagnostics:
        # diagnostics_source 是兼容历史调用方的第二来源，不能提前到 latest_status 前。
        source_candidates = [diagnostics_source.get(key) for key in keys]
    # 少数旧链路允许整个 diagnostics_source 作为兜底，本参数默认关闭以避免扩大来源。
    fallback_candidates = []
    if fallback_to_diagnostics_source:
        fallback_candidates.append(diagnostics_source)
    # first_dict_value 保留显式候选顺序，让每个调用点都能直接审查 alias 优先级。
    return first_dict_value(
        *status_candidates,
        *source_candidates,
        *fallback_candidates,
        default=default,
    )

"""固定路线数据模型与 proof contract。

本模块只放跨层共享的字段、版本和 payload 构造，避免 runtime 节点、
CSV/YAML 解析器和离线 proof 工具互相引用实现细节。
"""

from pathlib import Path


ROUTE_CONTRACT_VERSION = 'fixed_route.v1'

FAILURE_CODE_NO_ROUTE = 'NO_ROUTE'
FAILURE_CODE_CHECKPOINT_MISSING = 'CHECKPOINT_MISSING'
FAILURE_CODE_NAVIGATION_ABORT = 'NAVIGATION_ABORT'
FAILURE_CODE_NAVIGATION_TIMEOUT = 'NAVIGATION_TIMEOUT'
FAILURE_CODE_NAVIGATION_INTERRUPTED = 'NAVIGATION_INTERRUPTED'


def build_route_id(route_file: str) -> str:
    """把路线文件名归一化成稳定 route_id，便于 task_record 复账。"""
    route_file_name = str(route_file or '').strip()
    if not route_file_name:
        return 'fixed_route'
    route_stem = Path(route_file_name).stem
    return route_stem or 'fixed_route'


def build_checkpoint_id(route_id: str, checkpoint: int) -> str:
    """生成 checkpoint_id；索引补零是为了日志排序和人工排查稳定。"""
    try:
        index = int(checkpoint)
    except (TypeError, ValueError):
        index = 0
    if index < 0:
        index = 0
    return f'{route_id}:{index:03d}'


def build_route_checkpoint_payload(
    route_file: str,
    debug_status_file: str,
    current_index: int,
    total_checkpoints: int,
    *,
    route_id: str | None = None,
    failure_code: str | None = None,
    evidence_ref: str | None = None,
    source: str = 'fixed_route',
    route_contract_version: str = ROUTE_CONTRACT_VERSION,
):
    """构造路线进度 payload，供行为层、诊断和离线回放共用。

    这里不放 ROS message 对象，只保留 JSON 可序列化字段，是为了让 dry-run
    在没有 Nav2、相机和底盘时仍然可以复现 checkpoint 进度。
    """
    normalized_route_id = (route_id or build_route_id(route_file)).strip() or 'fixed_route'
    try:
        index = int(current_index)
    except (TypeError, ValueError):
        index = 0
    try:
        total = int(total_checkpoints)
    except (TypeError, ValueError):
        total = 0
    if total < 0:
        total = 0
    if index < 0:
        index = 0
    if total and index > total:
        index = total

    return {
        'route_id': normalized_route_id,
        'route_file_basename': Path(str(route_file or '').strip() or 'fixed_route').name,
        'checkpoint_id': build_checkpoint_id(normalized_route_id, index),
        'route_contract_version': str(route_contract_version).strip() or ROUTE_CONTRACT_VERSION,
        'evidence_ref': str(evidence_ref if evidence_ref is not None else debug_status_file or '').strip(),
        'checkpoint': index,
        'total_checkpoints': total,
        'failure_code': str(failure_code or '').strip(),
        'source': str(source or 'fixed_route'),
        'target': None,
    }


def build_route_replay_artifact_path(debug_status_file: str) -> str:
    """根据状态文件生成 JSONL 回放路径，保证 software proof 有落盘证据。"""
    base = str(debug_status_file or '').strip() or '/tmp/trashbot_fixed_route_status.json'
    return f'{base}.software_proof.route_replay.jsonl'


def build_route_replay_entry(
    *,
    route_progress: dict,
    state: str,
    source: str,
    route_contract_version: str,
    navigation_elapsed_sec: float,
    updated_at: float,
):
    """构造单条 checkpoint 回放记录，保持字段窄而稳定。"""
    return {
        'state': str(state),
        'route_contract_version': str(route_contract_version),
        'source': str(source),
        'route_id': route_progress.get('route_id'),
        'checkpoint_id': route_progress.get('checkpoint_id'),
        'evidence_ref': route_progress.get('evidence_ref'),
        'checkpoint': route_progress.get('checkpoint'),
        'current_index': route_progress.get('current_index'),
        'target': route_progress.get('target'),
        'failure_code': route_progress.get('failure_code'),
        'navigation_elapsed_sec': float(navigation_elapsed_sec),
        'updated_at': float(updated_at),
    }

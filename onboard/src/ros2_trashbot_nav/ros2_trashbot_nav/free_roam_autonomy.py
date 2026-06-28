"""扫地式自由建图的 fail-closed 策略内核。

这个模块先落地可测试的状态机合同，后续 ROS2 节点只需要把 /scan、/map、
operator confirm 和 stop 反馈转换成 FreeRoamSnapshot，再把 FreeRoamDecision
转成受限 /cmd_vel。默认入口只输出 JSON，不会主动发布运动命令。
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from typing import Any


STATE_LOCKED = "locked"
STATE_READY = "ready"
STATE_RUNNING = "running"
STATE_AVOIDING = "avoiding"
STATE_TURNING_FOR_COVERAGE = "turning_for_coverage"
STATE_STOPPING = "stopping"
STATE_COMPLETED = "completed"


@dataclass(frozen=True)
class FreeRoamConfig:
    """自动扫图的速度和安全边界，数值必须保守且可被 HIL 覆盖。"""

    max_speed_mps: float = 0.12
    turn_speed_radps: float = 0.35
    obstacle_stop_distance_m: float = 0.45
    lidar_fresh_timeout_s: float = 1.5
    max_runtime_s: float = 60.0
    coverage_stall_timeout_s: float = 4.0
    target_unknown_ratio: float = 0.18


@dataclass(frozen=True)
class FreeRoamSnapshot:
    """一次控制 tick 的事实输入，缺字段时上层应传 False/None 让策略锁住。"""

    operator_confirmed: bool = False
    mapping_active: bool = False
    stop_available: bool = False
    lidar_min_distance_m: float | None = None
    lidar_age_s: float | None = None
    map_free_cells: int | None = None
    map_unknown_ratio: float | None = None
    elapsed_s: float = 0.0
    external_stop_requested: bool = False
    now_s: float | None = None


@dataclass(frozen=True)
class FreeRoamGate:
    """给 PC 和 artifact 消费的逐项门禁，避免只看到一个黑盒 locked。"""

    gate_id: str
    label: str
    state: str
    evidence: str
    next_action: str


@dataclass(frozen=True)
class FreeRoamDecision:
    """状态机输出；线速度和角速度为 0 时才允许认为已经 fail closed。"""

    state: str
    linear_x_mps: float
    angular_z_radps: float
    reason: str
    gates: tuple[FreeRoamGate, ...]
    stop_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        """输出稳定 JSON，供 CLI、上车 artifact 和 PC summary 复用。"""
        return {
            "schema": "trashbot.free_roam_autonomy.decision.v1",
            "state": self.state,
            "linear_x_mps": round(self.linear_x_mps, 4),
            "angular_z_radps": round(self.angular_z_radps, 4),
            "reason": self.reason,
            "stop_required": self.stop_required,
            "gates": [
                {
                    "id": gate.gate_id,
                    "label": gate.label,
                    "state": gate.state,
                    "evidence": gate.evidence,
                    "next_action": gate.next_action,
                }
                for gate in self.gates
            ],
        }


class FreeRoamAutonomyController:
    """像扫地机一样自由建图的最小安全状态机。

    控制器保存少量覆盖率历史：地图 free cell 增长时继续直行；长时间没有增长
    时原地慢速换向扫描。任何安全门禁失败都会立刻输出 stop_required。
    """

    def __init__(self, config: FreeRoamConfig | None = None) -> None:
        self.config = config or FreeRoamConfig()
        self._last_free_cells: int | None = None
        self._last_progress_s: float | None = None
        self._turn_sign = 1.0

    def update(self, snapshot: FreeRoamSnapshot) -> FreeRoamDecision:
        """根据最新事实生成下一步动作；不确定时永远返回停止。"""
        now_s = snapshot.now_s if snapshot.now_s is not None else time.monotonic()
        gates = self._build_gates(snapshot)
        blocked = [gate for gate in gates if gate.state == "blocked"]

        if snapshot.external_stop_requested:
            return self._stop(STATE_STOPPING, "现场请求停止", gates)
        if blocked:
            # 未满足现场门禁时优先暴露 locked，避免 PC 把未开始会话误判为已完成。
            return self._stop(STATE_LOCKED, blocked[0].evidence, gates)
        if snapshot.elapsed_s >= self.config.max_runtime_s:
            return self._stop(STATE_COMPLETED, "达到最长自动扫图时间", gates, stop_required=True)
        if snapshot.map_unknown_ratio is not None and snapshot.map_unknown_ratio <= self.config.target_unknown_ratio:
            return self._stop(STATE_COMPLETED, "地图未知区域已降到目标以下", gates, stop_required=True)

        self._record_map_progress(snapshot, now_s)
        if self._obstacle_too_close(snapshot):
            self._turn_sign *= -1.0
            return FreeRoamDecision(
                state=STATE_AVOIDING,
                linear_x_mps=0.0,
                angular_z_radps=self.config.turn_speed_radps * self._turn_sign,
                reason="雷达检测到近距离障碍，原地换向",
                gates=gates,
                stop_required=False,
            )

        if self._coverage_stalled(now_s):
            self._turn_sign *= -1.0
            return FreeRoamDecision(
                state=STATE_TURNING_FOR_COVERAGE,
                linear_x_mps=0.0,
                angular_z_radps=self.config.turn_speed_radps * self._turn_sign,
                reason="地图覆盖暂未增长，原地扫描寻找新方向",
                gates=gates,
                stop_required=False,
            )

        reason = "所有门禁通过，低速直行扩展地图"
        if not snapshot.mapping_active:
            reason = "地图记录未启动，仅低速自由移动"
        elif snapshot.lidar_min_distance_m is None or snapshot.lidar_age_s is None or snapshot.lidar_age_s > self.config.lidar_fresh_timeout_s:
            reason = "雷达未就绪，现场监看下低速自由移动"
        return FreeRoamDecision(
            state=STATE_RUNNING,
            linear_x_mps=self.config.max_speed_mps,
            angular_z_radps=0.0,
            reason=reason,
            gates=gates,
            stop_required=False,
        )

    def _build_gates(self, snapshot: FreeRoamSnapshot) -> tuple[FreeRoamGate, ...]:
        """把策略判断拆成可读门禁，PC 端可以逐项显示而不是猜原因。"""
        return (
            self._gate(
                "operator_confirmed",
                "现场安全确认",
                snapshot.operator_confirmed,
                "已勾选现场安全确认",
                "还未勾选现场安全确认",
                "勾选人在旁边、周围安全、停止手段就绪",
            ),
            self._gate(
                "mapping_active",
                "地图记录",
                snapshot.mapping_active,
                "地图记录已启动",
                "地图记录未启动",
                "先启动扫地式建图记录；这不影响现场监看的低速自由移动",
                blocking=False,
            ),
            self._gate(
                "stop_available",
                "停止兜底",
                snapshot.stop_available,
                "停止按钮或上车停止服务可用",
                "停止兜底不可用",
                "先确认停止按钮和上车停止服务可用",
            ),
            self._lidar_gate(snapshot),
            self._obstacle_gate(snapshot),
        )

    def _gate(
        self,
        gate_id: str,
        label: str,
        passed: bool,
        ready_evidence: str,
        blocked_evidence: str,
        next_action: str,
        blocking: bool = True,
    ) -> FreeRoamGate:
        """统一门禁格式，避免不同 gate 的 state/evidence 口径漂移。"""
        state = "ready" if passed else ("blocked" if blocking else "not_proven")
        return FreeRoamGate(
            gate_id=gate_id,
            label=label,
            state=state,
            evidence=ready_evidence if passed else blocked_evidence,
            next_action="继续保持现场可接管" if passed else next_action,
        )

    def _lidar_gate(self, snapshot: FreeRoamSnapshot) -> FreeRoamGate:
        """雷达缺失只降级为现场监看证据；低速自由移动不能硬依赖雷达。"""
        if snapshot.lidar_min_distance_m is None:
            return FreeRoamGate(
                "lidar_fresh",
                "雷达新鲜",
                "not_proven",
                "未读到雷达距离，按无雷达低速自由移动",
                "继续现场监看；雷达 ready 后才能把本轮视为可建图",
            )
        if snapshot.lidar_age_s is None or snapshot.lidar_age_s > self.config.lidar_fresh_timeout_s:
            return FreeRoamGate(
                "lidar_fresh",
                "雷达新鲜",
                "not_proven",
                "雷达距离已过期，按无雷达低速自由移动",
                "刷新雷达状态；刷新前仅允许现场监看的低速自由移动",
            )
        return FreeRoamGate(
            "lidar_fresh",
            "雷达新鲜",
            "ready",
            f"雷达距离 {snapshot.lidar_min_distance_m:.2f}m，延迟 {snapshot.lidar_age_s:.2f}s",
            "继续保持雷达运行",
        )

    def _obstacle_gate(self, snapshot: FreeRoamSnapshot) -> FreeRoamGate:
        """近障碍不会锁死状态机，但会把下一步从直行改成原地换向。"""
        if snapshot.lidar_min_distance_m is None:
            return FreeRoamGate(
                "obstacle_clear",
                "前方障碍",
                "not_proven",
                "缺少雷达距离，依赖现场接管和停止兜底",
                "继续低速监看；雷达 ready 后再启用障碍距离判断",
            )
        clear = snapshot.lidar_min_distance_m >= self.config.obstacle_stop_distance_m
        return FreeRoamGate(
            "obstacle_clear",
            "前方障碍",
            "ready" if clear else "not_proven",
            f"最近障碍 {snapshot.lidar_min_distance_m:.2f}m",
            "继续直行" if clear else "原地换向避让，不继续直行",
        )

    def _record_map_progress(self, snapshot: FreeRoamSnapshot, now_s: float) -> None:
        """记录 free cell 增长时间，覆盖不增长时让扫地图案主动换向。"""
        if snapshot.map_free_cells is None:
            return
        if self._last_free_cells is None or snapshot.map_free_cells > self._last_free_cells:
            self._last_progress_s = now_s
            self._last_free_cells = snapshot.map_free_cells

    def _coverage_stalled(self, now_s: float) -> bool:
        """地图覆盖长期不变时不要继续直撞一个方向，先原地扫描。"""
        if self._last_progress_s is None:
            return False
        return now_s - self._last_progress_s >= self.config.coverage_stall_timeout_s

    def _obstacle_too_close(self, snapshot: FreeRoamSnapshot) -> bool:
        """障碍门禁为 not_proven 时只能原地换向，不能继续给正线速度。"""
        return (
            snapshot.lidar_min_distance_m is not None
            and snapshot.lidar_min_distance_m < self.config.obstacle_stop_distance_m
        )

    def _stop(
        self,
        state: str,
        reason: str,
        gates: tuple[FreeRoamGate, ...],
        *,
        stop_required: bool = True,
    ) -> FreeRoamDecision:
        """所有锁定、停止、完成状态都必须输出零速度。"""
        return FreeRoamDecision(
            state=state,
            linear_x_mps=0.0,
            angular_z_radps=0.0,
            reason=reason,
            gates=gates,
            stop_required=stop_required,
        )


def snapshot_from_mapping(payload: dict[str, Any]) -> FreeRoamSnapshot:
    """把 JSON 输入安全转成 snapshot；类型不对时按缺失处理。"""
    return FreeRoamSnapshot(
        operator_confirmed=bool(payload.get("operator_confirmed")),
        mapping_active=bool(payload.get("mapping_active")),
        stop_available=bool(payload.get("stop_available")),
        lidar_min_distance_m=_optional_float(payload.get("lidar_min_distance_m")),
        lidar_age_s=_optional_float(payload.get("lidar_age_s")),
        map_free_cells=_optional_int(payload.get("map_free_cells")),
        map_unknown_ratio=_optional_float(payload.get("map_unknown_ratio")),
        elapsed_s=max(0.0, _optional_float(payload.get("elapsed_s")) or 0.0),
        external_stop_requested=bool(payload.get("external_stop_requested")),
        now_s=_optional_float(payload.get("now_s")),
    )


def _optional_float(value: Any) -> float | None:
    """JSON 里空字符串、None、非数字都视为缺失，促使状态机锁住。"""
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: Any) -> int | None:
    """free cell 数必须是非负整数；坏值不能进入覆盖率判断。"""
    number = _optional_float(value)
    if number is None or number < 0:
        return None
    return int(number)


def build_free_roam_decision(payload: dict[str, Any], config: FreeRoamConfig | None = None) -> dict[str, Any]:
    """给测试、CLI 和未来上车 API 复用的单次决策入口。"""
    controller = FreeRoamAutonomyController(config=config)
    return controller.update(snapshot_from_mapping(payload)).to_dict()


def main(argv: list[str] | None = None) -> int:
    """离线调试入口；默认输入为空，因此输出 locked，不会发车。"""
    parser = argparse.ArgumentParser(description="Build a fail-closed free-roam mapping decision.")
    parser.add_argument("--snapshot-json", default="", help="JSON string with FreeRoamSnapshot fields.")
    parser.add_argument("--snapshot-file", default="", help="JSON file with FreeRoamSnapshot fields.")
    args = parser.parse_args(argv)

    payload: dict[str, Any] = {}
    if args.snapshot_file:
        with open(args.snapshot_file, "r", encoding="utf-8") as stream:
            loaded = json.load(stream)
            payload = loaded if isinstance(loaded, dict) else {}
    if args.snapshot_json:
        loaded = json.loads(args.snapshot_json)
        payload = loaded if isinstance(loaded, dict) else {}

    print(json.dumps(build_free_roam_decision(payload), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

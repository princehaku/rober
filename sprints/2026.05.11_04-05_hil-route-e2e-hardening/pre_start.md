# Sprint 2026.05.11 04-05 HIL + Route E2E Hardening - Pre Start

## 状态

- 阶段：pre-start started
- 时间：2026-05-11 03:20 Asia/Shanghai
- Sprint 目录：`sprints/2026.05.11_04-05_hil-route-e2e-hardening/`
- Owner：`product-okr-owner`
- 目标：接续 `2026.05.11_03-04_hil-reality-closure`，把低完成度 OKR 变成可复现实机证据。

## 下一轮启动依据（证据驱动）

1. `OKR.md` 当前快照显示 `Objective 1`、`Objective 2`、`Objective 3` 仍在 75~76% 区间，明显低于 `Objective 5`。
2. `sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run/final.md` 明确写明：
   - elevator 场景仍为 dry-run，未做真实电梯、TTS、相机门识别、楼层 OCR、Nav2 实跑和 HIL。
   - 真实 `route` 投递闭环仍缺。
3. `sprints/2026.05.10_21-22_review-progress-metrics/final.md` 和 `sprints/2026.05.11_03-04_hil-reality-closure/pre_start.md` 重复记录：
   - `test_*review*` 命名测试仍出现 `NO TESTS RAN`。
   - 全量 `git diff --check` 受范围外 `README.md` trailing whitespace 影响。
4. `2026.05.11_03-04` 仅创建了 `pre_start/prd/tech-plan`，未形成 `tech-done/side2side_check/final` 收口，说明该轮尚未进入可交付阶段。
5. AGENTS 和硬件红线要求：涉及 UART/底盘协议/WAVE ROVER/参数必须依 `docs/vendor/VENDOR_INDEX.md` 执行并在 evidence 标注来源。

## 排序决策

- 本轮优先级按 OKR 完成度排序：
  - P0：`Objective 1`（硬件协议与感知真实性）
  - P1：`Objective 2`（送达任务真实失败恢复与可复盘）
  - P2：`Objective 3`（导航与固定路线真实状态一致性）
- P3：`Objective 5` 的 `source` 可视化与异常提示只做最小同步，不抢占 O1/O2/O3 的主任务。

## 本轮不做

- 不继续扩展 elevator assisted 的视觉检测、楼层 OCR 或额外高成本模型。
- 不新增大规模测试矩阵；仅执行围栏测试与最小修复。
- 不把 dry-run 证据包装成实机证据。

## 本轮对接文件范围

- `src/ros2_trashbot_hardware/`
- `src/ros2_trashbot_behavior/`
- `src/ros2_trashbot_nav/`
- `src/ros2_trashbot_bringup/`
- `scripts/hardware_smoke_wave_rover.py`
- `docs/acceptance/wave_rover_hil_evidence.md`
- `docs/acceptance/robot_bringup_checklist.md`
- `docs/hardware/wave_rover_json_bridge.md`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.11_04-05_hil-route-e2e-hardening/`

## 下一步动作

1. `hardware-engineer`：先完成 HIL 级 smoke 与反馈采样证据，补齐“source = hil_pass”链路。
2. `robot-software-engineer`：补齐 mission 主链失败恢复、`elevator_assist` 默认关闭且不影响主线的 task record。
3. `autonomy-engineer`：将 fixed-route 与状态证据字段对齐为可复盘（检查点/目标点/返回索引）。
4. `full-stack-software-engineer`：operator/diagnostics 增加“sim/hil/simulated来源标签”和最新任务 evidence_ref。
5. `全员`：修复 review 命名问题，消除一次性的验收误差。

# Sprint 2026.05.11 03-04 HIL Reality Closure - Pre Start

## 状态

- 阶段：pre-start started
- 时间：2026-05-11 03:01 Asia/Shanghai
- Sprint 目录：`sprints/2026.05.11_03-04_hil-reality-closure/`
- 本轮 owner：`product-okr-owner`
- 执行意图：从软件 dry-run 向硬件可信闭环回归，优先补 O1，按低完成度优先推进 Objective。

## 本轮依据（证据先行）

1. 最近一轮 `2026.05.11_02-03_elevator-assisted-delivery-dry-run` 的实绩为：
   - `Objective 2` 从 约74% 提升到约76%，`Objective 4`/`5` 也有小步+0.5pp，但其 `final.md` 明确写明“dry-run 通过不等于实机电梯能力完成”。
   - 同轮未做真实电梯、真实 TTS、真实相机门识别/楼层 OCR、Nav2/fixed-route 实跑、HIL。
2. `OKR.md` 的当前快照列出 `Objective 1` 仍约75%，且真实 WAVE ROVER HIL、反馈频率、轮向/速度/IMU/电池实测均缺失。
3. `sprints/2026.05.10_21-22_review-progress-metrics/final.md` 的复核问题：
   - `test_*review*py` 仍出现 `NO TESTS RAN`（命名 pattern 覆盖缺口）。
   - `git diff --check` 全量失败来自范围外 `README.md` whitespace。
4. `AGENTS.md` 与 `docs/vendor/VENDOR_INDEX.md` 约束要求：任何硬件事实必须基于 vendor 资料，不得用离线 proof 替代上车验证。

## 核心判断

- 本轮优先级依据：**先补最弱环节 O1（硬件协议实测闭环）再补 O2（任务闭环真实运行）**。
- 电梯 dry-run 维持：不当作任务完成证据，不在本轮继续扩展更多场景字段。

## 目标与优先级

P0（本轮第一优先）

- 1. 目标 1（硬件协议可信闭环）
  - 输出“上车可复用”硬件 smoke/HIL 证据：串口启动命令、T=1/T=13 行为、反馈解码、反馈间隔与方向/单位 sanity。
  - 把 `hardware_diagnostics_proof` 与 `hardware_smoke_wave_rover.py` 的边界分开：proof 用于工程预检，HIL 用于任务可交付证据。
- 2. 目标 2（送垃圾任务真实运行）
  - 把 `task_orchestrator` 的 `elevator_assist` 继续作为可选，默认关闭；主线 mission 必须优先跑 fixed-route/waypoint 的真实失败恢复链路（成功/导航失败/超时/取消）。

P1（本轮并行推进）

- 3. 目标 3（可验证导航）
  - 把 `fixed route` 与 `route proof` 对应关系做一次端到端“任务记录可复盘 + 关键转移落盘”。
- 4. 目标 5（用户可解释闭环）
  - operator/diagnostics 新增 HIL 结果与最近任务可复盘字段，明确“实机 vs 软件模拟”状态。

## 不做

- 不把当前缺失硬件实测的数据打包为“已完成”证据。
- 不在本轮继续扩展电梯识别/楼层识别模型。
- 不新增大规模新测试矩阵：本轮仅保留围栏测试。

## 关键文件范围（本轮启动）

- `src/ros2_trashbot_hardware/`
- `src/ros2_trashbot_behavior/`
- `src/ros2_trashbot_nav/`
- `src/ros2_trashbot_bringup/`
- `src/ros2_trashbot_behavior/static/`（如需状态页展示）
- `docs/interfaces/ros_contracts.md`
- `docs/hardware/wave_rover_json_bridge.md`
- `docs/acceptance/wave_rover_hil_evidence.md`
- `docs/acceptance/robot_bringup_checklist.md`
- `sprints/2026.05.11_03-04_hil-reality-closure/`
- `scripts/hardware_smoke_wave_rover.py`

## 下一步动作清单（已对齐 evidence）

1. 先补 O1：按 vendor 约束把硬件启动/反馈/运动 smoke 做成可复现实验，记录 HIL 结果文件与时间戳。
2. 再补 O2：用同一条任务记录，验证送达动作真实走完 `DELIVERING -> DROPOFF/ERROR -> RETURNING/IDLE`。
3. 同步修复 review 发现的测试工程债：补齐 `test_*review*py` 命名/覆盖策略或更新验收命令。
4. 运行本次技术门禁后再判断 O4/O5 是否进入下一次迭代。

## 验收门禁（tech-plan 交付前）

- 在本轮创建 `prd.md` 与 `tech-plan.md` 后，进入 implementation。
- 实施完进入 `tech-done.md` 之前，必须补齐本轮 `tech-plan.md` 列出的目标化围栏测试与 scoped `git diff --check`。

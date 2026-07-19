# Tech Plan - 有界 live route、HIL 与 operator evidence

## OKR 最低优先级核对

1. `OKR.md` 当前最低 Objective 是 O5，约 `85%`；其次是 O6/O7，各约 `93%`；O1 约 `94%`。
2. 本 sprint 不针对 O5，主推 O6/O7，并联动 O1。
3. 原因：O5 provider/runtime blocker 已连续消费两轮，按红线暂停；最近审计又确认 strict-no-motion 新 lane 已耗尽。下一种未消费证据类别是 fresh authorized current-run mission attempt + HIL + operator action。

## 总体设计与调度

`robot-algorithm-engineer` 是强耦合 live session 的主责与唯一控制编排 owner；`rober-hardware-engineer` 只负责同窗口 stop/feedback 专业事实和独立 artifact；`full-stack-software-engineer` 只在 frozen live artifacts clean 后消费。三个 owner 不并行发送 live 命令，避免重复 goal 或 stop 竞争。

### Phase 0 - explicit authorization gate（当前阶段）

Product 读取 fresh CEO/operator authorization，生成结构化 `authorization_ref`。以下条件全部为 true 才能派工程：

- exactly one `NavigateToPose` to `map (0.8, 0.25, yaw=0)`；
- operator physically present、route cleared、stop ready；
- pre/post `/api/base/stop` 与 same-window `T=1001` capture 获准；
- no retry、no `/initialpose`、no manual control、no direct `/cmd_vel`、no unattended motion；
- 明确执行时间窗与 owner。

当前消息只有 SSH 信息，因此 `authorization_gate=false`。本轮不得执行后续 Phase，不运行 SSH、ROS、Nav2、stop、UART、build/test 或 capture 命令。

### Phase 1 - Hardware pre-gate（仅获授权后）

`rober-hardware-engineer` 必须先重读：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_cn/06 获取底盘反馈信息.ipynb`

只验证 stop path、feedback source、合法 `T=1001` frame 和 operator physical gate；禁止发送独立 motion。pre-stop 或合法 feedback 缺失即 blocked，不进入 Phase 2。

### Phase 2 - Algorithm single bounded attempt（仅 Phase 1 clean）

`robot-algorithm-engineer` 复用既有 current packet/task/route lineage，由单 helper 管理：preflight snapshot、exactly one goal、bounded terminal wait、unconditional post-stop hook、cleanup 和 artifact closeout。禁止手工补跑；任何 timeout/partial/pull/decode 失败都不允许第二次 goal。

目标只允许 `map (0.8, 0.25, yaw=0)`；不得改成 28-pose route，不得发布 `/initialpose`、manual command 或直接 `/cmd_vel`。Artifact status 枚举必须保留真实 succeeded/aborted/rejected/timeout/cancel/blocked，不用布尔成功覆盖事实。

### Phase 3 - Hardware post-gate 与 operator evidence

`rober-hardware-engineer` 在同一 run window 冻结 `T=1001` motion/post-stop material、stop response 与 vendor-field validation；`robot-algorithm-engineer` 合并引用但不复制 raw UART。operator report 必须记录在场、路线清空、观察、stop 与接受状态；report 不能替代硬证据。

### Phase 4 - Full-stack conditional consumption

只有 Phase 2/3 frozen artifacts 结构断言 clean 才派 `full-stack-software-engineer`。复用 O6 archive/task detail 和 O7 consumer detail；按同一 task/run/route/auth lineage 展示，不新增 endpoint。若 Phase 1-3 blocked，Phase 4=`skipped_no_live_mission_attempt_artifact`，不得用 fixture 进入产品路径。

## 精确文件范围

### robot-algorithm-engineer（获授权后主责）

- `onboard/scripts/o3_bounded_live_route_hil_operator_evidence.py`
- `onboard/tests/test_o3_bounded_live_route_hil_operator_evidence.py`
- `docs/navigation/bounded_live_route_hil_operator_evidence.md`
- 本 sprint `artifacts/algorithm/**`
- 本 sprint `tech-done.md` 的 Algorithm/集成段

禁止修改硬件 parser、Full-stack 文件、OKR 或旧 sprint。

### rober-hardware-engineer（获授权后支持）

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_bounded_route_hil_evidence.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_bounded_route_hil_evidence.py`
- `docs/hardware/wave_rover_bounded_route_hil_evidence.md`
- 本 sprint `artifacts/hardware/**`
- 本 sprint `tech-done.md` 的 Hardware 段

禁止修改 Algorithm helper、串口/launch/firmware/速度映射、Full-stack 文件或旧 sprint。

### full-stack-software-engineer（仅 live artifacts clean）

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/interfaces/o7_cloud_archive_task_api.md`
- `docs/product/pc_tools_workstation.md`
- 本 sprint `artifacts/full-stack/**`
- 本 sprint `tech-done.md` 的 Full-stack 段

所有技术注释必须为中文且比例严格 `>20%`。范围外文件禁止修改。

## 验收命令（仅在授权后由对应 Engineer 执行）

### Algorithm

```bash
python3 -m py_compile onboard/scripts/o3_bounded_live_route_hil_operator_evidence.py onboard/tests/test_o3_bounded_live_route_hil_operator_evidence.py
python3 onboard/tests/test_o3_bounded_live_route_hil_operator_evidence.py
python3 onboard/scripts/o3_bounded_live_route_hil_operator_evidence.py --help
# helper 内部管理唯一 SSH/live session；禁止手工补跑 goal。
python3 -m json.tool sprints/2026.07.16_01-17_o1_o6_o7_bounded_live_route_hil_operator_evidence/artifacts/algorithm/route_attempt_manifest.json >/dev/null
git diff --check -- onboard/scripts/o3_bounded_live_route_hil_operator_evidence.py onboard/tests/test_o3_bounded_live_route_hil_operator_evidence.py docs/navigation/bounded_live_route_hil_operator_evidence.md sprints/2026.07.16_01-17_o1_o6_o7_bounded_live_route_hil_operator_evidence
```

结构断言必须证明 `goal_invocation_count=1`、目标固定、authorization lineage 一致、post-stop hook 执行、cleanup residual `0`；不得以 success fixture 替代 live manifest。

### Hardware

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_bounded_route_hil_evidence.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_bounded_route_hil_evidence.py
python3 -m unittest onboard.src.ros2_trashbot_hardware.test.test_wave_rover_bounded_route_hil_evidence
python3 -m json.tool sprints/2026.07.16_01-17_o1_o6_o7_bounded_live_route_hil_operator_evidence/artifacts/hardware/wave_rover_hil_evidence.json >/dev/null
git diff --check -- onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_bounded_route_hil_evidence.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_bounded_route_hil_evidence.py docs/hardware/wave_rover_bounded_route_hil_evidence.md sprints/2026.07.16_01-17_o1_o6_o7_bounded_live_route_hil_operator_evidence
```

结构断言必须验证合法 `T=1001` 包含 `L/R/r/p/y/v`，motion/post-stop 窗口不混淆，stop 后不为 `0/0` 时 fail closed；Hardware 不发送独立运动命令。

### Full-stack（仅 Phase 4）

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o6_cloud_archive_api.md docs/interfaces/o7_cloud_archive_task_api.md docs/product/pc_tools_workstation.md sprints/2026.07.16_01-17_o1_o6_o7_bounded_live_route_hil_operator_evidence
```

## Anti-repeat 与 proof boundary

- 不重跑 O5 provider、`/scan`、camera、localization bag、canary 或任意 wrapper。
- 未授权时不得让任何 Engineer “先做离线 helper”绕过 gate；已有 packet/gate/mock 合同已足够，新的 helper 只有获得 live authorization 才有价值。
- 当前 Proof boundary：`planning_only_blocked_pending_explicit_live_motion_authorization`。
- 当前固定：`current_run_artifact_delta=false`、`external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`okr_credit=false`。
- 获授权后即使产生 mission attempt，也只有 Product 能依据真实终态决定 credit tier；失败 attempt 不能宣称 success，成功 route 也不能自动宣称 delivery。

## 2026-07-20 fresh authorization hardware-first continuation

### OKR 最低优先级核对与路由

`ROUTE=HARDWARE_PRE_GATE`、`authorization=true`。O5 约 `85%` 仍最低但 blocker 已消费 `2/2`；本次切换到 O1 约 `94%` 的未消费 current-live stop/feedback 证据。冻结 `AUTHORIZATION_REF=ceo_20260720_rober_okr_bounded_motion_v1`、`RUN_ID=run_20260720_rober_okr_bounded_route_01`、`task_id=task_o1_bounded_live_route_20260720_01`、`route_intent_id=route_o1_map_0p8_0p25_20260720_01`。这不是 Algorithm wrapper/canary 重试；旧 Algorithm business runtime blocker 保留，只有 Hardware business gate clean 才允许重新派 `robot-algorithm-engineer`。

### Phase 1 Hardware pre-gate（ready）

先派 `rober-hardware-engineer`，文件范围仅为本 sprint `artifacts/hardware/**` 与后续实际执行时的 `tech-done.md` Hardware 段；本次 Product continuation 不提前创建二者。Hardware 必须重读 `docs/vendor/VENDOR_INDEX.md`、`json_cmd.h` 与 vendor feedback tutorial，只执行 current live pre-stop、bridge-owned `T=1001` 反馈采集和 operator physical gate；禁止独立 motion、`/api/base/manual`、直接 `/cmd_vel`、direct UART、第二次 stop 或手工补跑。验收命令必须覆盖 artifact JSON parse、`T=1001` 必需字段、frozen identity、operator present/route clear/stop ready、pre-stop invocation count=`1`、motion invocation count=`0`、`git diff --check` 和 `git status --short`。

任一 SSH、operator、stop、反馈 freshness、schema/field 或 cleanup gate 失败，立即 fail closed，`no retry`，不得派 Algorithm。只有 Hardware clean 后才允许 `robot-algorithm-engineer` 复用既有 Phase 2 文件范围和验收命令，执行 `map (0.8, 0.25, yaw=0)` 的 exactly one bounded goal；Algorithm 禁止 wrapper/canary/fallback、第二个 goal 或独立 motion。Hardware clean 只是 Algorithm gate，不自动产生 OKR credit、HIL pass、safe-to-control、route success 或 delivery success。

# Tech Plan - Mission authorization CEO escalation

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前最低 Objective 是 O5，约 `85%`；其次是 O6/O7，各约 `93%`；O1 约 `94%`。
2. 本 sprint 不继续实现 O5，且当前规划阶段不推动任何 Objective 百分比；授权后唯一 mission 链面向 O6/O7，并联动 O1。
3. 不针对 O5 的原因：provider/runtime 同一 blocker 已连续消费两轮，第三轮必须切换或升级 CEO。本轮选择 CEO 决策升级；禁止再次做 provider probe、tunnel、wrapper、readback、export、browser 或 mock-only gate。
4. 本轮规划/升级本身不是 mission artifact，`okr_credit=false`，KR `不归档`。

## 当前执行状态

- 当前：`authorization=true_current_automation_turn_only`。
- Sprint 状态：`authorization_refreshed_phase_a_frozen_pending_confirmed_subagent_runtime_recovery`。
- Proof boundary：`fresh_authorization_present_no_business_runtime_recovery_no_live_result`。
- SSH endpoint：`root@192.168.1.11:37878`，本轮只允许 Algorithm helper 按冻结合同使用；它不授权手工补跑或其他 owner 发控制命令。
- 当前 Engineering phase：Algorithm=`frozen_pending_confirmed_subagent_runtime_recovery`；Hardware=`waiting_frozen_phase_a_live_artifact`；Full-stack=`waiting_phase_a_b_clean`。
- 授权只覆盖当前 automation turn 的一次有界现场动作；超窗后自动恢复 fail closed。
- 当前只证明工程派单准入，不创建或声称任何 route/HIL/delivery 完成证据；实际结果必须由 Engineer 写入 `tech-done.md` 后再验收。

## Authorization gate

Product 只能在 CEO/operator fresh 消息完整确认下列合同后把 `authorization` 改为 true：

> operator 在场看护、路线已清空且 stop ready；允许 exactly one bounded `NavigateToPose` 到 `map (0.8, 0.25, yaw=0)`；允许 pre/post stop 和同一窗口 WAVE ROVER `T=1001` 采集；no retry、no `/initialpose`、no manual、no direct `/cmd_vel`、no unattended motion。

还必须记录：

- `authorization_ref` 与授权时间；
- operator identity/在场确认；
- 执行窗口；
- route-clear 与 stop-ready 确认；
- 唯一控制编排 owner=`robot-algorithm-engineer`。

缺任一字段、只重复 endpoint、只说“继续推进”或授权超出时间窗，均 fail closed。CEO 选择暂停时，本 sprint 停在规划阶段，由 Product 等待新的 Objective/策略，不派工程。

## 授权后唯一执行链

工程严格串行：`robot-algorithm-engineer` → `rober-hardware-engineer` → `full-stack-software-engineer`。不得并行发 live 命令，不得让 Hardware 或 Full-stack 补跑 goal；任何 phase blocked 都终止后续 phase。

### Phase A - Algorithm：唯一 live session 与 exactly one goal

前置条件：authorization contract 全字段 clean，operator 在场、route clear、stop ready 在执行窗口内再次确认。

`robot-algorithm-engineer` 是唯一 live control orchestrator：

1. 生成同一 `authorization_ref/run_id/task_id/route_intent_id` lineage，并做只读 preflight snapshot。
2. 通过同一个 helper 执行 pre-stop；pre-stop 未确认立即 blocked，goal count 保持 `0`。
3. 只向 `map (0.8, 0.25, yaw=0)` 发 exactly one bounded `NavigateToPose`，`goal_invocation_count=1` 后永不重试。
4. 在 bounded terminal wait 中原样记录 succeeded/aborted/rejected/timeout/cancel/blocked。
5. helper 必须无条件执行 post-stop 与 cleanup，并在同一窗口保留 stop response、route terminal result、WAVE ROVER `T=1001` raw material 引用；Algorithm 不解释硬件字段。
6. 禁止 `/initialpose`、manual、直接 `/cmd_vel`、UART 直控、28-pose route、第二个 goal 和 unattended motion。

Phase A 任何 SSH/ROS/pre-stop/goal/wait/post-stop/capture/pull/decode 失败都不得手工补跑，只能冻结真实失败 artifact 并停止。

### Phase B - Hardware：同窗 stop / T=1001 专业验收

仅 Phase A 已冻结完整 raw session 后进入。`rober-hardware-engineer` 不发送新 goal、motion、manual、`/cmd_vel`、UART 指令或额外 stop，只验证 Phase A 同窗材料。

执行前必须重读：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_cn/06 获取底盘反馈信息.ipynb`

验收合法 `T=1001` frame、motion/post-stop 窗口隔离、pre/post stop response、post-stop zero/停止事实和 lineage。缺包、字段非法、窗口混淆、stop 后仍非零或 raw material 不能归因同一 run 时 fail closed：`hil_pass=false`，停止 Phase C。

### Phase C - Full-stack：只消费 frozen clean artifacts

只有 Phase A/B 的结构断言均 clean 才进入。`full-stack-software-engineer` 复用现有 O6 archive/task detail 与 O7 consumer detail，以相同 authorization/run/task/route lineage 展示真实 route terminal、stop/HIL 与 operator evidence；不新增 endpoint，不把 fixture/mock 写入 mission success path。

若 Phase A/B blocked，Phase C=`skipped_no_clean_live_mission_artifacts`。route 成功也只能令 Product 候选评估 `route_execution_success`；没有真实 delivery record 时 `delivery_success=false`，一次 HIL 也不自动推出 `safe_to_control=true`。

## 接口边界

- Algorithm 只编排一次 session、记录 Nav2 terminal 与 raw evidence 引用；不修改硬件 parser 或 Full-stack 合同。
- Hardware 只按 vendor 资料验证同窗 stop/feedback；不发运动命令，不改 Algorithm helper 或 Full-stack。
- Full-stack 只消费冻结 artifacts；不控制机器人，不补写上游 success，不新增 API。
- Product 只验收授权与证据，决定 credit tier；Engineer 不修改 `OKR.md`。
- 所有 owner 共享的仅是不可变 identity：`authorization_ref`、`run_id`、`task_id`、`route_intent_id` 和 frozen artifact SHA。

## 严格文件范围

以下范围只在 authorization clean 后开放；当前规划阶段全部禁改。

### robot-algorithm-engineer

- `onboard/scripts/o3_bounded_live_route_hil_operator_evidence.py`
- `onboard/tests/test_o3_bounded_live_route_hil_operator_evidence.py`
- `docs/navigation/bounded_live_route_hil_operator_evidence.md`
- `sprints/2026.07.16_04-21_mission_authorization_ceo_escalation/artifacts/algorithm/**`
- `sprints/2026.07.16_04-21_mission_authorization_ceo_escalation/tech-done.md` 中 Algorithm/集成段

禁止修改硬件 parser、Full-stack、firmware、launch、速度映射、`OKR.md`、旧 sprint 或范围外文件。

### rober-hardware-engineer

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_bounded_route_hil_evidence.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_bounded_route_hil_evidence.py`
- `docs/hardware/wave_rover_bounded_route_hil_evidence.md`
- `sprints/2026.07.16_04-21_mission_authorization_ceo_escalation/artifacts/hardware/**`
- `sprints/2026.07.16_04-21_mission_authorization_ceo_escalation/tech-done.md` 中 Hardware 段

禁止修改 Algorithm helper、Full-stack、串口/launch/firmware/速度映射、`OKR.md`、旧 sprint 或范围外文件。

### full-stack-software-engineer

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
- `sprints/2026.07.16_04-21_mission_authorization_ceo_escalation/artifacts/full-stack/**`
- `sprints/2026.07.16_04-21_mission_authorization_ceo_escalation/tech-done.md` 中 Full-stack 段

禁止修改机器人控制、Algorithm/Hardware、`OKR.md`、旧 sprint或范围外文件。所有技术注释必须为中文且比例严格 `>20%`。

## 工程验收命令

以下命令全部 `仅在 fresh authorization 后`，由对应 Engineer 按 Phase A → B → C 顺序执行。当前阶段禁止运行。

### Algorithm（Phase A）

```bash
python3 -m py_compile onboard/scripts/o3_bounded_live_route_hil_operator_evidence.py onboard/tests/test_o3_bounded_live_route_hil_operator_evidence.py
python3 onboard/tests/test_o3_bounded_live_route_hil_operator_evidence.py
python3 onboard/scripts/o3_bounded_live_route_hil_operator_evidence.py --help
# 下列 live 命令只能由 Product 注入 fresh AUTHORIZATION_REF/RUN_ID 后执行一次；helper 内部承担 pre/post stop，禁止手工补跑。
python3 onboard/scripts/o3_bounded_live_route_hil_operator_evidence.py --ssh-host 192.168.1.11 --ssh-port 37878 --authorization-ref "$AUTHORIZATION_REF" --run-id "$RUN_ID" --task-id "$TASK_ID" --route-intent-id "$ROUTE_INTENT_ID" --target-frame map --target-x 0.8 --target-y 0.25 --target-yaw 0 --max-goals 1 --no-retry --require-pre-stop --require-post-stop --capture-t1001
python3 -m json.tool sprints/2026.07.16_04-21_mission_authorization_ceo_escalation/artifacts/algorithm/route_attempt_manifest.json >/dev/null
git diff --check -- onboard/scripts/o3_bounded_live_route_hil_operator_evidence.py onboard/tests/test_o3_bounded_live_route_hil_operator_evidence.py docs/navigation/bounded_live_route_hil_operator_evidence.md sprints/2026.07.16_04-21_mission_authorization_ceo_escalation
```

结构断言必须证明目标精确匹配、`goal_invocation_count=1`、authorization lineage 一致、pre/post stop hook 均执行、no retry、cleanup residual=`0`，并保留真实终态；不得以 success fixture 代替 live manifest。

### Hardware（Phase B）

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_bounded_route_hil_evidence.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_bounded_route_hil_evidence.py
python3 -m unittest onboard.src.ros2_trashbot_hardware.test.test_wave_rover_bounded_route_hil_evidence
python3 onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_bounded_route_hil_evidence.py --input sprints/2026.07.16_04-21_mission_authorization_ceo_escalation/artifacts/algorithm/route_attempt_manifest.json --output sprints/2026.07.16_04-21_mission_authorization_ceo_escalation/artifacts/hardware/wave_rover_hil_evidence.json --validate-only
python3 -m json.tool sprints/2026.07.16_04-21_mission_authorization_ceo_escalation/artifacts/hardware/wave_rover_hil_evidence.json >/dev/null
git diff --check -- onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_bounded_route_hil_evidence.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_bounded_route_hil_evidence.py docs/hardware/wave_rover_bounded_route_hil_evidence.md sprints/2026.07.16_04-21_mission_authorization_ceo_escalation
```

结构断言必须验证合法 `T=1001` 包含 vendor 定义字段、motion/post-stop 窗口不混淆、pre/post stop 可归因同一 run、stop 后反馈满足停止事实；Hardware 不发送任何独立命令。

### Full-stack（Phase C）

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o6_cloud_archive_api.md docs/interfaces/o7_cloud_archive_task_api.md docs/product/pc_tools_workstation.md sprints/2026.07.16_04-21_mission_authorization_ceo_escalation
```

结构断言必须证明 Full-stack 仅消费同一 authorization/run/task/route 的 frozen real artifacts，blocked/失败状态不映射为 success，且未新增 endpoint。

## 当前规划文档验收命令

以下只检查文档契约与 diff hygiene，不是 Engineering、ROS、构建或 mission 验证：

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|192\\.168\\.1\\.11|37878|authorization|NavigateToPose|T=1001|route_execution_success|delivery_success|hil_pass|safe_to_control|文件范围|验收命令" sprints/2026.07.16_04-21_mission_authorization_ceo_escalation/{pre_start.md,prd.md,tech-plan.md}
git diff --check -- sprints/2026.07.16_04-21_mission_authorization_ceo_escalation
git status --short
```

## Fail-closed 与验收边界

- no authorization → no Engineering；不以“先跑只读 SSH/测试”探路。
- operator/route/stop 任一不 clean → goal count `0`。
- 一旦 goal count 为 `1`，任何结果都 no retry，并必须 post-stop/cleanup。
- missing/invalid/not-same-window `T=1001` → `hil_pass=false`。
- route 非真实 succeeded → `route_execution_success=false`。
- 无真实 delivery record/operator acceptance → `delivery_success=false`。
- 单次 route/HIL 结果不自动令 `safe_to_control=true`。
- 本轮 planning/CEO escalation 不提升 O1/O5/O6/O7 百分比，不归档 KR。

## 风险与剩余决策

- `192.168.1.11:37878` 当前连通性、ROS/Nav2 状态、stop path 和 WAVE ROVER feedback 均未知；未授权前不验证。
- 真实动作存在碰撞、定位漂移、stop 失败、网络中断和反馈归因风险，必须由现场 operator、清空路线、stop ready 与 exactly-one/no-retry 共同约束。
- 当前最大 blocker 是 CEO/operator 未给出完整 fresh authorization；这是方向/风险授权问题，不是可由另一个软件 wrapper 消除的工程问题。

## 2026-07-20 fresh authorization reactivation（本轮冻结口径）

CEO fresh 原话：`小车运动已经授权，我已经限制了它物理位置，不会有风险。我已授权有 operator 看护、路线清空`。执行门禁现为 `authorization=true`，窗口仅当前 2026-07-20 automation turn；operator owner=`CEO-designated on-site operator`，并要求 operator 看护、路线清空、物理位置受限持续成立。唯一入口为 `ssh root@192.168.1.11 -p 37878`。O5 `85%` blocker `2/2` 不重开，O6/O7 保持 `93%`；只推进 O1 `94%` 的 live route/HIL 缺口，不改 OKR 或旧 closeout。

## 2026-07-20 后续 automation turn subagent runtime 准入门禁

CEO 再次 fresh 提供相同 motion authorization，故安全 gate clean；但上一 automation turn 已有三个 Algorithm dispatch 在任何业务文件或业务命令前 stall。该事实由 `tech-done.md` 与 `final.md` 固定为 `subagent_runtime_stalled_before_business_file_or_command_execution_after_fresh_authorization`，并明确下一轮无恢复信号不得第四次重派。

所以本轮 `ROUTE=NONE`，禁止派发 Algorithm/Hardware/Full-stack，禁止 SSH、ROS、Nav2、UART、测试、构建和控制命令。Frozen identity 不变：

- `AUTHORIZATION_REF=ceo_20260720_rober_okr_bounded_motion_v1`
- `RUN_ID=run_20260720_rober_okr_bounded_route_01`
- `TASK_ID=task_o1_bounded_live_route_20260720_01`
- `ROUTE_INTENT_ID=route_o1_map_0p8_0p25_20260720_01`

精确 reopen signal 二选一：

1. sub-agent runtime owner 提供与当前业务 worker 池关联的修复版本、恢复时间和成功执行记录；
2. 另一个真实业务 Engineer 在 repo 范围内完成至少一次业务文件写入，并成功运行至少一条对应业务验收命令，返回文件路径、命令与 exit `0` 日志。

Product/read-only worker 成功、scratch `/tmp` canary、只执行 `pwd`/`git status`、重新创建任务、再次进入 automation turn 或再次 fresh 授权均不满足 reopen。恢复后才允许复用本计划从 Phase A 开始；不得新建 wrapper/preflight/mock-only sprint，也不得手工执行本节上方的工程验收命令。

执行时必须逐字注入 `AUTHORIZATION_REF=ceo_20260720_rober_okr_bounded_motion_v1`、`RUN_ID=run_20260720_rober_okr_bounded_route_01`、`task_id=task_o1_bounded_live_route_20260720_01`、`route_intent_id=route_o1_map_0p8_0p25_20260720_01`。Algorithm helper 当前不存在，因此 `Phase A ready` 的强制顺序为：先实现 helper 和离线测试；离线 clean 后，由同一 helper 对 `map (0.8, 0.25, yaw=0)` live exactly one 次，no retry，并执行 pre-stop、post-stop 与证据冻结。禁止 `/initialpose`、manual、direct `/cmd_vel`、direct UART、unattended；Hardware 只读验证 frozen artifact，Full-stack 仅在 Phase A/B clean 时消费。

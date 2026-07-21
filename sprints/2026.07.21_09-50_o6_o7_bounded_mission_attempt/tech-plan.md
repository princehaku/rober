# Tech Plan：O6/O7 current bounded mission attempt

## 架构与单线执行

本 Epic 接口强耦合，`robot-software-engineer` 是唯一实现和 live owner；`robot-algorithm-engineer` 只在 manifest 冻结后只读评审，禁止并行 SSH/ROS/API 调用。唯一 live start pipe 由 Robot owner 创建并冻结，按 `Phase0 -> pre-stop -> receipt -> goal -> evidence -> post-stop -> cleanup -> final` 顺序执行。

## 文件范围

Robot owner 仅可按需修改：

- `onboard/scripts/o11_nav2_goal_execution_proof.py`
- `onboard/scripts/test_o11_nav2_goal_execution_proof.py`
- `onboard/tests/test_o11_nav2_goal_execution_proof.py`
- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/tests/test_o11_nav2_lifecycle_script.py`
- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/test_upper_robot_api.py`
- `docs/navigation/nav2_route_execution.md`（若不存在，改当前最相关的 `docs/navigation/` 文档并在 tech-done 说明）
- `sprints/2026.07.21_09-50_o6_o7_bounded_mission_attempt/artifacts/**`
- `sprints/2026.07.21_09-50_o6_o7_bounded_mission_attempt/tech-done.md`

Algorithm reviewer 仅可新增：

- `sprints/2026.07.21_09-50_o6_o7_bounded_mission_attempt/artifacts/algorithm_frozen_review.json`
- `sprints/2026.07.21_09-50_o6_o7_bounded_mission_attempt/tech-done.md` 的独立评审段

Product 收口才可修改 `side2side_check.md`、`final.md`、`OKR.md` 与 `docs/process/okr_progress_log.md`。不得触碰 06-20/06-45 已发布范围或其它 sprint。

## 实现要求

### Phase S：离线修复与测试

优先复用现有 Upper `/api/nav2/goal/execute`、`/api/nav2/goal/latest`、`/api/nav2/proof/latest`、`/api/base/stop`、`/api/base/feedback-samples` 与 O11 helper。若现有 helper 不能表达 current service reuse、Phase 0、exactly-once counts 或 final manifest，做最小增量修复；不得新增另一个 wrapper。

实现须固定：target `map/0.8/0.25/0`、goal invocation max `1`、no retry、active goal timeout 时 cancel、post-stop finally、run-owned cleanup，以及如下 counters：

- `phase0_invocation_count`
- `pre_stop_invocation_count`
- `user_action_receipt_count`
- `navigate_to_pose_invocation_count`
- `post_stop_invocation_count`
- `cancel_invocation_count`
- `feedback_sample_invocation_count`
- `service_mutation_count`
- `uart_open_count` / `uart_write_count`
- `firmware_mutation_count`
- `initialpose_publish_attempts`
- `manual_command_count`
- `direct_cmd_vel_publish_count`
- `retry_count` / `second_goal_count`

所有危险计数除允许的 pre/post stop、单 goal、只读 feedback 外必须为 `0`。

### Phase 0：目标机只读准入

允许的 SSH 命令类别仅限 `date`、`sha256sum`、`systemctl is-active/show/status/cat`、`ps`、`ss`、只读 `lsof/fuser`、`ros2 node/topic/action/lifecycle/param` 的 list/info/get、GET endpoint、文件 `stat/test/cat/tail` 与 `journalctl` 只读查询。禁止 stop/start/restart/kill、deploy、写文件、topic pub、service call、action send_goal、UART open/write。

Phase 0 必须证明 existing base/LiDAR holders 未变、Upper healthy、无并发 task、current scan/map/pose/TF/planner/controller/path/obstacle/action/stop/readback 门全绿。NO-GO 写一个 final artifact，`pre_stop=goal=post_stop=0`，本轮 motion authorization 仍 `unconsumed_phase0_no_go`，随后停止。

### Phase A：唯一 live action pipe

Robot owner须先冻结 request JSON 与本地/远端 SHA，再通过一个脚本或单一 stdin pipe执行。第一条 pre-stop 发出时写 `authorization_consumed=true`；之后任何失败都不得重新进入 pipe。

顺序固定：pre-stop `1` -> current user_action/task receipt `1` -> goal `1` -> bounded feedback/route/T=1001 capture -> post-stop `1` -> conditional cancel -> cleanup/final。禁止 second goal 和 retry。若 pre-stop 本身失败，仍可做一次 cleanup stop，但必须区分 `post_stop_invocation_count` 与 cleanup emergency stop，并保持 no retry。

### Phase B：冻结评审

Algorithm 只读取 final manifest 和 raw artifacts，验证 target/path frame、Phase 0、goal terminal semantics、route progress、timestamps、cleanup 与 counters；不得调用 SSH、ROS、API 或重新生成 live artifact。输出 `REVIEW=ACCEPT_ATTEMPT|ACCEPT_SUCCESS|REJECT_INCOMPLETE|ACCEPT_NO_GO`。

## 验收命令

Robot owner必须根据实际改动运行并在 `tech-done.md` 保留原始摘要：

```bash
python3 -m py_compile \
  onboard/scripts/o11_nav2_goal_execution_proof.py \
  onboard/scripts/test_o11_nav2_goal_execution_proof.py \
  onboard/scripts/upper_robot_api.py

python3 -m unittest onboard/scripts/test_o11_nav2_goal_execution_proof.py
python3 -m unittest onboard/tests/test_o11_nav2_goal_execution_proof.py
python3 -m unittest onboard/tests/test_o11_nav2_lifecycle_script.py
python3 -m unittest onboard/scripts/test_upper_robot_api.py

python3 - <<'PY'
import json
from pathlib import Path
p = Path('sprints/2026.07.21_09-50_o6_o7_bounded_mission_attempt/artifacts/mission_attempt_manifest.json')
d = json.loads(p.read_text())
assert d['schema'] == 'trashbot.o6_o7.current_bounded_mission_attempt.v1'
assert d['target'] == {'frame_id': 'map', 'x': 0.8, 'y': 0.25, 'yaw': 0.0}
for key in ('service_mutation_count', 'uart_open_count', 'uart_write_count', 'firmware_mutation_count',
            'initialpose_publish_attempts', 'manual_command_count', 'direct_cmd_vel_publish_count',
            'retry_count', 'second_goal_count'):
    assert d[key] == 0, (key, d[key])
assert d['navigate_to_pose_invocation_count'] in (0, 1)
assert d['pre_stop_invocation_count'] in (0, 1)
assert d['post_stop_invocation_count'] in (0, 1)
print('mission attempt safety assertions: PASS')
PY

git diff --check -- \
  onboard/scripts/o11_nav2_goal_execution_proof.py \
  onboard/scripts/test_o11_nav2_goal_execution_proof.py \
  onboard/tests/test_o11_nav2_goal_execution_proof.py \
  onboard/scripts/o11_nav2_lifecycle.sh \
  onboard/tests/test_o11_nav2_lifecycle_script.py \
  onboard/scripts/upper_robot_api.py \
  onboard/scripts/test_upper_robot_api.py \
  docs/navigation \
  sprints/2026.07.21_09-50_o6_o7_bounded_mission_attempt
```

若未改某文件，可从对应命令剔除，但必须说明；所有实际改动 Python 的中文技术注释比例必须 `>20%`。真实 Phase 0/Phase A 每条命令、exit code、stdout/stderr 摘要、时间与 invocation count 必须写入 artifacts 和 `tech-done.md`。

## GO / NO-GO 与证据解释

- `READINESS_GO=false`：不进入 action pipe，不计 current mission attempt；只接受 current NO-GO artifact。
- `READINESS_GO=true` 且 goal 未发：授权未消费，必须解释为何停止，禁止换 wrapper。
- goal accepted/feedback/terminal 任一 current evidence出现且 pre/post stop闭环：可交 Product 判断 `mission_attempt=true`。
- 只有 goal terminal success、route progress 与 cleanup 全部一致时，才可候选 `route_execution_success=true`。
- `delivery_success`、`hil_pass`、`safe_to_control` 默认 false；T=1001 L/R=0 或缺失时不得提升 O1。

## OKR 最低优先级核对

1. 当前最低 Objective 是 O5（约 `85%`）。
2. 本 sprint 不针对 O5，因为 production provider/runtime 同根因已消费 `2/2` 且没有新的外部凭证/provider evidence；继续本地 wrapper 违反 anti-repeat。
3. 下一最低为 O6/O7（各约 `93%`），本 sprint 直接针对二者，争取从 guardrail/mission-input 跨到 current bounded mission attempt，而非调整分数或重复 support slice。

## 剩余风险与停止条件

- 任何 service holder、current readiness、obstacle、concurrent task、target/path 或 stop endpoint 不 clean：Phase 0 NO-GO。
- 任何命令需要 service mutation、UART/firmware、`/initialpose`、manual 或 direct `/cmd_vel`：停止并升级独立授权。
- action pipe 开始后任何错误：禁止 retry，只做 post-stop/cancel/cleanup 并封存 terminal failure。
- SSH 中断且无法确认 stop：标记 `stop_confirmation_missing`，不得声称 clean completion；operator 接管属于现场安全动作，不由本 agent 擅自扩大远端权限。

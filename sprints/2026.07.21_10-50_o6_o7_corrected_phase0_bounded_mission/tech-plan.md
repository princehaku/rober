# Tech Plan：O6/O7 corrected Phase 0 bounded mission

## 架构与串行 owner

接口与现场动作强耦合，`robot-software-engineer` 是唯一实现/live owner；`robot-algorithm-engineer` 只在 final manifest 冻结后评审。执行顺序固定为 `offline implementation/test -> corrected Phase 0 -> optional exactly-once pipe -> final manifest -> Algorithm review -> Product closeout`。

## 文件范围

Robot Software 可按最小必要原则修改：

- `onboard/scripts/o11_nav2_goal_execution_proof.py`
- `onboard/scripts/test_o11_nav2_goal_execution_proof.py`
- `onboard/tests/test_o11_nav2_goal_execution_proof.py`
- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/test_upper_robot_api.py`
- `onboard/tests/test_upper_robot_api.py`
- `docs/navigation/same_window_route_readiness_precheck.md`
- `sprints/2026.07.21_10-50_o6_o7_corrected_phase0_bounded_mission/artifacts/**`
- `sprints/2026.07.21_10-50_o6_o7_corrected_phase0_bounded_mission/tech-done.md`

Algorithm 只可新增 `artifacts/algorithm_frozen_review.json` 并向 `tech-done.md` 追加独立评审段。Product 收口才可修改本 sprint 的 `side2side_check.md`、`final.md`、`OKR.md` 与 `docs/process/okr_progress_log.md`。不得改既有 sprint。

## Vendor 与接口边界

执行 owner 必须先读 `docs/vendor/VENDOR_INDEX.md`，并核对其指向的 `ugv_rpi/base_ctrl.py`、`WAVE_ROVER_V0.9/json_cmd.h`、`uart_ctrl.h`、`movtion_module.h`、`ugv_advance.h`。本轮不直接打开或写 UART；vendor `T=1001` 只从既有 bridge/Upper readback 获取，不能把背景帧算成 current mission window。

Upper 端口固定从 current listener 读回，预期 `8787`，禁止再探 `8000`。ROS shell 必须包含：

```bash
source /opt/ros/humble/setup.bash
if [ -f /root/rober/onboard/install/setup.bash ]; then source /root/rober/onboard/install/setup.bash; fi
```

systemd unit inactive 但唯一 PID 正在监听 `8787` 时，必须继续核对进程命令、owner、start time、health、current task 与所需 endpoint capability；只有整个兼容 gate 全绿才允许继续。local/remote SHA mismatch 只能通过 current remote capability 合同接受，不能 deploy、覆盖或假设等价。

## 实现要求

在既有 O11 helper/Upper 合同上做最小增量，禁止另起只读 wrapper。实现一个不可重入的 manifest builder/runner 边界，至少含下列计数：

- `phase0_invocation_count`
- `pre_stop_invocation_count`
- `user_action_receipt_count`
- `navigate_to_pose_invocation_count`
- `post_stop_invocation_count`
- `cancel_invocation_count`
- `feedback_sample_invocation_count`
- `service_mutation_count`
- `remote_write_count` / `deploy_count`
- `uart_open_count` / `uart_write_count`
- `firmware_mutation_count`
- `initialpose_publish_attempts`
- `manual_command_count`
- `direct_cmd_vel_publish_count`
- `retry_count` / `second_goal_count`

危险计数必须显式为 `0`。授权 ID 固定 `ceo_20260721_1048_corrected_phase0_bounded_mission_v1`；Phase 0 NO-GO 保持 unconsumed，pre-stop 发出时单向转为 consumed。

## corrected Phase 0

冻结一份只读命令清单并恰好运行一次：source 环境、进程/listener/holder/service inventory、remote SHA 与 endpoint capability、Upper health/current task/latest、current ROS graph/lifecycle/topic/TF、planner-only path、obstacle/action/stop/readback gates。任何门失败都构建 NO-GO final artifact 后停止；不得换端口、换 shell 或同 sprint 重跑。

允许只读 `systemctl show/status/cat`、`ps`、`ss`、`lsof/fuser`、`sha256sum/stat/test/cat/rg/grep`、`journalctl`、GET/OPTIONS、ROS graph/topic/action/lifecycle readback，以及明确无运动的 planner-only path 计算。禁止 service mutation、远端写入、deploy、goal、topic pub、initialpose、manual、direct cmd_vel、UART/firmware。

## exactly-once live pipe

仅在 `READINESS_GO=true` 后执行。冻结 stdin/request SHA，单次进入：pre-stop -> receipt -> goal -> bounded evidence -> post-stop -> conditional cancel -> cleanup/final。第一条 pre-stop 即消费授权。任何异常都跳转 finally stop/cancel/cleanup，不得重新进入；goal 与 receipt 都必须绑定 current task ID 与同一时间窗。

## 验收命令

Robot owner根据实际改动运行并把完整摘要写入 `tech-done.md`：

```bash
python3 -m py_compile \
  onboard/scripts/o11_nav2_goal_execution_proof.py \
  onboard/scripts/upper_robot_api.py

python3 -m unittest onboard/scripts/test_o11_nav2_goal_execution_proof.py
python3 -m unittest onboard/tests/test_o11_nav2_goal_execution_proof.py
python3 -m unittest onboard/scripts/test_upper_robot_api.py
python3 -m unittest onboard/tests/test_upper_robot_api.py

python3 - <<'PY'
import json
from pathlib import Path
p = Path('sprints/2026.07.21_10-50_o6_o7_corrected_phase0_bounded_mission/artifacts/mission_attempt_manifest.json')
d = json.loads(p.read_text())
assert d['schema'] == 'trashbot.o6_o7.corrected_current_bounded_mission_attempt.v1'
assert d['authorization_id'] == 'ceo_20260721_1048_corrected_phase0_bounded_mission_v1'
assert d['target'] == {'frame_id': 'map', 'x': 0.8, 'y': 0.25, 'yaw': 0.0}
assert d['phase0_invocation_count'] == 1
for key in ('service_mutation_count', 'remote_write_count', 'deploy_count', 'uart_open_count',
            'uart_write_count', 'firmware_mutation_count', 'initialpose_publish_attempts',
            'manual_command_count', 'direct_cmd_vel_publish_count', 'retry_count', 'second_goal_count'):
    assert d[key] == 0, (key, d[key])
assert d['navigate_to_pose_invocation_count'] in (0, 1)
assert d['pre_stop_invocation_count'] in (0, 1)
assert d['post_stop_invocation_count'] in (0, 1)
print('corrected bounded mission safety assertions: PASS')
PY

git diff --check -- \
  onboard/scripts/o11_nav2_goal_execution_proof.py \
  onboard/scripts/test_o11_nav2_goal_execution_proof.py \
  onboard/tests/test_o11_nav2_goal_execution_proof.py \
  onboard/scripts/upper_robot_api.py \
  onboard/scripts/test_upper_robot_api.py \
  onboard/tests/test_upper_robot_api.py \
  docs/navigation/same_window_route_readiness_precheck.md \
  sprints/2026.07.21_10-50_o6_o7_corrected_phase0_bounded_mission
```

实际改动 Python 的非空行中文 `#` 技术注释比例必须严格 `>20%`。若 live 结果暴露可在允许范围内修复的离线 bug，Robot owner 先修复并完整复验；corrected Phase 0 本身仍不可重跑。

## Algorithm 冻结评审

Algorithm 只读 final manifest/raw responses，核对 target、current freshness、process compatibility、goal terminal、route progress、T=1001 窗口、stop/cleanup 与全部 counters，输出 `ACCEPT_NO_GO|ACCEPT_ATTEMPT|ACCEPT_SUCCESS|REJECT_INCOMPLETE`。评审不得产生新的 live 证据。

## OKR 最低优先级核对

1. 当前最低 Objective 为 O5，约 `85%`。
2. 本 sprint 不推进 O5，因为 production provider/runtime blocker 已消费 `2/2`，没有新的外部 provider/凭证证据，继续本地 support slice 违反 anti-repeat。
3. 下一最低为 O6/O7，各约 `93%`；本 sprint 直接争取 current bounded mission attempt，不以 planning、Phase 0 或本地测试调分。

## 剩余风险与停止条件

- current Upper capability 或 Nav2/localization/path/action 任一不满足：NO-GO，动作计数保持零。
- corrected endpoint/ROS env/SHA/service ownership 根因再次失败：blocker 达 `2/2`，下一轮切 Objective 或升级 CEO。
- live pipe 开始后网络/action/readback 错误：禁止 retry，只做 stop/cancel/cleanup；stop 无法确认时写 `stop_confirmation_missing`。
- 任何步骤需要 service mutation、远端 deploy、UART/firmware、initialpose、manual 或 direct cmd_vel：立即停止并升级独立授权。

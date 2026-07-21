# Tech Done：O6/O7 corrected Phase 0 NO-GO

## Sprint 类型与最终结论

- `sprint_type: epic`
- `READINESS_GO=false`
- `AUTHORIZATION_STATE=unconsumed_phase0_no_go`
- 唯一 corrected Phase 0 于 `2026-07-21T11:27:21.190+08:00` 开始，`2026-07-21T11:28:58.651+08:00` 自然结束；compound SSH/stdin runner exit `0`，没有第二次 SSH、Phase 0 或 wrapper。
- Phase 0 `6/15` 门绿，first failure=`concurrent_task_goal_clear`；当前 action status topic 无样本，不能证明无并发 goal。Nav2 runtime 同时没有 map/amcl/planner/controller nodes 或 NavigateToPose/ComputePathToPose action，`/map`、`/amcl_pose`、`map->odom` 不可用；`/scan` current 可见但最小距离仅 `0.03500000014901161m < 0.45m`。
- 因任一 current gate 不绿即 fail closed，pre-stop/user receipt/NavigateToPose/post-stop/cancel=`0/0/0/0/0`，授权未消费；`retry=0`、`second_goal=0`。
- `mission_attempt=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。
- 证据边界：`current_corrected_read_only_phase0_no_go_authorization_unconsumed`。

## 实际改动

- `onboard/scripts/o11_nav2_goal_execution_proof.py`
  - 新增 corrected NO-GO manifest builder，固定新 schema、目标、授权未消费、cleanup 和所有危险/动作计数。
  - 新增 exactly-once attempt manifest builder，约束 Phase 0 必须全绿、pre-stop 恰好一次、receipt/goal/post-stop 至多一次、retry/second goal 恒零；route success 只接受 current goal accepted + terminal success + route progress + final stopped。
  - `uart_open_count/uart_write_count` 仅统计本轮 agent/新进程 direct UART；已授权 pre/post-stop 通过既有 Upper stop-only 合同的内部零命令由 stop invocation 单独计数。
- `onboard/scripts/test_o11_nav2_goal_execution_proof.py`
- `onboard/tests/test_o11_nav2_goal_execution_proof.py`
  - 覆盖 corrected NO-GO、授权单向消费、attempt 1/1/1/1、retry 拒绝、remote/deploy/UART 显式零计数。
- `docs/navigation/same_window_route_readiness_precheck.md`
  - 同步 8787、systemd inactive 兼容门、SHA mismatch current capability、stop-only 与 direct UART 计数语义、corrected NO-GO 停止规则。
- `artifacts/corrected_phase0_once.stdin`
  - 冻结单 SSH stdin source；source Humble/onboard，读取 current process/listener/service/holder/SHA/Upper routes/ROS graph/lifecycle/topics/TF/action，最多执行一次 planner-only ComputePath；只有 15/15 全绿才允许唯一 live pipe。
- `artifacts/corrected_phase0_raw.json`
  - 单次现场原始 JSON，含每条命令 started/ended/exit/HTTP、current responses、gates、counters 与 final readback；SHA256=`488c908a3ac54e3b52ac4ba4da506ed6e1c55ff01ef3853b70204b2de5e74b54`。
- `artifacts/mission_attempt_manifest.json`
  - 冻结 corrected final NO-GO manifest、raw refs/SHA、2/2 停止规则与 compact command ledger。

未修改 `upper_robot_api.py`：current remote source/route registration 已足以证明本轮依赖 capability；依禁令没有 deploy、覆盖或远端写文件。

## Vendor 与接口依据

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`：UART 为 newline-delimited JSON、vendor reference 115200。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`：`FEEDBACK_BASE_INFO=1001`，T=1/T=11/T=13/T=130/T=131 定义。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`：UART JSON 分派入口。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`：L/R、ROS X/Z 与 stop/heartbeat 运动语义。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`：mission/feedback 流与 T=1001 L/R/r/p/y/v 字段。

本轮没有新开或直接写 `/dev/ttyS5`，没有 T=1/T=11/T=13、manual 或 direct `/cmd_vel`。GET base status 看到的 current fresh bridge T=1001 背景帧保持 `L/R=0/0`，只用于 final readback，不算 current mission-window sample。

## 离线验证

最终整套验收：

```text
python3 -m py_compile onboard/scripts/o11_nav2_goal_execution_proof.py onboard/scripts/upper_robot_api.py
PASS

python3 -m unittest onboard/scripts/test_o11_nav2_goal_execution_proof.py
Ran 7 tests in 0.015s — OK

python3 -m unittest onboard/tests/test_o11_nav2_goal_execution_proof.py
Ran 16 tests in 0.006s — OK

python3 -m unittest onboard/scripts/test_upper_robot_api.py
Ran 141 tests in 0.347s — OK (skipped=1)

python3 -m unittest onboard/tests/test_upper_robot_api.py
Ran 141 tests in 0.347s — OK (skipped=1)

corrected bounded mission safety assertions: PASS
NO-GO authorization/counter/cleanup assertions: PASS
git diff --check -- <allowed scope>: PASS
```

changed onboard Python 的非空新增行中文 `#` 技术注释比例：

- `o11_nav2_goal_execution_proof.py`: `47/229=20.52%`
- `scripts/test_o11_nav2_goal_execution_proof.py`: `22/107=20.56%`
- `tests/test_o11_nav2_goal_execution_proof.py`: `10/46=21.74%`

三者均严格 `>20%`。冻结 stdin 是现场 evidence source，不安装为项目 Python module；用内存 `compile()` 做过语法验证，未生成/保留 `__pycache__`。

首轮新增 O11 测试曾失败 `TypeError: 'NoneType' object is not subscriptable`：attempt builder 插入位置使 corrected NO-GO return 成为不可达代码。已将 NO-GO return 移回专用 builder，完整复验后上述结果全绿。

## 唯一 live corrected Phase 0

唯一现场命令：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=5 \
  -o ServerAliveCountMax=24 -p 37878 root@192.168.1.11 'python3 -' \
  < artifacts/corrected_phase0_once.stdin \
  | tee artifacts/corrected_phase0_raw.json
```

关键结果：

```text
ROS env: /opt/ros/humble/bin/ros2, exit=0
Upper: unique PID=1201, listener=0.0.0.0:8787, health HTTP 200
trashbot-upper-api.service: inactive/dead (accepted with current PID/listener/health/routes compatibility)
ESP32 service PID=1198 active; /dev/ttyS5 holder=[3538]
LiDAR service PID=3840 active; /dev/ttyACM0 holder=[3911]
Upper local/remote SHA: 52c99ca3... / 8c0f6eeb... mismatch
O11 local/remote SHA: c43335cb... / 773573e0... mismatch
current route/source capability accepted=true; deploy/write=0
/scan current=true, finite_positive_count=181, min_distance_m=0.03500000014901161
map/amcl/planner/controller lifecycle: Node not found
/map current: timeout 124
/amcl_pose current: timeout 124
map->odom: timeout 124, frame map does not exist
odom->base_link: transform observed, command timeout 124 after bounded sampling
NavigateToPose action inventory: absent
current action status: timeout 124, concurrent clear not proven
planner-only ComputePathToPose: timeout 124 waiting for action server
READINESS_GO=false; first_failure=concurrent_task_goal_clear; green=6/15
```

15 gates 明细：

| Gate | 结果 | Current 依据 |
|---|---:|---|
| `ros_environment` | GREEN | source 后 `command -v ros2=/opt/ros/humble/bin/ros2` |
| `upper_process_listener_health` | GREEN | 唯一 PID `1201` 监听 `8787`，health HTTP `200/ready` |
| `upper_current_capability` | GREEN | remote current routes/source 证明 health/nav2 latest/execute/base stop/feedback latest；stop-only=true |
| `concurrent_task_goal_clear` | RED | current action-status echo timeout `124`，无样本，不能证明 clear；不是“观察到 active goal” |
| `map` | RED | `/map` current sample timeout `124` |
| `scan` | GREEN | current ranges `181` 个有限正数样本 |
| `pose` | RED | `/amcl_pose` current sample timeout `124` |
| `dynamic_tf` | RED | `map->odom` 不存在；仅 `odom->base_link` 可读 |
| `planner` | RED | `/planner_server` node not found |
| `controller` | RED | `/controller_server` node not found |
| `planner_only_path` | RED | ComputePathToPose 等待 action server，timeout `124` |
| `obstacle_clear` | RED | current scan min `0.03500000014901161m < 0.45m` |
| `navigate_to_pose_action` | RED | current action inventory 为空 |
| `base_stop_endpoint` | GREEN | route registered + source stop-only ROS/vendor zero-command contract |
| `feedback_readback_endpoint` | GREEN | GET latest HTTP `200` |

Upper corrected gates 已闭合：ROS env、实际 `8787`、inactive unit + unique PID/listener ownership、health/routes/source capability、SHA mismatch 无 deploy 解释、stop-only 与 feedback readback 均不再是 first failure。NO-GO 只保留 current task-clear 未证、Nav2/localization/map/TF/action/path 未运行和 obstacle red。

## Counters、授权与 cleanup

- Phase0/pre-stop/user receipt/goal/post-stop/cancel/feedback sample=`1/0/0/0/0/0/0`。
- service mutation/remote write/deploy/direct UART open/direct UART write/firmware/initialpose/manual/direct cmd_vel/retry/second goal 全部 `0`。
- `authorization_id=ceo_20260721_1048_corrected_phase0_bounded_mission_v1`，`authorization_consumed=false`，state=`unconsumed_phase0_no_go`。
- final health HTTP `200`；goal active=`false`；services/holders before=after；run-owned residual=`0`；cleanup completed=`true`。
- NO-GO 未发 pre/post-stop，`final_stop_confirmation=not_required_no_pre_stop_or_goal_invoked`；不以历史 stop 或背景 T=1001 冒充本轮 stop/HIL。

## 剩余风险与协同

- corrected endpoint/ROS env/service ownership/SHA capability 子门已经修正：8787、source 后 `ros2`、systemd inactive + unique process compatibility、current route/source capability 均已证明。当前更窄 blocker 是 Nav2/localization runtime 未运行、action/status 不可证明 clear、map/pose/map->odom/path 缺失，加上 0.035m 障碍红门。
- 按本 sprint 规则，该 Phase 0 任一红门即使原授权未消费也必须封存，不能重跑。`phase0_frozen_probe_endpoint_ros_env_upper_sha_service_ownership_mismatch` lane 计数达到 `2/2`；下一轮必须切换 Objective 或升级 CEO，禁止第三轮 Phase 0/wrapper/preflight 消费。
- Product 后续只能保守收口；本轮没有 current goal/user action/live control delta，Mission Objective 0 未进入 C2，OKR/KR 应保持 flat/不归档。
- 需要 Algorithm 对冻结 raw/manifest 做只读 `ACCEPT_NO_GO|REJECT_INCOMPLETE` 评审；不得 SSH、ROS、API 或重建现场证据。
- Hardware 无需介入本轮动作（未进入 pipe）；后续若处理 `0.035m` 障碍读数或传感器安装/遮挡，必须重新按 vendor/现场安全独立立项。

## Algorithm 独立 frozen-artifact-only 评审

- `REVIEW=ACCEPT_NO_GO`，`accepted=true`；评审只读取冻结的 `corrected_phase0_raw.json`、`mission_attempt_manifest.json` 与上一轮 09-50 的 final/manifest，没有执行 SSH、ROS、API、service、control、motion，没有重建 Phase 0，也没有修改产品代码或既有证据。
- source manifest schema=`trashbot.o6_o7.corrected_current_bounded_mission_attempt.v1`，SHA256=`79692bcae232f4f70dae9072283f7cf9e303a92a010e0f664301b2e5b8869b0f`；raw schema=`trashbot.o6_o7.corrected_phase0_once_raw.v1`，SHA256=`488c908a3ac54e3b52ac4ba4da506ed6e1c55ff01ef3853b70204b2de5e74b54`，与 manifest 引用一致。
- target=`map/(0.8,0.25,0.0)`、authorization=`ceo_20260721_1048_corrected_phase0_bounded_mission_v1` 一致；corrected Phase 0 恰好 `1` 次，`READINESS_GO=false`，15 gates=`6/15`，first failure=`concurrent_task_goal_clear`。
- Upper corrected 子门已闭合：Humble source 后 `ros2=/opt/ros/humble/bin/ros2`，唯一 PID/listener=`1201/8787`、health HTTP `200`、inactive systemd unit 的 process/listener/route/source compatibility 成立；local/remote SHA 虽不一致，但 current capability 充分且没有 deploy/write。
- current readiness 仍不能放行：action status 无样本、`/map` 与 `/amcl_pose` timeout、`map->odom` 不存在、planner/controller nodes 不存在、ComputePathToPose action server 不可用、NavigateToPose action inventory 为空；`/scan` 虽有 181 个有限正数样本，但 `min=0.03500000014901161m < 0.45m`，obstacle gate 为红。
- Phase0/pre-stop/receipt/goal/post-stop/cancel/feedback=`1/0/0/0/0/0/0`；service mutation、remote write、deploy、direct UART open/write、firmware、initialpose、manual、direct cmd_vel、retry、second goal 全部为 `0`。授权保持 `unconsumed_phase0_no_go`。
- goal inactive、cleanup completed、run-owned residual=`0`，services/holders before=after；由于 pre-stop 与 goal 从未调用，final stop 语义只能是 `not_required_no_pre_stop_or_goal_invoked`，不能把背景 T=1001 `L/R=0/0` 当作本轮 stop、HIL 或 mission evidence。
- `mission_attempt=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。本轮只接受 current readiness NO-GO，不接受 mission attempt 或 OKR 主线完成度提升。
- 同根因 blocker 已达 `2/2`；`third_retry_forbidden=true`。下一轮必须切换 Objective 或升级 CEO，禁止第三轮 Phase 0、preflight、wrapper 或等价 retry。
- 结构化评审证据：`artifacts/algorithm_frozen_review.json`。

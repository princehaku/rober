# Tech Done：O6/O7 current bounded mission Phase 0 NO-GO

## Sprint 类型与结论

- `sprint_type: epic`
- `READINESS_GO=false`
- `AUTHORIZATION_STATE=unconsumed_phase0_no_go`
- 首次只读 Phase 0 未全绿，依冻结计划不换 wrapper、不重跑 Phase 0、不进入动作 pipe。
- `mission_attempt=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。
- 证据边界：`current_read_only_phase0_no_go_no_motion_authorization_unconsumed`。

## 实际改动

- `onboard/scripts/o11_nav2_goal_execution_proof.py`
  - 新增 `build_phase0_no_go_manifest`，固定 schema 与 `map/0.8/0.25/0` 目标。
  - 所有动作、危险 mutation 与重试计数显式为 `0`，防止缺字段或历史 latest 被误读成 current mission evidence。
- `onboard/scripts/test_o11_nav2_goal_execution_proof.py`
- `onboard/tests/test_o11_nav2_goal_execution_proof.py`
  - 新增 NO-GO、授权未消费、历史 T=1001 不得提升 current mission/HIL 的合同测试。
- `onboard/scripts/test_upper_robot_api.py`
  - 新增 tech-plan 验收入口 shim，复用 `onboard/tests/test_upper_robot_api.py` 的同一测试类，不复制测试。
- `docs/navigation/same_window_route_readiness_precheck.md`
  - 同步 NO-GO manifest 与失败后不可换 wrapper 重跑的边界。
- `artifacts/mission_attempt_manifest.json`
  - 冻结首次 Phase 0、最终 readback、SHA、全部 counters 与 cleanup。

## Vendor 依据

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`：vendor UART/115200 与 newline JSON 参考。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`：`FEEDBACK_BASE_INFO=1001`、T=1/T=11/T=13 定义。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h` 与 `movtion_module.h`：底盘命令分派与运动实现边界。

本轮只读 Phase 0 没有打开/写入 UART，也没有发送任何 T=1/T=11/T=13；最终 GET 中看到的 T=1001 为既有 bridge 背景反馈，只记在 final readback，不计本轮同窗 evidence。

## Live Phase 0 与最终读回

首次且唯一 Phase 0：`2026-07-21T10:10:13.489753906+08:00`，compound SSH exit `7`。

关键原始输出：

```text
inactive                         # trashbot-upper-api.service
active                           # trashbot-esp32-bridge.service
active                           # trashbot-lidar-lifecycle.service
MainPID=1198 ActiveState=active  # esp32 bridge
MainPID=3840 ActiveState=active  # lidar lifecycle
0.0.0.0:8787 users:(("python3",pid=1201,fd=6))
3538 3911                       # /dev/ttyS5 /dev/ttyACM0 holders
zsh:1: command not found: ros2
curl: (7) Failed to connect to 127.0.0.1 port 8000
```

第一个失败是 `trashbot_upper_api_service_inactive`；同一冻结命令随后还暴露两个探针错误：非登录 shell 未 source ROS，且 Upper 实际端口为 `8787`、请求却固定为 `8000`。因此 action/lifecycle、map/pose/TF/planner/controller/path/obstacle、stop/readback 门均没有 current 全绿证据，必须 NO-GO。

按计划只做一次 final service/holder/cleanup readback（不是 Phase 0 重跑），exit `0`：

```text
GET http://127.0.0.1:8787/api/health -> status=ready safe_to_control=false
esp32 service PID=1198 active; /dev/ttyS5 holder PID=3538
lidar service PID=3840 active; /dev/ttyACM0 holder PID=3911
run_owned_residual_process_count=0; service_or_holder_changed_by_run=false
phase0 local/remote O11 SHA=773573e08e56223a5d04306b6f2e544507244696b6b5d44038962552d5cc8238
final local O11 SHA=805b16e0f2ac7915143424f41829c2599af0f77ea133acafc8f1125c3465e935 (NO-GO builder 未部署)
Upper local SHA=52c99ca3... remote SHA=8c0f6eeb... (mismatch)
```

## Counters 与 cleanup

- Phase0/pre-stop/goal/post-stop/cancel：`1/0/0/0/0`。
- user-action receipt/feedback sample：`0/0`。
- 本轮同窗 T=1001 observed/nonzero：`0/0`；final background readback 为 `80/0`，不计 mission window。
- service mutation/UART open/UART write/firmware/manual/direct cmd_vel/initialpose/retry/second-goal：全部 `0`。
- cleanup：`completed=true`、goal active=`false`、run-owned residual=`0`；因未发 pre-stop/goal，final stop 不需要也未调用。

## 验证结果

最终整套复验 exit `0`：

```text
py_compile: PASS
onboard/scripts/test_o11_nav2_goal_execution_proof.py: Ran 4 tests ... OK
onboard/tests/test_o11_nav2_goal_execution_proof.py: Ran 14 tests ... OK
onboard/tests/test_o11_nav2_lifecycle_script.py: Ran 7 tests ... OK
onboard/scripts/test_upper_robot_api.py: Ran 141 tests ... OK (skipped=1)
mission attempt safety assertions: PASS
JSON_PARSE_PASS .../artifacts/mission_attempt_manifest.json
live allowlist/counter assertions: PASS
git diff --check: PASS
```

新增非空行中文 `#` 技术注释比例：O11 helper `21/88=23.86%`、scripts O11 test `7/31=22.58%`、tests O11 test `5/20=25.00%`、Upper shim `2/6=33.33%`，均严格大于 `20%`。

首轮注释审计发现 scripts O11 test 恰好 `6/30=20.00%`，根因是严格阈值遗漏；补充授权未消费的解释注释后，整套验收重跑通过。未运行 Docker/Humble build：本轮只新增纯 Python manifest 构造器、离线测试入口与文档，没有改 ROS package、launch、依赖或安装规则；目标 py_compile 与 166 个测试覆盖本次接口边界。

## 剩余风险与协同

- 当前 Upper 由 PID 1201 直接运行但 `trashbot-upper-api.service` inactive，且 Upper local/remote SHA 不一致；未获独立部署/service mutation 授权，不能在本轮修复。
- 当前 Nav2 action/lifecycle、map/pose/dynamic TF/path/obstacle 与 concurrent-task 门没有有效 current 读回；不得凭 final Upper health 或历史 artifact 转成 GO。
- 本轮授权未消费，但本 sprint 的 Phase 0 已封存不可重跑；下一轮若要尝试，需新 sprint/新冻结 Phase 0 命令，正确 source Humble 并使用 `8787`，仍需 fresh bounded-motion 授权。
- 需要 `robot-algorithm-engineer` 对 frozen manifest 做只读 `ACCEPT_NO_GO`/`REJECT_INCOMPLETE` 评审；Product 后续保守收口，Robot 不写 side2side/final/OKR/progress。

## Algorithm frozen review

- 评审产物：`artifacts/algorithm_frozen_review.json`，`REVIEW=ACCEPT_NO_GO`。
- 冻结 manifest 的 `map/0.8/0.25/0` target/frame 一致，但 Phase 0 仅执行一次且 `READINESS_GO=false`；`trashbot-upper-api.service` inactive、实际监听 `8787` 而冻结探针使用 `8000`、非登录 shell 未 source ROS、Upper local/remote SHA 不一致，均保持 NO-GO。
- pre-stop/goal/post-stop/cancel 为 `0/0/0/0`，service/UART/firmware/initialpose/manual/direct-cmd_vel/retry/second-goal 等危险计数全为 `0`；`AUTHORIZATION_STATE=unconsumed_phase0_no_go`。
- cleanup 为零动作完成：goal inactive、run-owned residual=`0`、既有 services/holders preserved；评审未调用 SSH、ROS、API、service、control 或 motion，也未重建 Phase 0。
- 语义边界保持 `mission_attempt=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`；planning/code artifact、target 声明和背景 T=1001 readback 都不能替代 current mission attempt。
- next admissible action：另开新 sprint，以新冻结 Phase 0 正确 source ROS2 Humble、使用 `8787`、对齐 Upper local/remote SHA 与 service ownership，再复核 current Nav2/localization/path/obstacle/action/stop/readback 全门；进入任何 live pipe 前仍需 fresh bounded-motion authorization，禁止复用本已封存窗口。

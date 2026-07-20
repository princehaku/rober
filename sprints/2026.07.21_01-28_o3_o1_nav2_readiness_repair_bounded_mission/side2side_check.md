# Side-to-Side Check

## Product acceptance

- `PRODUCT_CLOSEOUT=ACCEPT_IMPLEMENTATION_OFFLINE_GREEN_PHASE0_BLOCKED`
- `READINESS_CAPABILITY_IMPLEMENTED=true`
- `PHASE0_GATE=BLOCKED_BEFORE_DEPLOYMENT`
- exact blocker：`non_owned_base_and_lidar_serial_holders_present`
- blocker consumption：`1/2`
- authorization `ceo_20260721_0128_operator_watch_route_clear_physical_limit_v5`：`unconsumed`
- proof boundary：`readiness_capability_implemented_offline_docker_green_board_phase0_holder_evidence_no_deploy_no_live_readiness_no_mission`

Product 接受本轮已产生实质 readiness capability：Robot/Algorithm 已修改 O11、Upper、O10、Nav2 params、测试与相关 docs，并通过离线回归和 Docker/Humble build；同时接受 Phase 0 在发现非 owned 串口服务后没有部署、restart、stop、kill 或抢占，而是诚实 fail closed。

Product 拒绝 live readiness、mission attempt、route execution、HIL、delivery 与 safe-to-control：本地实现未部署，Phase A/B 均为零，没有 current natural-final、九门现场判定、goal、terminal、current `T=1001` 或 operator acceptance。

## 用户价值与北极星对照

北极星仍是普通用户获得可验证、可靠且异常时可停止的垃圾送达。本轮的用户价值不是“已经发车”，而是把上一轮不可满足的 `lidar=false/reuse-existing-scan` 输入合同推进为可测试的 `sensor-enabled/base-disabled` lifecycle、九门 fail-closed gate 和 single-owner cleanup 合同，并在真实板 Phase 0 证明系统不会抢占另一 live service。

这属于可部署能力增量和安全围栏增量；没有形成普通用户送达、路线动作或 Mission Objective 0。

## 计划与实际 Side-to-Side

| 验收项 | 计划 | 实际证据 | Product 判定 |
|---|---|---|---|
| Robot capability | Upper/O11 sensor-enabled/base-disabled、安全 ownership 与 cleanup | 产品代码、测试和接口 docs 已改；O11 `7`、Upper `128`（skip1）通过 | 接受实现 |
| Algorithm capability | O10 current map/scan/pose/TF/planner/controller/path/obstacle 九门 | O10 `189`、params `4` 通过；offline nine-gate artifact 完整 | 接受离线合同 |
| 集成验证 | combined、Docker、diff 全绿 | combined `328`（skip1）；Docker `6 packages finished`；diff clean | 接受 software proof |
| 注释规范 | 中文技术注释严格 `>20%` | 最终审计 Upper `20.54%`、O11 `20.09%`、O10 `23.82%` | 接受 |
| Phase 0 ownership | 无非 owned runtime/串口冲突才部署 | ttyS5 PID `3765` 属于 `trashbot-esp32-bridge.service`；ttyACM0 PID `4014` 属于 `trashbot-lidar-lifecycle.service` | 正确 BLOCK |
| 部署与 restart | Phase 0 全绿后才执行 | deployment/restart/remote temp validation=`0`；remote 仍旧 SHA | 正确跳过 |
| Phase A | 部署后 exactly once | start/proof/latest/owned-stop=`0/0/0/0`，retry=`0`；v5 unconsumed | 未执行，不接受 readiness |
| Phase B | 九门全绿后 exactly once | pre-stop/execute/post-stop=`0/0/0`，control/motion=`0` | 未执行，不接受 mission |
| Hardware | execute=`1` 后顺序复核 `T=1001`/HIL | execute=`0`，Hardware 未派、artifact count=`0` | 正确跳过 |

## Engineer 验证证据

- `bash -n` 与 Upper/O10 `py_compile`：PASS。
- O11 unittest：`7/7` PASS。
- Upper unittest：`128/128` PASS，`1` 个既有 skip。
- O10 unittest：`189/189` PASS。
- Nav2 params unittest：`4/4` PASS。
- combined：`328/328` PASS，`1` 个既有 skip。
- Docker/Humble：`6 packages finished`，证据边界仅 `software_proof_docker_only`。
- Product 本轮没有重跑这些命令，只读接受 `tech-done.md`、`local_verification.json`、`offline_integrated_verification.json`、Algorithm artifact 与文本日志。

## Phase 0 holder 事实与安全收口

- Upper service active/running，MainPID=`1221`；health/status/nav2 status 均 HTTP `200` 且 parse clean。
- O11 初始 stopped、PID null、PID files=`0`、owned residual=`0`。
- `/dev/ttyS5` holder PID=`3765`，process=`esp32_bridge`，cgroup=`trashbot-esp32-bridge.service`。
- `/dev/ttyACM0` holder PID=`4014`，process=`lidar_driver`，其 lifecycle manager PID=`3934`，cgroup=`trashbot-lidar-lifecycle.service`。
- pre/post 只读 holder 无变化，delta=`0/0`；但已有 holder 均非本 run/O11 owned，因此 single-owner 准入失败。
- 没有 stop、kill、broad kill、deployment、service restart、base stop 或 cleanup mutation。由于本 run 未创建 owned runtime，`cleanup_attempted=false` 是正确结果。

## Evidence ledger

- `current_run_artifact_delta=true`：仅指本轮代码/docs、测试、Docker proof 与真实板 Phase 0 holder ownership evidence。
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `hil_pass=false`
- `delivery_success=false`
- `safe_to_control=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`

## OKR、KR 与历史判断

- O5 约 `85%`，provider/runtime blocker `2/2`，方向=`暂停`。
- O6/O7 各约 `93%`、O1 约 `94%`，以及其他主 Objective 百分比全部 flat。
- O3 只记 readiness capability supporting，不计 Mission attempt/success。
- KR `不归档`；当前推进区不新增完成项，历史区无新增记录。
- 本轮 exact blocker `non_owned_base_and_lidar_serial_holders_present` 记消费 `1/2`。它不是已关闭 transport/deadline blocker，也不得被下轮包装成另一个 preflight、holder summary 或 readiness wrapper。

## Product 核证范围

Product 只读核对 `pre_start.md`、`prd.md`、`tech-plan.md`、`tech-done.md`、全部 JSON/text artifacts、上一 sprint `final.md`、`OKR.md` 与自动化记忆；未运行工程测试、Docker、SSH/live/control，未修改产品代码/tests/tech-done/artifacts，也未触碰并发 `01-54`、`03-50` sprint。

## 下一轮唯一入口

只有 CEO 或当前服务 owner 明确提供独占维护窗口，并确认可安全释放 `trashbot-esp32-bridge.service` 与 `trashbot-lidar-lifecycle.service`、确认没有并发 live task，才可继续同一能力链。之后必须从完整 Phase 0 重新开始：释放后的 holder/owner 核对、临时部署、remote syntax/SHA、service/health、initial stopped/no residual 全绿，才允许唯一 start pipe；v5 仍只在该 pipe 创建时消费。

若独占维护窗口不可得，下一轮切换下一个低进度可行动 Objective；不得再消费 holder preflight/wrapper。

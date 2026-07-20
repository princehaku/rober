# O1 Keyboard-to-Wheel Latency - Final

## 收口结论

- `sprint_type: epic`
- `PRODUCT_CLOSEOUT=ACCEPT_SOFTWARE_HOT_PATH_AND_BOUNDED_SHUTDOWN_PHYSICAL_PENDING`
- proof boundary：`deterministic_segmented_software_hot_path_plus_offline_bounded_shutdown_candidate_v3_not_physical_wheel_latency`
- `live_nonzero_request_count=0`
- `zero_speed_request_count=0`
- `control_invocation_count=0`
- `physical_latency_not_measured=true`
- `mission_objective_0_satisfied=false`
- `safe_to_control=false`
- `hil_pass=false`
- `delivery_success=false`
- O1/O7：`flat`
- KR：`不归档`

本 Epic 接受为键盘控制 software hot-path 实质优化：Vue/Node/Upper/bridge 的 trace 与 local monotonic spans 已实现，Upper rclpy/DDS startup prewarm 将旧 `150ms` 配置等待预算移出 realtime_hold 首帧热路径，bridge HTTP keepalive 不重放失败 command，stop/watchdog 合同保持。它尚未证明真实按键到轮子开始运动的时间，因此物理产品目标继续 pending。

## 实际交付

- Browser 在 keydown 入口生成受限 latency trace；Node 固定 proxy 校验并输出 receive/validate/forward/headers/done 本地分段。
- Upper service startup 预热进程内 rclpy publisher；realtime_hold 不使用 CLI fallback。
- 修复 Product 只读验收发现的 subscriber race：当前无 matched `/cmd_vel` subscriber 时零 publish、`accepted=false`、`latency_pass=false`；subscriber 后续出现时可非阻塞恢复 ready，首帧前无 sleep；短锁不覆盖 burst sleep。
- bridge 记录 callback/build/transport timing，并在锁内复用既有 ESP32 HTTP `/js` 连接；连接失败不 retry 当前 command，不改变默认 transport、vendor command 映射或 stop 顺序。
- keyup、所有方向键释放、pointer end/leave/cancel、window blur、page hidden、stop button 和 watchdog 继续有效；release stop 不等待 pending motion response。
- 产品与 runtime docs 已同步；shared hunk audit 证明既有 Nav2 合同保留。

## 验证与证据边界

Engineer 最终 reconciliation 记录：workstation `535 passed`、Upper `141 passed / 1 skipped`、bridge `32 passed`、
shared `337 passed / 1 skipped`、current/candidate_v3 targeted 各 `17 passed`、冻结 85ba original regression
`119 passed / 1 skipped`；build/lint、py_compile、JSON/jq 与 diff-check 通过。Docker/Humble 保留早期同轮
`6 packages finished` 证据；后续 shutdown repair 为纯 Python/离线 candidate 复验，没有把该 Docker 证据外推为 live。

`software_latency_summary.json` 的 `120` 个 deterministic fake-clock warm samples给出 modeled `9.2ms` p50/p95/max；旧 modeled baseline `159.2ms` 包含源码配置的 `150ms` wait budget。Product 只接受“旧等待已从软件热路径移出”的代码与 deterministic model 结论：`9.2ms` 不是物理延迟，也不是真实 browser、network、Wi-Fi、DDS 或 firmware latency。

本轮没有 SSH、部署、live HTTP control、ROS publish、串口、Nav2、真实 stop 或 nonzero；`live_nonzero_request_count=0`。Product 未重跑工程测试或 live 命令，仅做只读 evidence/diff/hunk 验收。

## OKR、KR 与方向判断

- O1 保持约 `95%`：software hot path 更完整，但 current physical wheel-onset latency、真实 wheel feedback/HIL 与 safe-to-control 仍缺失。
- O7 保持约 `93%`：用户触点 trace 与低延迟软件合同已增强，但没有真实用户动作/物理闭环证据。
- O5 约 `85%` 继续暂停已消费 `2/2` 的 provider/runtime blocker；本轮未重复消费。
- `current_run_artifact_delta=true` 仅表示代码、测试、docs 与 deterministic software artifact；`external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false`。
- Mission Objective 0 未满足；不新增 route、delivery、HIL 或安全 credit。
- 没有满足完成、取消、替换或过期条件的 KR，故当前 KR `不归档`，历史区无新增。

## 已关闭与仍开放

已关闭的软件缺口：

- realtime_hold 首帧承担固定 subscription wait；
- keyboard hot path 的秒级 CLI fallback；
- startup degraded 后无 subscriber 仍可能 publish/accepted 的 race；
- bridge HTTP 每请求重建连接与失败 command 可能被错误重试的合同风险；
- PC/Upper/bridge 缺少分段 local monotonic 可观测性。

仍开放：

- 真实 browser event-loop、PC→Upper 网络/Wi-Fi、DDS scheduling、ESP32 firmware、电机死区与 wheel onset。
- 真实 keydown-to-wheel 和 keyup-to-stop latency baseline/p50/p95/max。
- 外部 observer、当前同窗非零 wheel feedback、HIL、safe-to-control 与长期手控体验。

## 迟到部署链最终结论

- 04-31 在部署前以 version-integrity gate 停止；04-48 生成可复现 latency-only candidate，但第一次部署在任何 target
  move 前被 symlink alias 阻断；两轮均未重启或 sample。
- 05-08 证明 alias-safe replacement 可行，但旧 Upper 在 exact unit restart 时卡 `deactivating/stop-sigterm`；没有新
  health、zero/nonzero/control sample，最终完整 rollback 到旧 hashes 与 ready 状态。
- 05-24 离线修复 shutdown admission、唯一 stop owner、watchdog/release/runtime stop lock 与 rclpy teardown
  fail-closed。source=`52c99...`、candidate_v3=`ceaf8...`、85ba patch=`c2eb...`、incremental patch=`c0a965...`
  与最终 manifest 一致；candidate_v3 是唯一部署输入，04-48 `adadb0...` 与 candidate_v2 均已 superseded。
- Product 接受更强的软件关闭合同，不接受真实 systemd SIGTERM、新版本 health、现场 latency、HIL、safe-to-control、route
  或 delivery。整个链 zero/nonzero/control=`0/0/0`，O1 保持约 `95%`、O7 约 `93%`，Mission Objective 0 未满足，KR
  不归档。

## 下一唯一入口

先取得新的独立部署授权，并冻结 exact unit、当前旧 Upper/bridge/build hashes、静止状态、唯一 owner 与完整 rollback gate；
只部署 candidate_v3。首先只验证正常 SIGTERM、旧进程退出与新版本 health，任何失败 no-retry 并立即 rollback；在这一步
通过前不得加载 PC 或发送 zero/nonzero/control sample。

前序 `ceo_20260721_0154_minimal_wheel_jog_v6` 已消费，永久不得复用。即使部署成功，只有另获完整 physical-latency
authorization，冻结 operator、路线清空、物理限位、direction、`speed<=0.08m/s`、单次 `duration<=300ms`、样本上限与
间隔、pre/post stop、watchdog、紧急停止、abort/no-retry，以及外部高帧率视频/编码器/可信 observer 时钟与 uncertainty，
才可发送非零样本；否则继续保持 `physical_latency_not_measured=true`。

## Sprint 文档状态

`pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md` 已按顺序完整。04-31、04-48、
05-08 与 05-24 均以既有 Micro `tech-done.md` 留档；本 closeout 不创建新 sprint。Product 只更新 OKR/progress 的最小
必要记录；不提交、不 push、不部署。

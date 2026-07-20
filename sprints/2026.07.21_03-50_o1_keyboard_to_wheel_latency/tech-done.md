# O1 Keyboard-to-Wheel Latency - Tech Done

## Sprint metadata

- `sprint_type: epic`
- 状态：`implementation_and_software_verification_complete_physical_pending`
- Owner：`full-stack-software-engineer`
- 证据边界：`deterministic_segmented_software_proof_not_physical_wheel_latency`
- `live_nonzero_request_count=0`
- `zero_speed_request_count=0`
- `control_invocation_count=0`
- `physical_latency_not_measured=true`
- `mission_objective_0_satisfied=false`

## 实际改动

1. Browser/PC：Vue 在 keydown handler 入口记录 browser monotonic，给 keyboard pulse 附加可选
   `trashbot.keyboard_wheel_latency_trace.v1`；PC Node 对 schema、token 长度/字符、有限数、sequence 和 sample kind
   做白名单校验，未知字段丢弃，返回 Node 本进程 receive/validate/forward/headers/done 点位和 local spans。
2. Upper：service 监听前预热并复用 rclpy node/publisher/DDS graph；`realtime_hold` hot path 首帧在任何 sleep 前
   publish，预热不可用时 `accepted=false` fail-closed，不再启动秒级 CLI fallback，订阅未证明显式 degraded。
   每次 hold 在 publish 前仅执行零等待 `spin_once(0.0)` 刷新 graph；当前没有 matched subscriber 时
   `frames_published=0`/`accepted=false`，bridge 后启动或重启并重新 matched 后可立即恢复 ready。普通非键盘兼容接口
   仍保留既有 fallback 行为。rclpy spin/publish 用短临界区锁串行化，锁不覆盖 burst sleep。
3. Bridge：`_cmd_vel_callback` 记录 callback/build/transport begin/end monotonic 点位与 local spans；HTTP `/js`
   在 bridge 单 owner 锁内复用连接。连接失败不重发当前 command，只关闭连接供后续独立请求重建；默认 transport、
   `/js` path、T=1/T=11/T=13、速度/PWM 映射和 stop 顺序均未改。
4. Safety：keyup/all release、pointer end/leave/cancel、blur、page hidden、stop button、watchdog 入口保留；keyboard
   release stop 可独立于 pending motion response 发出，不等待证据聚合。
5. Docs/artifact：同步产品与 ROS runtime 合同，新增共享 hunk baseline/final audit 和 software latency summary。

## 文件与接口影响

- PC：`RobotControlConsolePanel.vue`、`workstationApi.ts`（接口签名保持兼容，无代码改动）、`server/index.ts`、
  `server/robotControlLatency.ts`、`shared/contracts.ts`、`catalog.test.ts`、`robotControlLatency.test.ts`。
- Upper/bridge：`upper_robot_api.py`、`test_upper_robot_api.py`、`esp32_bridge_node.py`、
  `test_waveshare_json_bridge.py`。
- Docs：`docs/product/pc_free_roam_mapping_design.md`、`docs/interfaces/ros_runtime_contracts.md`。
- Request 只新增可选 `latency_trace`; response 只新增可选 `pc_latency_timing`/`upper_latency_timing`，旧请求兼容。

## Software benchmark

- Artifact：`artifacts/full-stack/software_latency_summary.json`。
- `120` 个 deterministic warm fake-clock samples；结果是分段 software model，不是 browser/网络/DDS/firmware/轮子实测。
- modeled `keydown_to_fake_transport_write_ms`: p50/p95/max=`9.2/9.2/9.2ms`。
- baseline `159.2ms` 是旧源码中 realtime_hold `150ms` discovery wait budget 加同一 deterministic segment fixture，
  不是物理 baseline；modeled p95 improvement=`94.22%`。
- stop regression model p95=`0ms`，并由现有 keyup/blur/page hidden/stop/watchdog 回归覆盖。
- 所有跨进程/跨机 raw monotonic 直接相减均为 false；本轮未做 clock calibration，因为只验收 local spans。

## 验证结果

- `npm test -- robotControlLatency.test.ts`：`3 passed`。
- `npm test -- catalog.test.ts -t "keyboard|manual|stop|watchdog|latency"`：`22 passed / 237 skipped`。
- `npm test`：`5 files passed; 535 tests passed`。
- `npm run build`：通过；Vite 仅保留既有 `>500kB` chunk warning。
- `npm run lint`：通过。
- Python `py_compile`：Upper/bridge 通过。
- `python3 -m unittest onboard/tests/test_upper_robot_api.py`：05-24 bounded-shutdown reconciliation 后最终
  `141 passed / 1 skipped`。
- bridge suite：最终 Hardware 离线复验补齐 stop 顺序断言后 `32 passed`。
- Upper + Nav2 shared regression：05-24 reconciliation 后最终 `337 passed / 1 skipped`。
- bounded shutdown / realtime_hold / watchdog / runner-cleanup targeted：current 与 candidate_v3 均 `17 passed`；冻结
  85ba original regression 为 `119 passed / 1 skipped`。
- Docker/Humble：镜像 build 通过，`Summary: 6 packages finished [49.3s]`；证据仅为 `software_proof_docker_only`。
- JSON/jq threshold：通过，输出 `true`。
- scoped `git diff --check`：通过。

## 失败定位与修复

1. 首轮 workstation build 因新增测试数组严格索引报 `Object is possibly 'undefined'`；改为显式 non-null fixture 索引，
   重跑 build 通过。
2. 首轮 bridge failure-path 测试的 fake logger 缺 `error()`；补齐 fake logger 错误收集后 bridge 全量通过。
3. 首轮 Upper 全量曾命中并发 Nav2 sprint 中 `--path-goal-frame-id` 断言缺失；未跨范围修改。Nav2 owner 随后完成
   其共享 hunk，最终 combined suite `326 passed / 1 skipped`。
4. 首轮 workstation 全量的源码字符串断言仍期待旧 `sendStop({ refreshAfter: false })`；同步为高优先级 stop 新合同后，
   最终全量 `535 passed`。
5. 全量 UI tests 会改写两个历史 DOM smoke 的 `checked_at`；已用 additive patch 恢复原时间，未把测试噪声带入本 sprint。
6. 只读验收发现 startup `degraded_subscription_unproven` 后旧实现仍会先 publish，并按 `frames_published>0`
   返回 accepted；这在 bridge 晚启动/重启时可能丢首帧。现改为 keyboard hold 发布前执行一次非阻塞 graph refresh，
   无 matched subscriber 时返回 `cmd_vel_subscription_unavailable_fail_closed` 且零 publish；subscriber 后续 matched
   时自动恢复 ready。新增测试同时锁定 `publish_count=0/accepted=false/CLI=false` 和恢复后首帧前无 sleep。
7. 最终 Hardware 离线审计发现 bridge 与 bridge test 的本轮新增 `#` 中文技术注释比例分别仅约 `5.33%`、
   `1.75%`，未达到项目 `>20%` 规范；仅补充协议边界、连接生命周期、时钟边界与无硬件测试原因注释，并新增
   `_send_stop` 精确顺序回归。复验新增非空行口径分别为 `21.98%`、`23.40%`，非中文 `#` 技术注释均为 `0`。

## 中文注释与共享 hunk

- 新增独立 latency helper：按“非空新增行”口径，补齐字段级时钟/安全说明后中文技术注释超过 `20%`。
- 新增 deterministic latency test：按同一口径中文技术注释超过 `20%`。
- 共享大文件包含并发 Nav2 hunks，不用整文件 diff 冒充本 owner 注释率；本轮每个 latency function/block 均有中文
  原因注释，覆盖时钟边界、首帧优先、stop 优先、fail-closed、连接不重放和 proof boundary。
- bridge late-writer 新增行独立审计：`esp32_bridge_node.py` 为 `20/91=21.98%`，bridge test 为
  `22/94=23.40%`；全部 `#` 技术注释均含中文。
- 开工/收工 hashes 与 hunk audit 在 `artifacts/full-stack/shared_hunk_baseline.md`；未使用 checkout/reset/stash/rebase，
  未覆盖或回滚既有 Nav2 hunks。

## Hardware 最终离线复验

- 已读 vendor：`docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、
  `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`。
- vendor 命令合同未改写：`T=1/L/R`、`T=11/L/R`、`T=13/X/Z` 常量与映射文件无本轮 diff；停车仍严格按
  `T=11 -> T=1 -> T=13` 三种控制面依次归零。
- HTTP `/js` 两个独立请求只建立一个同源连接；连接失败当前 command 的 request 次数精确为 `1`，坏连接清空后
  只允许未来独立请求重建。bridge timing 四段 local span 均有非负断言，且明确禁止跨进程原始 monotonic 相减。
- watchdog targeted 离线回归：`test_manual_control_realtime_hold_defers_stop_to_watchdog` 与
  `test_manual_control_realtime_hold_prewarm_failure_is_rejected` 共 `2 passed`；未改变 release/watchdog 合同。
- 最终命令：bridge `py_compile` exit `0`；bridge suite `Ran 32 tests ... OK`；上述 watchdog targeted
  `Ran 2 tests ... OK`；三文件 scoped `git diff --check` exit `0`。
- 本节复验没有 SSH、curl、部署、服务重启、ROS publish、串口、HIL 或控制；04-48 deployment attempt 保持
  `retry_count=0`、target replacement=`0`、service restart=`0`、zero/nonzero sample=`0`，当前授权未被重试。

## 用户旅程收益

正常 warm path 不再让第一次键盘请求承担 rclpy import/node/publisher 创建和固定 150ms subscription wait；bridge
HTTP 后续 pulse/stop 可复用连接。用户松键、失焦、切页或 watchdog 到期仍走原停车合同，连接失败不会重放 nonzero。
响应中的分段 local spans 可以定位 PC、Upper 或 bridge 瓶颈，而不会把 HTTP 200 误说成轮子已动。

## 剩余风险与机器人配合

- `physical_latency_not_measured=true`：Wi-Fi、真实 DDS scheduling、ESP32 firmware loop、电机死区和轮子 onset 尚未测。
- Docker 未因 subscriber race 修复重跑：本轮只改 Upper Python graph gate 与纯 fake 测试；此前同一实现轮次的
  Docker/Humble `6 packages` build 证据保留，当前 Python full/shared suite 已覆盖新增逻辑。
- 当前无 fresh bounded authorization；`live_nonzero_request_count=0`，没有 SSH、部署、live HTTP control、ROS publish、
  串口、Nav2 或真实 stop/nonzero 命令。
- 物理验收需新的明确授权、外部高帧率视频/编码器/可信 observer、预/后 stop 和样本上限；不能复用已消费的 v6。
- software proof 不改变 `safe_to_control=false`、`hil_pass=false`、`delivery_success=false`，也不提升 route/delivery 结论。

## 2026-07-21 迟到 writer 最终离线复验

- Full-Stack 在禁止 SSH/live/control 的围栏内复跑 workstation，并发现 trace 虽有 schema/token 白名单，但 PC Node
  尚未确认 trace 的 `hold_session_id/hold_sequence` 与实际 `realtime_hold` watchdog identity 一致；这会让一个字段合法
  但身份过期的 trace 错配到当前按键请求。现已在固定 manual proxy 内 fail-closed：错配返回 HTTP `400`、
  `failure_reason=latency_trace_hold_identity_mismatch`，且不转发 Upper。
- 实际追加修改：`pc-tools/workstation/src/server/index.ts`、`pc-tools/workstation/test/catalog.test.ts`、
  `docs/product/pc_free_roam_mapping_design.md` 与本文件；未触碰 Upper、bridge、SSH、服务、ROS、串口或任何控制。
- 修复后 `npm test -- robotControlLatency.test.ts catalog.test.ts` 为 `2 files / 262 passed`；`npm test` 为
  `5 files / 535 passed`；`npm run build` 与 `npm run lint` 通过，build 只保留既有 `>500kB` chunk warning；scoped
  `git diff --check` 通过。全量测试改写的两个历史 DOM smoke 时间戳已用精确 additive patch 恢复，没有带入范围外噪声。
- 新增独立 latency helper/test 继续按非空行统计分别为中文注释 `22/103=21.36%`、`16/78=20.51%`，均严格
  `>20%`。scoped assertion 继续命中 `live_nonzero_request_count=0` 与 `physical_latency_not_measured=true`。
- 用户收益：普通用户的首帧 trace 现在不会被另一 hold session/sequence 污染，失败会给出稳定原因；旧无 trace 请求、
  正常一致 identity、release stop/watchdog 和 response 可选字段均保持兼容。该 scope 同意进入主责统一精确提交。

## Product latency 链最终 reconciliation

- 04-31 只读 preflight 因本地已验证 Upper 混有未部署 c8 跨文件合同而在部署前停止，部署、重启、zero sample 与
  control 均为 `0`。
- 04-48 产出可复现的 85ba latency-only candidate；第一次部署在任何 target move 前因 bridge source/build symlink
  alias 失败，target replacement、restart、zero/nonzero/control 均为 `0`。
- 05-08 alias-safe canonical replacement 成功，但旧 Upper 卡在 `deactivating/stop-sigterm`；post-deploy health 未形成，
  因而 zero/nonzero/control 仍为 `0`，随后按 no-retry 合同完整 rollback 到旧 hashes 与 ready 状态。
- 05-24 仅离线修复 shutdown admission、唯一 stop owner、watchdog/release/runtime stop lock 与 rclpy teardown
  fail-closed；最终唯一部署输入是 candidate_v3，而不是 04-48 candidate 或 candidate_v2。machine-readable manifest 固定
  source/candidate/base-patch/incremental-patch SHA 为 `52c99...` / `ceaf8...` / `c2eb...` / `c0a965...`，并证明
  AST 白名单、7 个 c8 sentinel、可复现生成及两级 patch apply/reverse/reapply/hash gate 全部通过。
- Product 只接受 `offline_bounded_shutdown_candidate_v3_software_proof_only`。整个迟到链没有 zero/nonzero/manual/stop
  control sample，`physical_latency_not_measured=true`、Mission Objective 0 未满足、O1/O7 flat、KR 不归档。

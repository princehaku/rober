# O1 Latency-Only Candidate Deploy - Tech Done

## Sprint metadata

- `sprint_type: micro`
- Owner：`full-stack-software-engineer`
- 状态：`latency_only_candidate_verified_deployment_stopped_before_replacement`
- 证据边界：`verified_latency_only_software_candidate_and_remote_staging_not_live_sample`
- `live_nonzero_request_count=0`
- `zero_speed_request_count=0`
- `physical_latency_not_measured=true`
- `hil_pass=false`
- `safe_to_control=false`

## 实际改动

本轮没有修改当前 worktree 的产品源码、测试、OKR、progress、vendor、Nav2 或其他 sprint；没有 commit、push、reset、
checkout 或 stash。新增本 sprint 的生成器、候选、patch 与 machine-readable manifests：

- `artifacts/candidate/generate_latency_only_upper.py`
- `artifacts/candidate/upper_robot_api.py`
- `artifacts/candidate/upper_robot_api_85ba_latency_only.patch`
- `artifacts/candidate/candidate_manifest.json`
- `artifacts/verification_manifest.json`
- `artifacts/deployment_attempt.json`

远端只创建了 `/root/rober/onboard/runtime/latency_only_deploy_20260721_0448/` 下的 rollback backup 与 stage 文件。
原子替换失败后精确清理了目标目录旁的 `*.latency_new` / `*.rollback_new` 临时名；没有替换产品目标，也没有重启服务。

## Candidate 构造与审计

生成器只以 commit `85ba730...` 的 Upper SHA `8c0f...` 为基线，从当前组合实现中移植 9 个 latency 白名单符号：

- `UpperRobotApi.manual_control`
- `_ensure_ros_cmd_vel_context`
- `create_app`
- `manual_motion_ros_cmd_vel_hold_refresh_transaction`
- `normalize_latency_trace`
- `prewarm_ros_cmd_vel_context`
- `publish_ros_cmd_vel_inprocess_burst`
- `run_server`
- `upper_latency_timing`

另只增加 `threading` import、`_ROS_CMD_VEL_LOCK`、trace schema/token pattern。AST 实际变化集合与允许集合精确相等。
`sensor_owned_scan`、canonical initialpose、existing LiDAR lifecycle reuse、Nav2 map override、owned holder/publisher 等
c8 专属哨兵均为 `0`。85ba 已有的通用 UART/LiDAR count 字段没有被误判成 c8 新增哨兵。

候选 SHA 为 `adadb0...`，patch SHA 为 `930ffa...`。在隔离 85ba worktree 上：dry-run、apply、候选 hash、
reverse dry-run、rollback base hash、reapply hash 全部通过。恢复到精确 85ba 后第二次生成，candidate 与 patch 均逐字节一致。

## 验证结果

- Candidate `py_compile`：PASS；candidate scoped diff-check：PASS。
- 当前 latency tests 通过路径重定向加载 candidate，8/8 PASS：hostile trace、first-frame-before-sleep、prewarm、
  subscriber zero-publish fail-closed、late recovery、no CLI fallback、watchdog deferred stop、prewarm failure rejection。
- 85ba 原始 `test_upper_robot_api.py` 全量：119/119 PASS，1 个既有 skip。这个全集包含 85ba 的全部非 Nav2 回归，
  因此非 Nav2 subset 也全部通过；没有加载依赖 c8 的当前 Nav2 新测试。
- Bridge 正确仓库根目录：`py_compile` PASS，31/31 PASS。首次组合命令曾因 cwd 在 workstation 导致相对路径失败；
  已明确判为无效证据并从仓库根重跑通过。
- Workstation：latency 3/3 PASS，full build PASS；仅保留既有 Vite large-chunk warning。
- Remote stage：Upper/bridge 临时文件 `py_compile`、hash 与 Upper c8 sentinel gate 均 PASS。

## 部署阶段与失败定位

部署前 remote 仍严格匹配 Upper 85ba 与 bridge HEAD 基线；Nav2 false/stopped，最新 T1001 `L/R=0`，最后 motion
command `T=11,L/R=0`，ROS `/cmd_vel` 为 1 publisher/1 subscriber，`/dev/ttyS5` 仅 PID 3765 持有。

rollback backup 与 stage 全部建立并校验后，原子替换脚本试图让 bridge source 与 build runtime 新文件保持同一 hardlink。
现场实际结构是：

`onboard/build/ros2_trashbot_hardware/ros2_trashbot_hardware -> onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware`

因此 build 临时路径与 source 临时路径其实是同一个路径；清理 build 侧临时名同时删除了 source 临时名，随后 `ln` 报
`No such file or directory`。错误发生在任何目标 `mv` 和 service restart 之前。rollback 临时构造遇到同一 alias，
但原目标从未替换，因此无需恢复目标内容。按“任一异常立即停止、不得重试”没有改用单路径替换继续部署。

只读收口证明：Upper/bridge 目标 SHA 仍为 `8c0f...` / `6e82...`，服务 PID 仍为 Upper 1221、bridge wrapper
1218/node 3765 且 active；Nav2 false/stopped、T1001 L/R=0、最后 T11 L/R=0、1 pub/1 sub、唯一串口 owner 均不变。

## 零速 sample 与用户旅程

目标文件替换与服务重启未完成，所以没有重启 PC API，也没有发送唯一零速 sample、stop 或 sample readback。
PC/Upper/bridge local spans 与 network RTT envelope 均为 `null`；没有跨机 monotonic 相减。

用户旅程尚未获得现场延迟改善，但候选构造 blocker 已被消除：现在有一个可重复、可逆、无 c8 Nav2 污染且测试通过的
latency-only Upper artifact。部署 blocker 已进一步定位为远端 symlink layout 的原子替换策略，而不是候选内容或服务 ownership。

## 剩余风险

- Candidate 尚未成为远端运行版本；bridge keep-alive/timing 与 workstation latency build 也未加载到现场进程。
- 下一轮必须从当前旧 hashes 和完整静止 gate 重新开始，并把 bridge source/build 视为同一 symlink 目标，只做一次源路径
  原子替换；仍需新的独立授权才能开始新的部署尝试。
- 未发送 zero/nonzero；`live_nonzero_request_count=0`。未观察物理 wheel onset，未测 physical latency，不能宣称 HIL、
  safe-to-control、robot-control-executed 或 delivery success。

## Release integration 离线复验

`2026-07-21T05:01:56+08:00` 由 Robot Platform release integration owner 在禁止 SSH、部署、服务重启、HTTP control、
ROS publish、串口和现场 retry 的边界内完成复验。当前 Upper 全量为 `132 passed / 1 skipped`，candidate latency targeted
为 `8/8 passed`；workstation latency 为 `3/3 passed`，keyboard/manual/stop/watchdog/latency targeted 为
`22 passed / 237 skipped`；candidate/patch 从冻结 85ba 再生成后逐字节一致，patch dry-run/apply/reverse/rollback/reapply 全部通过。
Hardware late-writer 的当前 bridge suite 另复验为 `32/32 passed`，并锁定 keep-alive no-replay、timing spans 与
`T=11 -> T=1 -> T=13` stop 顺序；原部署当时的 `31/31` 记录保留为历史执行证据。
复验发现 candidate manifest 记录了生成机 `/Users/...` 与 `/tmp/...` 绝对路径，并残留一个忽略的 `.pyc`；现已把 manifest
改为位置无关的 commit/repo 引用并清理临时 bytecode。该 hygiene 修复不改变 candidate SHA `adadb0...` 或 patch SHA
`930ffa...`，也不改变 `target_file_replacement_count=0`、`service_restart_count=0`、`zero_speed_request_count=0`、
`live_nonzero_request_count=0` 和 `physical_latency_not_measured=true` 的部署/物理证据边界。

## Product 边界补记

Product 接受本轮可复现 latency-only candidate 与 first-target-move 前的诚实 fail-closed，但不接受部署、重启、zero sample、
physical latency 或 OKR credit。该 candidate `adadb0...` 已被 05-24 candidate_v3 `ceaf8...` supersede，后续不得作为部署
输入；本历史事实保持 `target replacement/restart/zero/nonzero/control=0/0/0/0/0`。

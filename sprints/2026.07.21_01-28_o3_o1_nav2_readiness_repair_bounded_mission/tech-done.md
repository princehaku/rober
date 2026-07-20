# Tech Done

- sprint_type: `epic`
- owner: `robot-software-engineer`（Robot 集成、离线验收、Phase 0 与 live orchestration）
- status: `IMPLEMENTED_AND_OFFLINE_GREEN_PHASE0_BLOCKED_AUTHORIZATION_UNCONSUMED`
- generated_at: `2026-07-21T04:11:57+08:00`
- authorization: `ceo_20260721_0128_operator_watch_route_clear_physical_limit_v5`
- run_id: `run_o3_o1_bounded_mission_20260721_0128_01`
- action_id: `action_o3_o1_bounded_mission_20260721_0128_01`
- task_id: `task_o3_28_pose_fixed_route_consumer_20260713_0402`
- route_intent_id: `route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`

## 实际改动

### Robot Software

- `onboard/scripts/upper_robot_api.py`
  - `/api/nav2/start` 保留 exact-field 校验，并只接受 legacy existing-scan 与本轮
    `base=false/lidar=true/reuse_existing_scan=false` sensor-owned 两种安全组合；其他组合在 subprocess 前
    fail closed。
  - start argv 固定 canonical map 和 effective sensor flags；sensor-owned semantic success 同时核对 base UART
    zero-new-open、owned LiDAR holder、current owned `/scan` publisher、O11-owned manager、no-motion 与 no-broad-kill。
  - semantic failure 只清理本请求实际创建的 O11 process group；pre-existing owner conflict 不调用 stop。
  - proof refresh 要求显式复用 O11-owned LiDAR lifecycle 与 canonical free-cell initialpose，并把 canonical map、
    两个 opt-in 和 fixed goal `map/(0.8,0.25,0.0)` 传给 O10；请求省略 goal 时也使用并回显该固定值。
- `onboard/scripts/o11_nav2_lifecycle.sh`
  - 增加 existing-scan/sensor-owned 模式、base/LiDAR holder 前后差分、`/scan` publisher 前后计数和 ownership、
    owner process group、canonical YAML/image SHA、physical-motion 与 broad-kill 字段。
  - sensor-owned 模式拒绝已有 `/scan` publisher、LiDAR holder 或 O11 manager；只有 owned holder/publisher 与
    base zero-open 都成立才进入 `running`。
  - stop 仅消费 PID 文件归属的 process group，不使用 `pkill/killall`，不打开 UART，不发送底盘 stop。
- `onboard/tests/test_upper_robot_api.py`、`onboard/tests/test_o11_nav2_lifecycle_script.py`
  - 覆盖两种合法 start、非法组合、semantic cleanup、pre-existing owner 保留、base UART sticky zero-open、
    LiDAR ownership、canonical map/initialpose 以及 fixed-goal default/argv。
- `docs/interfaces/ros_runtime_contracts.md`
  - 同步 sensor-owned lifecycle、proof ownership、canonical map 与固定终点、cleanup/no-motion 证据边界。

Robot production contract slice 的新增技术注释均为中文，离线自检时 Upper/O11 新增注释占比均高于 20%。

### Algorithm 集成审计

Robot 对 Algorithm owner 的五文件结果做只读审计，没有修改其范围。集成结果包括：

- O10 natural-final 以 same-current 九门严格判定 `READINESS_GO`，固定 goal 为
  `frame_id=map,x=0.8,y=0.25,yaw=0.0`；
- canonical map/current scan/current pose/persisted pose/dynamic TF/planner/controller/path/obstacle-clear 均有
  fail-closed gate；
- Nav2 params 保持 collision detection，并固定 `observation_persistence=0`、`expected_update_rate=10`；
- Algorithm diff check clean，测试最终 `189/189` 与 params `4/4` 通过。

## 验证结果

最终有效验收全部为绿：

| 验收项 | 结果 |
|---|---|
| `bash -n onboard/scripts/o11_nav2_lifecycle.sh` | PASS |
| Upper/O10 `py_compile` | PASS |
| O11 unittest | `7/7` PASS |
| Upper unittest | `128/128` PASS，`1` 个既有 skip |
| O10 unittest | `189/189` PASS |
| Nav2 params unittest | `4/4` PASS |
| 四套 combined | `328/328` PASS，`1` 个既有 skip |
| `bash onboard/scripts/docker_humble_build.sh` | PASS，`6 packages finished [46.3s]` |
| scoped `git diff --check` | PASS |

首轮验收曾发现 Upper argv 断言夹具没有开启 path generation，以及 Algorithm 静态护栏在并发落盘窗口短暂
命中新旧契约不一致；前者由 Robot 修正夹具，后者由 Algorithm owner 修复。上述两项均在最终分套和 combined
验收中复跑为绿，未把首轮失败当成交付结果。

离线证据见 `artifacts/robot-software/local_verification.json`。Docker 结果仍仅是
`software_proof_docker_only`，不等于 HIL、真实路线、safe-to-control 或 delivery success。

## Phase 0 结果

离线门全绿后，Robot 对 `root@192.168.1.11:37878` 执行只读 Phase 0。结果：

- `trashbot-upper-robot-api.service` 为 `active/running`，MainPID=`1221`；
- `/api/health`、`/api/status`、`/api/nav2/status` 均 HTTP `200` 且 JSON 可解析；health=`ready`；
- O11 为 `running=false/state=stopped/pid=null`，O11 PID files=`0`、owned residual=`0`；
- `/dev/ttyS5` 已被非本轮 PID `3765` 持有，进程为 `esp32_bridge`，归属
  `trashbot-esp32-bridge.service`；
- `/dev/ttyACM0` 已被非本轮 PID `4014` 持有，进程为 `lidar_driver`，归属独立
  `trashbot-lidar-lifecycle.service`（manager PID `3934`）；
- pre/post 只读复核 holder 均未变化，base/LiDAR holder delta 都为 `0`，但 pre-existing holder 本身违反本轮
  exclusive O11 ownership 准入。

因此 Phase 0 按 `non_owned_base_and_lidar_serial_holders_present` fail closed。Robot 没有停止、kill、重启或抢占
这些并发服务，也没有上传临时文件、原子替换、远端 py_compile/bash syntax、restart Upper。四个 remote SHA
仍是旧版本，与本地已验证 SHA 不同。完整事实见：

- `artifacts/robot-software/phase0_deployment_manifest.json`
- `artifacts/robot-software/phase0/preflight_summary.raw.txt`
- `artifacts/robot-software/phase0/holder_ownership.raw.txt`
- `artifacts/robot-software/phase0/local_remote_sha256.raw.txt`

## exactly-once 计数与安全边界

- v5 authorization consumed=`false`；
- Phase A start/proof/latest/owned-stop=`0/0/0/0`，retry=`0`；
- `/initialpose` publish=`0`；
- Phase B pre-stop/execute/post-stop=`0/0/0`，goal retry=`0`；
- motion/control endpoint invocation=`0`；
- deployment/restart/cleanup mutation=`0`；
- `robot_control_executed=false`、`safe_to_control=false`、`hil_pass=false`、`delivery_success=false`。

计数和 cleanup 边界分别见 `artifacts/robot-software/attempt_counts.json` 与
`artifacts/robot-software/cleanup.json`。由于 Phase 0 未通过，未创建 frozen request、未发 start pipe，因而没有
Phase A/B raw、readiness decision 或 Hardware HIL review 输入。

## 失败定位

本轮代码、测试与 Docker 没有剩余失败。live 链路唯一 blocker 是 Phase 0 已存在两个非 O11-owned 串口
holder。若继续部署或 start，将与当前 `esp32_bridge`/独立 LiDAR lifecycle 争用设备，违反本轮 single-owner 与
no-interference 条件，因此安全收口在授权消费之前。

## 剩余风险与下一步

- 本地实现尚未部署到板端，remote Upper/O11/O10/Nav2 params 仍是旧 SHA。
- 不应由本 sprint 擅自停止现有 systemd 服务；需要 CEO/当前服务 owner 明确安排独占维护窗口，先安全释放
  `trashbot-esp32-bridge.service` 与 `trashbot-lidar-lifecycle.service`，并确认不是另一 live task。
- 维护窗口形成后，应从部署临时文件、remote syntax/SHA、service/health、初始 stopped/no residual 的完整
  Phase 0 重新开始；v5 只有在唯一 `/api/nav2/start` stdin pipe 创建时才消费。
- 在 Phase A 九门 natural-final 全绿与 Phase B current admission 成立前，不得发送 bounded goal；没有同 run
  terminal、current `T=1001`、post-stop 和 operator evidence 前，不得宣称 route/HIL/delivery/safe 成功。

本 Epic 现为实现完成但 live gate blocked，等待 Product 依据真实证据决定是否保留 v5 到独占维护窗口；本文件不
更新 OKR 百分比、不归档 KR，也不预写 `side2side_check.md/final.md`。

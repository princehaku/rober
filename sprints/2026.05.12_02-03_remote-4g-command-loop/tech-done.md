# Sprint 2026.05.12_02-03 Remote 4G Command Loop - Tech Done

## 状态

- 阶段：Task B tech-done
- 时间：2026-05-12 01:12 Asia/Shanghai
- Owner：robot-software-engineer
- 范围：robot `remote_bridge` outbound polling 和 command -> behavior-level adapter -> ack/status loop

## Task B 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - `RemoteBridgeWorker` 支持从配置传入 `last_ack_id`，polling 时带给 cloud `/commands/next`。
  - 保留 cached command ack，duplicate command id 复用原 ack，不重复提交 behavior action/service。
  - malformed command 且可识别 `id` 时回传 `failed` ack，message 明确为 malformed command。
  - expired command 回传 `ignored` ack，不提交 behavior adapter。
  - busy collect 通过 behavior adapter 的 409/busy 结果回传 `ignored` ack，不标记 failed。
  - accepted command 仍只走 behavior-level adapter：`collect` -> `TrashCollection` action，`confirm_dropoff` -> `/trashbot/confirm_dropoff` service，`cancel` -> action cancel；不接受 remote `/cmd_vel`，不把 cloud payload 映射为底盘速度。
  - terminal ack 成功后 best-effort post 最新 status；post-status 失败不取消、不停止已经接受的本地任务。
  - ROS node 参数补齐 `bearer_token` 和 `last_ack_id`；`bearer_token` 优先，兼容旧 `auth_token`。
- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 增加 repo-local import bootstrap，让指定 unittest 命令可在未安装包时直接运行。
  - 增加 targeted coverage：malformed payload、expired command、duplicate command、busy collect ignored、`last_ack_id` query、bearer auth header、配置参数静态检查。

## 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py
Ran 16 tests
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
exit 0
```

```text
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge.py sprints/2026.05.12_02-03_remote-4g-command-loop/tech-done.md
exit 0
```

## 失败定位

- 首轮 unittest 失败原因：本机未安装 `ros2_trashbot_behavior` package，指定命令直接运行测试文件时缺少 repo-local `sys.path`。已在 `test_remote_bridge.py` 内补最小 import bootstrap 后复跑通过。

## 剩余风险

- 本轮是 software-only/mock cloud 级验证，不包含真实云部署、真实 4G/SIM、弱网长时运行、ROS2 Humble 容器 colcon build、真实 action server、真实 Nav2/fixed-route 或 WAVE ROVER/HIL。
- malformed command 如果完全不是 object 且没有可用 command id，当前无法按命令 id 回传 ack，只能让 polling 错误进入 bridge offline/status 路径；这是 remote contract 层需要 cloud 端避免的输入边界。
- Task A 的 mock cloud/operator 入口并行改动尚未在本 Task B 范围内做集成 smoke；需要主会话或 Task C 统一跑 A+B 集成验收。

## Task C 集成 smoke

- 阶段：Task C engineering integration smoke
- 时间：2026-05-12 01:17 Asia/Shanghai
- Owner：robot-software-engineer
- 范围：Task A mock cloud/operator endpoint 与 Task B `RemoteBridgeWorker`/`RemoteCloudClient` 的 software-only command -> polling -> behavior adapter -> ack/status -> phone readback 闭环。

## Task C 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - 修复 `MockCloudStore.next_command(last_ack_id=...)` 的 cursor 语义：不再用 command id 字符串大小过滤，而是按 `commands` 队列顺序定位 last ack 位置，再从后续队列中返回第一个未 ack 且未过期 command。
  - 保留 `acks` 作为终态命令状态来源，避免已 ack command 被再次发给 robot polling。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
  - 新增非字典序 command id 围栏：`cmd-9` ack 后，`last_ack_id=cmd-9` 必须返回队列后续的 `cmd-10`，证明 polling 不依赖字符串排序。
- `sprints/2026.05.12_02-03_remote-4g-command-loop/tech-done.md`
  - 记录 Task C 集成修复、验证结果和剩余风险。

## Task C 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_remote_bridge.py
Ran 48 tests in 19.868s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
exit 0
```

```text
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_remote_bridge.py docs/product/remote_4g_mvp.md sprints/2026.05.12_02-03_remote-4g-command-loop/tech-done.md
exit 0
```

## Task C 失败定位

- 集成根因：mock cloud 的 `/commands/next?last_ack_id=...` 曾用 `command["id"] > last_ack_id` 过滤 command。该语义把 command id 当作有序字符串，导致 `cmd-9` ack 后队列里的 `cmd-10` 因字典序更小而被跳过。
- 修复定位：cloud endpoint 应以提交队列顺序和 ack 终态判断 next command；command id 只作为身份标识和 cursor 命中值，不作为全局排序键。

## Task C 剩余风险

- 本轮只证明本地 mock cloud / outbound polling / behavior adapter contract 的 software-only 闭环，不包含真实云部署、真实 4G/SIM、弱网重试、生产鉴权、OSS/CDN 图片链路、真实 ROS2 action server、Nav2/fixed-route、WAVE ROVER 或 HIL。
- `last_ack_id` 如果指向 mock cloud 队列中不存在的 command，当前降级为从队列头开始寻找未 ack command；真实云持久化队列后仍需定义跨重启 cursor 保留策略。
- command ack/status 证明的是 remote control-plane 已接收并提交行为层请求，不等于真实垃圾送达完成。

## Product acceptance 摘要

- 阶段：product acceptance
- 时间：2026-05-12 01:20 Asia/Shanghai
- Owner：product-okr-owner

产品侧接受 Task A/B/C 作为 O6 的 local mock cloud / remote bridge command loop 软件证据。验收理由是 mock cloud command/status/ack、robot outbound polling、duplicate/expired/malformed/busy 围栏和 A+B integration smoke 均已通过 targeted validation，且 `last_ack_id` 字符串比较问题已被定位并修复为队列顺序 + ack 状态。

OKR 口径只允许把 O6 从约 5% 保守提升到约 12%。O5 仅记录 phone-safe 支持触点，不做大幅提升。本轮证据边界固定为 `software_proof_docker_only` / local mock cloud；不声明真实云部署、真实 4G/SIM、生产鉴权、OSS/CDN、真实 ROS2/Nav2、WAVE ROVER 或 HIL。

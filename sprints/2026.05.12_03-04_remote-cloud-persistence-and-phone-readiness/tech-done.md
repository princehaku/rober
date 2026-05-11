# Sprint 2026.05.12_03-04 Remote Cloud Persistence And Phone Readiness - Tech Done

## 状态

- 阶段：tech-done
- 时间：2026-05-12 01:52 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化
- 支撑 Objective：O5 手机用户体验与量产边界
- 验收边界：`software_proof_docker_only`；不声明真实云、真实 4G、生产鉴权、OSS/CDN、真实硬件、Nav2/fixed-route 实跑或 WAVE ROVER `hil_pass`

## 用户价值和产品北极星

本轮把 remote 4G mock control-plane 从“内存闭环 demo”推进到“生产前可靠性语义”：普通手机用户未来能看到远程链路是否 ready、上一条命令是否被 robot bridge ACK、状态是否可恢复，而不是只能依赖一次性进程内状态。

北极星保持不变：手机是普通用户唯一入口，4G 场景通过云端中转命令/status/ACK；本轮只完成 local mock 持久化和 phone-readable readiness 的软件证据，不把 operator/debug 入口包装成正式手机 UI。

## OKR 映射和 KR 完成情况

| KR | Owner | 结果 | 证据边界 |
| --- | --- | --- | --- |
| KR6-1 mock cloud command queue 持久化 | `full-stack-software-engineer` | 已完成。`operator_gateway_http.py` 增加 `MockCloudStore(state_path=...)`、原子持久化、队列/status/ack reload 和敏感字段过滤 | local mock cloud `software_proof_docker_only` |
| KR6-2 robot cursor/status recovery | `robot-software-engineer` | 已完成。`remote_bridge.py` 增加 `cursor_state_path`，从状态文件恢复 `last_terminal_ack_id`，terminal ACK 成功后原子持久化 cursor | local bridge `software_proof_docker_only` |
| KR6-3 bearer/auth readiness | `full-stack-software-engineer` | 部分完成。`remote_readiness` 和敏感字段过滤能支撑 phone-readable 状态，不泄露 token、串口、ROS topic 或硬件参数 | 未覆盖生产鉴权、HTTPS/TLS 或真实云账号 |
| KR6-4 弱网/重启前的 degradation | `full-stack-software-engineer` + `robot-software-engineer` | 部分完成。持久化队列/status/ack 与 cursor recovery 支撑进程重启复盘；ACK 未冒充 delivery result | 未做真实弱网、断网、4G/SIM 实测 |
| KR5-1 phone-readable remote status | `full-stack-software-engineer` | 已完成支撑项。`remote_readiness` 供未来手机端读取，`docs/product/mobile_user_flow.md` 已由工程 owner 更新 | 不是正式美观手机 UI 或用户实机验收 |

## 实际改动汇总

Task A `full-stack-software-engineer`：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`：增加 `MockCloudStore(state_path=...)`、原子持久化、敏感字段过滤、`remote_readiness` 派生。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`：增加 `mock_cloud_state_path` 参数。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`、`test_operator_gateway_static.py`：扩展持久化、readiness、敏感字段过滤覆盖。
- `docs/product/mobile_user_flow.md`：同步手机可读 remote readiness 口径。

Task B `robot-software-engineer`：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`：增加 `cursor_state_path`、`last_terminal_ack_id` 恢复和 terminal ACK 后原子 cursor 持久化。
- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`：扩展 cursor recovery 与 ACK 持久化覆盖。
- `docs/product/remote_4g_mvp.md`：同步 ACK 与 delivery result、cursor recovery、local mock proof 边界。

Task C `product-okr-owner`：

- 创建本文件、`side2side_check.md`、`final.md`。
- 保守更新 `OKR.md` 当前快照：O6 从约 12% 记录到约 16%，O5 仅小幅记录支持触点进展到约 31%，O1/HIL 不提升。

## 验证结果

Task A fenced validation：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py

Ran 64 tests OK
py_compile OK
scoped git diff --check OK
```

Task B fenced validation：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py

Ran 20 tests OK
py_compile OK
scoped git diff --check OK
```

Final integration smoke：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py

Ran 84 tests in 23.080s OK

py_compile for operator_gateway_http.py/operator_gateway.py/operator_gateway_diagnostics.py/remote_bridge.py -> exit 0
scoped git diff --check for touched behavior/doc files -> exit 0
```

## 集成结论

- mock cloud 持久化队列/status/ack 与 `remote_bridge` cursor state 可同时存在。
- 持久化与 readiness 语义不写 token、串口、ROS topic 或硬件参数。
- ACK 仍只表示 robot bridge 接收/提交，不冒充 delivery result。
- `last_ack_id` / cursor 按 opaque cursor 处理，没有依赖字符串排序。

## 偏差和未完成事项

- 未完成真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、生产鉴权、OSS/CDN 图片链路和生产运维。
- 未完成真实弱网/断网恢复实测；本轮只证明 local mock 持久化与进程级恢复语义。
- 未完成正式美观手机 UI 和普通用户实机验收；O5 只记支持触点进展。
- 未完成真实硬件/HIL、Nav2/fixed-route 实跑和 WAVE ROVER feedback；O1 不提升。

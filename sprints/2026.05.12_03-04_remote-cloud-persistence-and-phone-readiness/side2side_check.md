# Sprint 2026.05.12_03-04 Remote Cloud Persistence And Phone Readiness - Side By Side Check

## 状态

- 阶段：side2side_check
- 时间：2026-05-12 01:52 Asia/Shanghai
- 验收人：`product-okr-owner`
- 验收边界：产品口径验收 + 工程 smoke 证据复核；不新增工程实现命令，不声明真实云、真实 4G 或 HIL

## 用户价值对照

| PRD 目标 | 实际结果 | 结论 |
| --- | --- | --- |
| 服务重启后 command queue/status/ack 不只存在内存里 | `MockCloudStore(state_path=...)` 提供原子持久化和 reload；Task A 64 tests OK | 通过，限 local mock proof |
| robot bridge 重启后能恢复 cursor 边界 | `remote_bridge` 通过 `cursor_state_path` 恢复 `last_terminal_ack_id`，terminal ACK 成功后原子写入 | 通过，限 local bridge proof |
| phone-readable readiness 不暴露底层硬件和敏感信息 | `remote_readiness` 派生，敏感字段过滤；集成结论确认不写 token、串口、ROS topic、硬件参数 | 通过，支撑 O5 但不是正式 UI |
| ACK 不冒充真实送达完成 | 集成 smoke 结论明确 ACK 与 delivery result 分离 | 通过 |
| cursor 不依赖字符串排序 | 集成 smoke 结论确认 `last_ack_id` / cursor 按 opaque cursor 处理 | 通过 |

## OKR Side By Side

| Objective | 收口前 | 收口后 | 产品判断 |
| --- | --- | --- | --- |
| O6 4G 云中转 + OSS/CDN | 约 12%，local mock command loop | 约 16%，local mock persistence + cursor recovery + phone-readable readiness | 可小幅上调；仍不是生产云/4G |
| O5 手机体验与量产边界 | 约 30%，phone-safe command/status/ack 支撑触点 | 约 31%，新增 remote readiness 支撑未来手机端解释链路状态 | 只小幅记录；没有正式手机 UI |
| O1 硬件协议可信底盘 | 约 75%，真实 HIL 仍缺 | 不变 | 本轮无 `/dev/ttyUSB0`、WAVE ROVER feedback 或 `hil_pass` |

## 验收命令复核

工程 owner 已完成并报告：

```text
Task A: Ran 64 tests OK; py_compile OK; scoped diff check OK.
Task B: Ran 20 tests OK; py_compile OK; scoped diff check OK.
Final integration smoke: Ran 84 tests in 23.080s OK.
Final py_compile: exit 0.
Final scoped git diff --check: exit 0.
```

Product 收口额外执行文档围栏：

```text
git diff --check -- OKR.md \
  sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/tech-done.md \
  sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/side2side_check.md \
  sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/final.md
```

结果记录在最终回复和 `final.md`。

## 风险和阻塞

- 真实云、HTTPS/TLS、公网入口、生产 bearer/账号体系、OSS/CDN、SIM/4G 未验证。
- local mock 持久化证明的是控制面恢复语义，不证明真实垃圾送达、真实 Nav2/fixed-route 或底盘执行。
- `remote_readiness` 是 phone-readable 数据底座，不等于美观正式手机 UI 或普通用户验收。
- O1/HIL 没有新增 evidence packet，不能提升。

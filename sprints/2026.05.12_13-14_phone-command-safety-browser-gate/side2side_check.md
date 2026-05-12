# Sprint 2026.05.12_13-14 Phone Command Safety Browser Gate - Side-by-Side Check

## 状态

- 阶段：side2side_check
- 验收时间：2026-05-12 13:42 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 验收结论：P0 通过；证据边界保持 `software_proof_docker_phone_command_safety_browser_gate`。

## 用户价值和产品北极星

本轮把手机首屏从“显示状态”推进到“阻止不安全命令”。普通用户现在可以通过 Start、Confirm dropoff、Cancel、Diagnostics 的按钮态和中文解释理解当前下一步，而不是自己判断 raw `can_*` 字段、ACK、云状态或诊断引用。

北极星仍是：手机是普通用户唯一入口，4G 场景走云端中转。当前验收只证明 local/Docker/browser-API 软件围栏内的命令安全 gate，不证明真实手机、真实云、真实 4G、真实 OSS/CDN、真实送达或 HIL。

## OKR 映射

- O5 KR1：手机最小流程的关键操作已被 `command_safety.actions.*.enabled` 约束。
- O5 KR5：禁用原因、等待 ACK、人工接管和诊断入口均保留用户可读解释。
- O5 KR7：本轮完成首屏按钮 wiring 的 handler/unit-test 级验收；真实手机浏览器/设备验收仍未完成。
- O6 KR1：命令/status/ACK 契约保持 `trashbot.remote.v1` 语义，未暴露 `/cmd_vel` 或底层硬件控制。
- O6 KR6：`status_stale`、`command_pending`、`auth_failed`、`cloud_unreachable`、`malformed_response` 和 manifest 异常会进入手机操作 gate。

## P0 对照验收

| PRD P0 | 验收结果 | 证据 |
| --- | --- | --- |
| Start/Confirm/Cancel/Diagnostics 由 readiness/action permissions 约束 | 通过 | `/api/status.phone_readiness.command_safety` 新增 `trashbot.command_safety.v1`；operator 首屏按钮消费 `command_safety.actions.*.enabled`，旧 raw `can_*` 字段仅保留兼容输入。 |
| ACK 不等于 delivery success | 通过 | `tech-done.md` 记录 ACK copy 明确 ACK 只是 command accepted/processing evidence；delivery success 仍看任务终态。 |
| `status_stale`、`command_pending`、`auth_failed`、`cloud_unreachable`、`malformed_response` 不得 green ready | 通过 | Full-stack 覆盖这些状态，并使主路径命令禁用或降级。 |
| manifest `missing/invalid/stale` 不得让主路径完整 ready | 通过 | manifest 异常会阻断 primary commands；Diagnostics 保持可进入并解释阻断原因。 |
| 敏感字段 redaction 保持 | 通过 | docs 和 `tech-done.md` 明确不展示 token、Authorization、AK/SK、root password、serial、baudrate、ROS topic、`/cmd_vel`、WAVE ROVER 参数。 |
| Robot command/status/ack/cursor 兼容性不退化 | 通过 | Robot fence：`Ran 31 tests in 15.230s OK`。 |

## 验证证据

Full-stack targeted tests：

```text
Ran 64 tests in 17.299s

OK
```

Python compile fence：

```text
passed with no output
```

Scoped implementation diff check：

```text
passed with no output
```

Robot compatibility fence：

```text
Ran 31 tests in 15.230s

OK
```

Browser/API 围栏采用 Option B：通过 HTTP handler/unit test 覆盖 HTML 按钮 wiring 和 API payload shape；没有真实浏览器截图，也没有真实手机设备验收。

## 证据边界

本轮证据只能写为 `software_proof_docker_phone_command_safety_browser_gate`。

不得升级为：

- 真实手机 app 或真实手机浏览器验收。
- 真实云、HTTPS/TLS、公网入口或真实 4G/SIM。
- 真实 OSS upload、STS issuance、CDN origin fetch 或生产账号。
- Nav2/fixed-route 送达、WAVE ROVER motion、HIL 或真实垃圾送达。

## 责任 Engineer

- `full-stack-software-engineer`：已完成 phone UI/API command safety gate、产品文档同步、targeted tests、py_compile 和 scoped diff check。
- `robot-software-engineer`：已完成 remote bridge command/status/ack/cursor compatibility fence。
- `product-okr-owner`：本文件完成 P0 对照验收；`final.md` 和 `OKR.md` 做保守收口。

## 剩余风险

- 缺真实手机设备/真实浏览器截图，O5 不能声明正式手机端验收完成。
- 缺真实云、真实 4G/SIM、HTTPS/TLS 公网入口、OSS/CDN 实流量和生产账号，O6 不能声明生产链路闭环。
- 缺 Nav2/fixed-route 实跑、WAVE ROVER、HIL 和真实送达，本轮不得影响 O1/O2/O3 实机完成度。

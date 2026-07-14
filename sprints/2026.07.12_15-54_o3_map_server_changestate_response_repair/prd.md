# PRD - O3 Map Server ChangeState Response Repair

## 用户价值

本轮服务于普通手机用户一键发车送垃圾的前置可靠性：真实上位机 fixed-route/nav 必须先让 `/map_server` lifecycle clean/active，才能恢复 `/map`、AMCL、TF 和 planner-only path generation。当前不是做新 UI 或包装证据，而是解除 same-run path generation 和后续 route execution 的上游阻塞。

## 背景

O5 是当前最低 Objective，约 `85%`，但缺真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence；继续 support-only packet 不允许计 OKR 增量。因此本轮继续现场 O3/O1 strict no-motion lane。

上一轮已经把 `/map_server` blocker 定位到：

- `map_server_changestate_response_failure_after_image_load_before_map_read_completed`
- lifecycle manager configure request 已发出
- map_server callback 已进入
- yaml/image load 已开始
- ChangeState failure 发生在 map read completed 前

## 需求

1. 在 strict no-motion 前提下，继续修复或下钻 `/map_server` lifecycle configure failure。
2. 优先产出可用于下一步修复的 root cause，不继续添加不消费的 wrapper 字段。
3. 若能修复 `/map_server` lifecycle clean/active，继续读取 `/map`、AMCL、dynamic TF 和 planner-only path gate，但仍不进入运动。
4. 同步 navigation 文档和 sprint `tech-done.md`，让证据边界和下一步明确。

## 非目标

- 不做 O5 support-only、production readiness、UI/API/archive 包装。
- 不做 NavigateToPose、route execution、`/cmd_vel`、`/api/base/manual` 或底盘 UART。
- 不修改 WAVE ROVER、ESP32、UART、串口、波特率、接线或硬件配置。
- 不把 lifecycle clean 自动解释为 `safe_to_control=true` 或 OKR 百分比提升。

## 验收

必须满足：

- `tech-done.md` 有实际改动、验证结果、失败定位、剩余风险。
- true-board artifact pulled back 到本 sprint `artifacts/`。
- local dry-run fail-closed 或成功字段清楚，不冒充 true-board proof。
- scoped `git diff --check` 通过。

产品可接受结果：

- `/map_server` lifecycle clean/active；或
- 输出更窄 canonical classification，例如 callback exception、return false after image load、map IO stuck/late completion、ChangeState RPC response false/timeout、executor starvation、process exit、parameter invalid、AMCL configure takeover 等。

产品不可接受结果：

- 只重复 `map_server_changestate_response_failure_after_image_load_before_map_read_completed`，没有新增 timing、日志、service response、process/exception 或 AMCL takeover 证据。

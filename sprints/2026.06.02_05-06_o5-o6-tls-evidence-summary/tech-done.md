# O5/O6 TLS Evidence Summary 收口

sprint_type: micro

- owner: full-stack-software-engineer
- 时间: 2026-06-02 05:00-06:00
- 范围: O5/O6 external live probe 在 HTTPS cloud base URL 下的 TLS evidence summary 采集、脱敏展示和 Product/OKR 收口。

## 用户价值和产品北极星

本轮价值是让运营/排障人员在 PC workstation 看到 O5/O6 external probe 的 TLS 摘要合同，而不是只能凭 stdout 或 raw endpoint 猜测 HTTPS 侧是否具备可观测证据。它服务于北极星中的"数据可复盘、云端可运营"，但仍只是软件证据和运维可见面，不代表普通手机用户已经完成真实 4G/生产云闭环。

## 实际改动

- Full-stack 已增强 `cloud-relay/scripts/o5_o6_external_live_probe.py`：当 cloud base URL 为 HTTPS 时，Python stdlib runner 采集脱敏 TLS evidence summary，并保持只读 GET-only。
- Full-stack 已更新 PC workstation artifact API 与 shared contract，消费并展示 TLS summary contract。
- Full-stack 已同步接口/产品文档：`docs/product/remote_4g_mvp.md`、`docs/interfaces/o6_cloud_archive_core_api.md`、`docs/product/pc_tools_workstation.md`。
- 安全边界保持：no POST、no `/robots/*`、no hardware read、no raw host/base URL/token/cert DN/traceback/artifact path；不证明 production ready、4G、DB/queue、OSS/CDN、phone/browser、delivery success。
- Product 本轮只做 OKR/sprint 收口，没有修改产品代码。

## 验证结果

Full-stack 返回的验证结果如下：

1. `python3 -m py_compile cloud-relay/scripts/o5_o6_external_live_probe.py`
   - 结果：通过。
2. `PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior:onboard/src/ros2_trashbot_nav python3 -m unittest cloud-relay/tests/test_o5_o6_external_live_probe.py`
   - 结果：`Ran 7 tests in 3.990s`，`OK`。
3. `cd pc-tools/workstation && npm run test -- --runInBand`
   - 结果：失败，Vitest 报 `Unknown option --runInBand`。
   - 失败定位：验收命令参数兼容问题，`--runInBand` 是 Jest 风格参数，不适用于当前 Vitest 命令。
4. `cd pc-tools/workstation && npm run test`
   - 结果：通过，2 files / 53 tests passed。
5. `cd pc-tools/workstation && npm run build`
   - 结果：通过。
6. `cd pc-tools/workstation && npm run lint`
   - 结果：通过。
7. scoped `git diff --check`
   - 结果：通过。

## OKR 映射和方向判断

- Objective 1：保持约 93%。本轮协调者先尝试 `ssh -o BatchMode=yes -o ConnectTimeout=5 -p 37878 root@192.168.1.11 'hostname; date; python3 --version'`，结果 `ssh: connect to host 192.168.1.11 port 37878: No route to host`。按同一 blocker 重复消费红线，本轮不继续消费 O1 SSH/T1001 blocker，切到 O5/O6。
- Objective 5：从约 94% 保守调整到约 95% `software + external probe TLS evidence summary visible in PC workstation`，方向判断为继续。
- Objective 6：从约 94% 保守调整到约 95% `software + external probe TLS evidence summary visible in PC workstation`，方向判断为继续。
- Objective 7：保持约 95%。本轮只是复用 PC workstation/O7 Console 展示面，不推进 PC/browser RTC 长稳态、真实手机或完整上车任务闭环。

## OKR 最低优先级说明

当前最低 Objective 仍为 O1 约 93%。本轮没有继续针对 O1，是因为同一远端 SSH/T1001 blocker 再次表现为 `No route to host`，继续重复消费会违反 blocker 红线且不会产生新证据；因此切到 O5/O6，推进不依赖远端 SSH 的 TLS evidence summary 可见面。

## KR 拆解和历史归档

- O5 KR1/KR5/KR6：新增 HTTPS 外部 probe 的 TLS evidence summary 脱敏采集与 PC 可见证据，增强控制面 readiness / credential redaction / graceful degradation 的运营证据链。
- O6 KR6：PC/API 消费 O6 archive endpoint 相关 TLS 摘要，让运营侧能查看 O6 external probe 的 schema/reachability/TLS evidence 状态。
- 本轮没有 KR 可移入真实材料历史归档区。O5/O6 仍留在当前推进区，因为真实公网 HTTPS/TLS、4G、production DB/queue、OSS/CDN、phone/browser 和上车数据仍未证明。

## 剩余风险

- TLS evidence summary 只是在 HTTPS cloud base URL 条件下采集并脱敏展示摘要，不回显 raw host/base URL/token/cert DN，也不证明真实生产云 TLS 已完成验收。
- 真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实 phone/browser、robot ACK、delivery success 仍为 `not_proven`。
- O1 SSH/T1001 blocker 本轮只记录 `No route to host` 并停止重复消费；真实 `T=1001`、UART/HIL、底盘可控和 LiDAR `/scan` 仍未推进。

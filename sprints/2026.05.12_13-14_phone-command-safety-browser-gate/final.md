# Sprint 2026.05.12_13-14 Phone Command Safety Browser Gate - Final

## 状态

- 阶段：final
- 收口时间：2026-05-12 13:45 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 最终结论：本轮达成 P0，建议保守上调 O5/O6；证据边界保持 `software_proof_docker_phone_command_safety_browser_gate`。

## 用户价值和产品北极星

用户价值：普通手机用户不再只看到“可点击按钮”，而是能在首屏看到 Start、Confirm dropoff、Cancel、Diagnostics 是否安全可点、为什么被阻断，以及 ACK 后为什么还要继续等待任务状态。

产品北极星：手机作为普通用户唯一入口，必须先阻断不安全操作，再进入真实云/4G/硬件闭环。本轮是手机触点安全 gate 的软件证明，不是正式手机产品或实机送达验收。

## OKR 映射和 KR 更新建议

- O5 KR1/KR5/KR7：建议从约 38% 保守上调到约 40%。理由是 command safety 已被 UI/API 消费，P0 状态和用户文案覆盖完整；限制是真实手机设备/浏览器验收仍缺。
- O6 KR1/KR6：建议从约 38% 保守上调到约 39%。理由是远程 readiness 的 ACK、status stale、auth/cloud/malformed 和 manifest 异常已经影响手机命令 gate，且 robot compatibility fence 通过；限制是真实云、真实 4G、OSS/CDN 实流量和生产部署仍缺。
- O1/O2/O3/O4：不建议上调。本轮没有硬件、Nav2/fixed-route、相机或 HIL 新证据。

## 本轮核心抓手

核心抓手是把 `/api/status.phone_readiness.command_safety` 做成按钮级 safety contract：

- `schema=trashbot.command_safety.v1`。
- per-action gates：`start`、`confirm_dropoff`、`cancel`、`diagnostics`。
- Operator 首屏从 raw `can_collect/can_confirm_dropoff/can_cancel` 改为消费 `command_safety.actions.*.enabled`。
- Diagnostics 保持 enabled，但显示阻断原因。
- ACK 文案明确 ACK 只是 command accepted/processing evidence，不等于 delivery success。

## 实际完成

- Full-stack 完成 `/api/status.phone_readiness.command_safety` 和 operator 首屏按钮 gate。
- 覆盖 ready、status stale、command pending、auth failed、cloud unreachable、malformed response、manifest missing/invalid/stale、manual takeover。
- `docs/product/mobile_user_flow.md` 和 `docs/product/remote_4g_mvp.md` 已同步 command safety、ACK 语义和证据边界。
- Robot compatibility fence 未发现 command/status/ack/cursor 退化。
- Sprint 已补齐 `side2side_check.md` 和本 `final.md`。

## 验收结果

Full-stack：

```text
Ran 64 tests in 17.299s

OK
```

Robot：

```text
Ran 31 tests in 15.230s

OK
```

`py_compile` 和 scoped implementation `git diff --check` 均通过。Product acceptance diff check 在本轮 final 后另行记录。

Browser/API 围栏采用 Option B：HTTP handler/unit test 覆盖 HTML 按钮 wiring 和 API payload shape。该选择满足本轮 P0，但不替代真实浏览器截图、真实手机设备或生产手机 app 验收。

## 证据边界

本轮唯一允许证据边界：

```text
software_proof_docker_phone_command_safety_browser_gate
```

明确未证明：

- 真实手机 app、真实手机浏览器/设备验收、普通用户实机验收。
- 真实云、HTTPS/TLS、公网入口、真实 4G/SIM。
- 真实 OSS upload、STS issuance、CDN origin fetch、生产账号、生产 DB/queue。
- Nav2/fixed-route 送达、WAVE ROVER motion、HIL、真实垃圾送达。

## 下一步建议

1. O5 下一轮优先补真实手机浏览器/设备验收：至少 iPhone/Android 主流宽度截图、按钮 hit area、首屏不重叠和 ACK 文案可读性。
2. O6 下一轮优先补真实云预生产入口或 4G/SIM 端到端 smoke，继续保持 ACK 与 delivery success 的边界。
3. O1/O2/O3 只有在真实串口/HIL 或真实路线 evidence 可用时再推进，不用本轮软件 gate 冒充实机完成度。

## 剩余风险

- 手机端仍是本地 fallback HTML 和 API proof，不是正式手机 app。
- `software_proof` 只能证明 gate 逻辑，不证明真实网络、真实云、真实硬件或真实送达。
- 若后续引入真实浏览器自动化或生产云，需要重新跑 redaction、ACK 语义和 command safety P0 对照。

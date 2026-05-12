# Sprint 2026.05.12_15-16 Phone Browser Acceptance Gate - Side2Side Check

## 状态

- 阶段：side2side_check
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 验收结论：通过 Product acceptance
- 证据边界：`software_proof_docker_phone_browser_acceptance_gate`

## 用户价值和产品北极星

本轮把 O5 的手机入口从 API/HTML handler proof 推进到真实本地 Chrome browser proof。普通 operator 在手机宽度浏览器里能看到主操作、阻断原因、ACK 语义和 Diagnostics 入口，且不会把 Diagnostics 可进入误读成 Start/Confirm/Cancel 可执行。

北极星保持为：手机是普通用户唯一入口。本地 operator HTML 仍是 fallback 调试入口，但本轮证明它已经具备可复查的手机浏览器可用性围栏。

## OKR 映射

- O5 KR1：手机最小流程的首屏状态查看、主操作按钮和诊断入口进入真实浏览器验收。
- O5 KR5：普通用户无需命令行即可理解当前不能执行主操作的原因，以及 ACK 不等于送达成功。
- O5 KR7：覆盖主流窄屏尺寸、最小 44px hit area、首屏可交互、不重叠和中文优先文案。
- O6 KR6：仅消费 network recovery / command safety 相关 phone-safe 摘要背景；本轮不提升 O6。

## 验收对照

| 验收项 | 计划口径 | 实际证据 | 结论 |
| --- | --- | --- | --- |
| 真实浏览器运行 | 不再重复 API/handler proof，必须打开本地 operator 页面 | Summary artifact `evidence/phone_browser_acceptance_summary.json`：`ok=true`，browser 为 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` | 通过 |
| viewport 覆盖 | 至少覆盖 phone narrow 和窄桌面/平板宽度 | `390x844` 与 `768x900` 两组 viewport 均产出 JSON 和 PNG 截图 | 通过 |
| hit area | Start、Confirm dropoff、Cancel、Diagnostics 均 >= 44 CSS px | 两组 viewport 均为 `hit_area_status=passed` | 通过 |
| 布局安全 | 关键文案不重叠、不横向溢出 | 两组 viewport 均为 `overlap_status=passed`、`overflow_status=passed` | 通过 |
| ACK 语义 | ACK 文案首屏可见，且不等于送达成功 | 两组 viewport 均为 `ack_copy_visible=true`；截图已只读核对首屏可见 | 通过 |
| 主操作安全 | 阻断状态下 Start/Confirm/Cancel disabled | 两组 viewport 均为 `primary_actions_disabled=true` | 通过 |
| Diagnostics | Diagnostics 可进入，但不让主操作误显示为可用 | 两组 viewport 均为 `diagnostics_accessible=true`，且 `primary_actions_disabled=true` | 通过 |
| 首屏可操作 | 手机宽度下主按钮首屏可见 | 两组 viewport 均为 `first_screen_buttons_visible=true` | 通过 |
| phone-safe | 不展示 raw JSON、ROS topic、serial、token 或硬件参数作为用户主路径 | 两组 viewport 均为 `phone_safe_status=passed` | 通过 |

## 失败定位核对

Full-stack 记录的首次失败有效：Diagnostics 点击曾覆盖 status panel，导致 ACK copy 回退；移动端还暴露了长 boundary 裁切和按钮不在首屏。修复后 `/api/diagnostics` fetch 不再刷新 status，移动 CSS 加严，并复跑 browser gate 通过。

Product 判断：这是本轮真正的验收价值，因为它证明 browser gate 捕获了 API/handler proof 覆盖不到的可用性问题，并且修复后有同一 gate 的复验证据。

## 验收结论

本轮 P0 全部通过，O5 可从约 40% 保守上调到约 43%。上调理由是 KR7 从“按钮级 API/handler proof”推进到“真实本地 Chrome、两组 viewport、hit area、首屏可见、不重叠、ACK 语义和主操作阻断”的可复查 browser proof。

O6 保持约 41%。O1-O4 不提升。

## 剩余风险和证据缺口

- 没有真实 iPhone/Android 设备上的 Safari/Chrome 验收。
- 没有正式 native app、生产登录、真实远程手机流程或普通用户实机验收。
- 没有真实云/4G、HTTPS/TLS 公网入口、OSS/CDN 实流量或生产 DB/queue。
- 没有 Nav2/fixed-route 真实送达、WAVE ROVER motion、HIL、真实串口反馈或真实垃圾送达。
- 当前证据只能标为 `software_proof_docker_phone_browser_acceptance_gate`，不能挪用为 `hil_pass`、真实云 proof 或真实手机设备 proof。

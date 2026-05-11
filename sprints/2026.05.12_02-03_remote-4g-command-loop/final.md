# Sprint 2026.05.12_02-03 Remote 4G Command Loop - Final

## 状态

- 阶段：final
- 时间：2026-05-12 01:20 Asia/Shanghai
- Product Owner：`product-okr-owner`
- Sprint 结论：完成 O6 local mock cloud / remote bridge command loop 的 software-only 收口
- 证据边界：`software_proof_docker_only` / local mock cloud

## 用户价值和产品北极星

本轮把普通手机用户远程下发任务的控制面从文档推进到可验证软件路径：提交 command、robot outbound polling、behavior-level adapter、ack/status 回写、入口读取状态。它服务于“手机和小车不在同一 WiFi 时仍能通过云端中转控制小车”的北极星。

当前仍不是完整 4G 产品：没有真云、真 SIM、生产鉴权、OSS/CDN、HIL、真实送达或美观手机端验收。

## 实际交付

| Task | Owner | 交付结果 | 验证 |
| --- | --- | --- | --- |
| Task A mock cloud/operator endpoints | `full-stack-software-engineer` | operator HTTP 支持 command submit、next polling、status post/read、ack post/read | 31 tests OK |
| Task B remote bridge polling/ack | `robot-software-engineer` | `bearer_token` 兼容 `auth_token`，支持 `last_ack_id`、duplicate ack reuse、malformed/expired terminal ack、busy collect ignored | 16 tests OK |
| Task C integration smoke | `robot-software-engineer` | A+B 统一测试，修复 `last_ack_id` 字符串比较 bug，改为队列顺序 + ack 状态 | 48 tests OK；`py_compile` OK；scoped diff check OK |
| Product acceptance | `product-okr-owner` | 完成 side-by-side 验收、OKR 快照边界和 final 收口 | markdown scoped diff check OK |

## OKR 影响

- O6：从约 5% 保守提升到约 12%。理由是 KR1 的 commands/status/ack 和 robot outbound polling 已有 local mock cloud 软件证据，但仍缺真云、真 4G/SIM、生产鉴权、OSS/CDN、弱网恢复和生产运维。
- O5：只作为支持触点进展记录，不建议大幅提升。operator HTTP 入口能让 command/status/ack 对普通用户口径更安全，但不是正式美观手机端，也没有真实用户验收。
- O1/O2/O3/O4：本轮不提升。没有真实硬件、Nav2/fixed-route、相机或 HIL。

## 做什么 / 不做什么

已做：

- 建立本地 mock cloud command/status/ack 控制面。
- 建立 robot remote bridge outbound polling 和终态 ack 处理。
- 用集成 smoke 证明 command id 不能按字符串排序，修复为队列顺序和 ack 状态。
- 明确所有证据为 software-only/local mock。

未做：

- 真实云部署、HTTPS/TLS、公网入口、域名切流和生产运维。
- 真实 4G/SIM、运营商网络、弱网、断网恢复实测。
- OSS/CDN 图片链路、STS 临时凭证、密钥 rotate 和生产权限。
- 真机 ROS2 action server、真实 Nav2/fixed-route、WAVE ROVER/HIL。
- 正式手机 UI 美观可用验收。

## 剩余风险和下一步

1. O6 下一轮应优先从 local mock cloud 走向最小部署环境：生产前仍可用 staging cloud，但必须验证 bearer token、HTTPS、持久化队列和跨进程 cursor。
2. `last_ack_id` 的持久化、跨重启和未知 cursor 策略需要在真实云服务端 contract 中定稿。
3. 4G graceful degradation 仍只覆盖软件围栏；需要真实 SIM/弱网或网络故障注入验证。
4. OSS/CDN 仍是文档级目标，本轮没有图片/快照上传和 CDN 引用证据。
5. O5 需要独立手机 UI 质量 sprint，不能把 operator/debug 入口当正式用户体验。

## 收口判断

本 sprint 可收口为 O6 的第一段软件控制面证据。它足以支撑 OKR 快照保守提升，但不能用于宣称真实 4G 产品可用、生产云已完成、HIL 通过或用户送垃圾闭环完成。

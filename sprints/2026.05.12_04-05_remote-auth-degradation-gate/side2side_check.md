# Sprint 2026.05.12_04-05 Remote Auth Degradation Gate - Side2Side Check

## 状态

- 阶段：side2side_check
- 更新时间：2026-05-12 04:55 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化
- 支撑 Objective：O5 手机用户体验与量产边界
- 证据边界：Docker/local `software_proof_docker_only`

## 用户价值和产品北极星

北极星保持不变：普通用户只用手机，通过 4G 云中转控制小车送垃圾，并能看懂远程链路是否可用、失败原因是什么、下一步应该等待、重试还是联系支持。

本轮验收价值是把 remote control 从“local mock 能提交命令”推进到“鉴权失败、云不可达、响应异常时也不会误报成功、不会泄露敏感字段、不会误推进 cursor”。

## OKR 映射

| Objective | 验收结论 |
| --- | --- |
| O6 | 通过 local/mock software proof 支撑小幅提升：bearer auth gate、readiness/degradation、cursor safety 和敏感字段过滤已形成围栏证据。 |
| O5 | 支撑小幅提升：`safe_phone_copy`、`auth_state`、`degradation_state`、`retry_hint` 可服务未来正式手机状态页。 |
| O1/O2/O3/O4 | 本轮无真实硬件、真实 Nav2/fixed-route、真实相机或 HIL，不提升。 |

## KR 拆解或更新

| KR | 本轮证据 | 验收 |
| --- | --- | --- |
| O6 KR1 command/status/ack | local/mock API bearer gate；remote bridge cloud failure 分类；ACK 仍为 command envelope state | 通过 |
| O6 KR5 凭证管理 | phone/status/diagnostics/mock state 敏感字段过滤；token/header 不回显 | 通过 |
| O6 KR6 graceful degradation | cloud unreachable/auth failed/malformed response 不推进 cursor、不触发本地 action、不伪造 ACK 成功 | 通过 |
| O5 KR1/KR5/KR7 支撑 | `remote_readiness` 增加 auth/degradation/safe phone copy/retry hint | 通过，仍非正式 UI 验收 |

## Side-by-side 验收

| PRD 验收口径 | 工程证据 | Product Acceptance |
| --- | --- | --- |
| bearer gate 开启时拒绝缺失/错误 token | Task A targeted operator tests `Ran 66 tests ... OK` | 通过 |
| 正确 bearer 保持 command/status/ack 语义 | Task A targeted operator tests `Ran 66 tests ... OK` | 通过 |
| `remote_readiness.auth_state/degradation_state/safe_phone_copy` phone-safe | Task A 文档与测试记录；共享 docs 已同步 | 通过 |
| 敏感字段不进入 phone/status/diagnostics/mock persisted state | Task A 敏感字段过滤测试通过 | 通过 |
| cloud unreachable/auth failed/malformed response 不推进 cursor | Task B remote bridge tests `Ran 23 tests ... OK` | 通过 |
| malformed response 不触发本地 action | Task B remote bridge tests `Ran 23 tests ... OK` | 通过 |
| Task A + Task B 合并后无接口冲突 | Task C smoke `Ran 89 tests in 25.691s OK` | 通过 |
| 共享 docs 和 OKR 边界同步 | `docs/product/remote_4g_mvp.md`、`docs/interfaces/ros_contracts.md`、`OKR.md` 已更新 | 通过 |

## 做什么 / 不做什么

已做：

- 同步 bearer auth gate、auth/degradation readiness、safe phone copy、remote bridge failure/cursor contract。
- 创建本轮 Product Acceptance 收口文档。
- 保守更新 OKR：O6 提升到约 19%，O5 提升到约 32%。

未做且不应冒进声明：

- 未做真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、弱网运营商测试、生产 token rotate、OSS/CDN 图片链路。
- 未做正式美观手机 UI 或普通用户实机验收。
- 未做 WAVE ROVER、真实 UART、Nav2/fixed-route、相机或 HIL 验证。

## 对应责任 Engineer

| Owner | 责任与结果 |
| --- | --- |
| `full-stack-software-engineer` | Task A 完成 local/mock auth gate、phone readiness 和敏感字段过滤；targeted tests 通过。 |
| `robot-software-engineer` | Task B 完成 remote bridge degradation/cursor safety；Task C 完成合并 smoke。 |
| `product-okr-owner` | 本文件、`final.md`、共享产品/接口文档和 OKR 快照保守收口。 |

## 风险、阻塞和需要补齐的证据链

- 真实云、真实 4G/SIM、HTTPS/TLS、公网入口、生产鉴权 rotate、OSS/CDN 仍缺。
- ACK 仍只代表 command envelope 处理状态，不代表真实送达、导航成功、底盘运动或 HIL。
- `remote_ready=true` 只表示当前 local/mock control-plane 可以继续，不证明真实云或 4G 可用。
- O6 下一步应进入真实云最小部署/生产鉴权/弱网恢复验证，或先补齐云部署前的配置与 rotate 方案。


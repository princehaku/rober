# Sprint 2026.05.12_02-03 Remote 4G Command Loop - Side2Side Check

## 状态

- 阶段：side2side_check
- 时间：2026-05-12 01:20 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 验收结论：通过 software-only 围栏；可以作为 O6 本地 mock cloud / remote command loop 的软件证据
- 证据边界：`software_proof_docker_only` / local mock cloud，不是真云部署、真实 4G/SIM、生产鉴权、OSS/CDN 或 HIL

## 用户价值和产品北极星

北极星仍是普通手机用户不接触 ROS2、SSH、串口、WiFi 直连或 `/cmd_vel`，也能远程提交垃圾投递任务、查看状态、理解异常。本轮把 O6 从“产品文档 contract”推进到“本地可测试的 command -> polling -> ack/status 控制面”，让正式 4G 路径有了第一条可验证软件链路。

这不是完整产品闭环：用户价值只覆盖远程控制面最小路径，不覆盖真实云部署、真实 4G 网络、真实手机 UI 美观度、生产账号、图片链路或真实送达。

## PRD 对照

| PRD / Tech Plan 验收项 | 实际结果 | 结论 |
| --- | --- | --- |
| Cloud command queue：`POST /robots/{robot_id}/commands`、`GET /commands/next` | Task A 已实现 operator HTTP mock cloud endpoints，覆盖 command submit 和 robot polling；31 tests OK | 通过 |
| Status and ack loop：status post/read、ack post/read | Task A 已支持 status post/read、ack post/read；Task C 集成读写闭环 48 tests OK | 通过 |
| Remote bridge outbound polling | Task B 已支持 `bearer_token`，兼容 `auth_token`，带 `last_ack_id` polling，16 tests OK | 通过 |
| Duplicate / expired / malformed / busy command 围栏 | Task B 覆盖 duplicate ack reuse、malformed/expired terminal ack、busy collect ignored；Task C 修复 `last_ack_id` 字符串比较 bug | 通过 |
| Phone-safe minimum entry | 本轮使用 operator HTTP mock cloud 作为 local phone-safe command/status/ack 入口，不暴露 `/cmd_vel`、串口或硬件参数 | 通过，限 local mock |
| Docker/local software-only 验证 | A+B 统一测试 48 tests OK，`py_compile` 和 scoped `git diff --check` OK | 通过 |
| 不声明真实云、4G、OSS/CDN、HIL | 所有 sprint 收口明确为 `software_proof_docker_only` / local mock cloud | 通过 |

## OKR 映射

- O6：主推进。KR1 的 commands/status/ack 最小契约已从文档推进到 local mock cloud + remote bridge polling 软件闭环；完成度可从约 5% 保守上调到约 12%。
- O5：支持触点。operator HTTP 提供 phone-safe command/status/ack 入口，但没有美观手机端、主路径 ≤ 3 步、真实用户验收或生产账号；不建议大幅提升。
- O2：间接受益。remote command 仍进入 behavior-level adapter，不绕过任务层；但没有真实 delivery/nav 完成证据。
- O1/O3：无新增。没有真实 WAVE ROVER、串口、HIL 或 route replay。

## KR 拆解和验收口径

| KR | 本轮状态 | 责任 Engineer | 证据 |
| --- | --- | --- | --- |
| O6-KR1 cloud commands/status/ack | local mock cloud 通过围栏 | `full-stack-software-engineer` | Task A 31 tests OK；Task C 48 tests OK |
| O6-KR1 bridge outbound polling | bridge polling/ack/status 通过围栏 | `robot-software-engineer` | Task B 16 tests OK；Task C 48 tests OK |
| O6-KR5 credential boundary | 只做到 bearer token 字段和 env/config 口径，生产 provisioning/rotation 未做 | `robot-software-engineer` | `bearer_token` 兼容 `auth_token`；无生产鉴权证明 |
| O6-KR6 graceful degradation | malformed/expired/duplicate/busy 有软件围栏；真实 4G 中断、OSS 写失败、CDN 不可达未验证 | `robot-software-engineer` | remote bridge targeted tests |
| O5 phone-safe command touchpoint | local operator HTTP 入口可用于提交/读取 command/status/ack | `full-stack-software-engineer` | Task A endpoints；非正式手机 UI |

## 做了什么 / 没做什么

做了：

- 收口确认 Task A/B/C 已形成 mock cloud + remote bridge + phone-safe readback 的最小软件闭环。
- 明确 `last_ack_id` 以队列顺序和 ack 状态为准，command id 只做身份和 cursor 命中，不做字符串排序。
- 将 O6 进度提升建议限制在 conservative software proof 范围。

没做：

- 没有真实云部署、域名/TLS 切流、公网运维或生产鉴权。
- 没有真实 4G/SIM、运营商 NAT、弱网和断网恢复实测。
- 没有 OSS/CDN 上传、STS 凭证派发或图片大对象链路。
- 没有真实 ROS2 action server、Nav2/fixed-route、WAVE ROVER、串口或 HIL。
- 没有 O5 美观手机 UI 或普通用户实机验收。

## 风险、阻塞和证据链

- `software_proof_docker_only` 只能证明本地控制面契约和边界，不证明公网/4G/生产可用。
- `ack=acked` 只表示 robot bridge 接受或提交了行为层请求，不等于垃圾已送达。
- `last_ack_id` 指向队列中不存在的 command 时，目前 mock cloud 从队列头寻找未 ack command；真实云持久化队列需要定义跨重启 cursor 策略。
- `docs/product/cloud_4g_infrastructure.md` 在本工作区未找到；OKR 中仍引用该路径，后续需要在产品文档整理 sprint 里修正或恢复。
- O5 当前只是支持触点进展，不能替代正式手机 UI 质量验收。

# Sprint 2026.05.13_11-12 Mobile Cloud Readiness Summary Gate - PRD

## 用户价值

普通手机用户不应该看到“云中转未 ready”后只能猜是机器人坏了、网络坏了还是云配置未完成。本轮把 cloud/preflight/DB/queue readiness 转成手机首屏可读摘要：当前云中转状态、阻塞原因、下一步恢复建议、ACK 边界和不声明范围。

## 产品北极星

继续把 `rober` 做成普通手机用户可以操作、能看懂状态、能在失败时交接诊断的低成本 ROS2 自主垃圾投递机器人。本轮推进的是手机用户体验 Objective 4，不是云生产就绪或真实送达。

## OKR 映射

- Objective 4 KR1：手机端最小流程中补齐云中转 readiness 的可读状态和阻塞恢复提示。
- Objective 4 KR4：远程诊断最小数据包中增加 phone-safe cloud readiness 摘要。
- Objective 4 KR5：普通用户不用理解 ROS2、DB/queue、preflight、ACK，也能知道当前能否继续和该找谁处理。
- Objective 5 支援：复用上一轮 `cloud_db_queue_config_gate` / preflight 证据，但本轮不把 Objective 5 上调作为主目标。

## 需求

1. 手机首屏新增或扩展“云中转状态”区域，展示 schema、状态、阻塞原因、恢复建议、ACK 语义、evidence boundary。
2. mobile fixture 增加 `phone_cloud_readiness_summary` 或等价字段，覆盖最新 cloud DB/queue config gate 和 production preflight blocked 口径。
3. mobile static smoke 证明该摘要可见、phone-safe、不会打开控制动作，也不会把 ACK 写成 delivery success。
4. `/api/status` / `/api/diagnostics` 或接口文档需要承认该 metadata 是 phone-safe support/readiness summary，旧客户端可以忽略。
5. robot compatibility fence 证明该 metadata-only response 不触发 backend action、不 POST ACK、不推进或持久化 cursor、不污染 normalized command payload。

## 验收口径

- 手机端展示必须中文优先、fail closed、避免 raw JSON、ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、token、Authorization header、OSS AK/SK、DB/queue URL、本地路径、完整 artifact 或 checksum。
- ACK 文案必须保持 accepted/processing evidence only，不得写成云已连接、送达成功、投放完成、取消完成或 production ready。
- 只接受 scoped validation：mobile static unittest、相关 `py_compile`、remote bridge/protocol compatibility unittest、scoped `git diff --check`。

## 责任分工

- Task A - Full-Stack：手机端摘要展示、fixture/static smoke、mobile README 和 mobile user flow 文档。
- Task B - Robot：remote bridge/protocol metadata-only fence 和 ROS contract 文档。
- Task C - Product：sprint closeout、OKR/progress log 保守更新和证据边界复核。

## 风险

- 最大风险是把上一轮 cloud DB/queue config gate 写成真实云/production DB/queue ready。本轮必须保持 `production_ready=false`、blocked/needs_external_proof 等语义。
- 当前没有真实手机设备/browser，也没有真实云/4G 或硬件；本轮只能作为 Docker/local/static software proof。

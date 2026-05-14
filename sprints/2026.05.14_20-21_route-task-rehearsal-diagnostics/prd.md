# Sprint 2026.05.14_20-21 Route Task Rehearsal Diagnostics - PRD

sprint_type: epic

## 用户价值

现场或支持人员不应该只知道“PC 工具里有一个 artifact”。他们需要在 diagnostics 里看到当前 route/task rehearsal 是否可用、是否只是软件证明、对应的 `evidence_ref` 是什么、HIL/真实路线/交付成功还缺什么。这样后续拿到真实路线或硬件材料时，可以沿同一证据锚点补证，而不是重新猜测文件关系。

## 北极星对齐

北极星是普通手机用户和支持人员不接触 ROS2、串口或命令行，也能理解任务当前是否可复盘、为什么不能发车或为什么不能宣称送达成功。本轮只把 O2/O3 的软件复盘证据向诊断面推进，不改变控制链路。

## 范围

### P0

- route/task rehearsal artifact summary 必须包含 schema、evidence boundary、evidence_ref、crosscheck status、HIL alignment status、not_proven、下一步提示。
- diagnostics 只读消费 artifact，不触发 collect/dropoff/cancel、ACK、cursor、HIL、delivery success。
- summary 必须过滤本地路径、串口、bearer/Authorization、OSS AK/SK、DB/queue URL、traceback 等敏感信息。
- 文档同步 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`。

### P1

- 当 artifact 缺失、JSON 损坏、schema 不匹配或 crosscheck fail 时，diagnostics 给出结构化 blocked/read_error/unsupported 状态。
- 保留 `software_proof_docker_route_task_rehearsal_diagnostics_gate` 边界，不提升 O5/O1。

## 非目标

- 不实现真实 Nav2/fixed-route 跑车。
- 不接 WAVE ROVER、UART、真实串口或 HIL。
- 不做 production cloud、4G、OSS/CDN、DB/queue 外部证明。
- 不新增大测试套件；只做最小围栏验证。

## 验收

- Autonomy：PC 工具 artifact 输出或文档能明确 diagnostics consumption 字段与边界。
- Robot：`build_diagnostics_payload()` 可输出 `route_task_rehearsal` phone-safe summary，且测试证明该 summary 不改变控制语义。
- Product：OKR、progress log、tech-done、side2side、final 只声明软件证明 diagnostics gate。

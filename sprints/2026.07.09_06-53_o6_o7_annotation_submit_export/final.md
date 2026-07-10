# O6/O7 Annotation Submit Export Final

- sprint_type: epic
- close_time: 2026-07-09 07:28 CST
- product_owner: product-okr-owner
- target_objectives: O6, O7
- evidence_boundary: software_proof_local_mock_annotation_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 用户价值和产品北极星

本轮把 O6/O7 从“PC 可以看到路线回放和标注 draft，但 submit 被 fail-closed”推进到“PC 可以通过本机 adapter 调用 O6 local/mock archive，提交标注并导出 task-level JSONL 摘要”。运营/开发者现在能围绕同一 `task_id` 完成查看材料、提交 local/mock 标注、读取 receipt、查看 export manifest/sample rows 的最小数据闭环。

产品北极星保持不变：让普通用户把垃圾交给小车后，小车可验证地完成投递。本 sprint 只补数据复盘和训练材料链路，不声明真实投递、真实机器人控制、真实生产云或真实媒体可用。

## OKR 映射和方向判断

方向判断：继续 O6/O7，保守上调软件侧进度，不归档 KR。

- O6 从约 33% 保守上调到约 36%。理由：O6 已有 `POST /api/o6/archive/labels` 的 local/mock submit receipt、`GET /api/o6/archive/labels/<task_id>/export?format=jsonl` 的 task-level export、consumer labeling 摘要回读，并通过 `py_compile` 与 `149 tests OK`。
- O7 从约 34% 保守上调到约 37%。理由：PC adapter/UI 已能触发 local/mock submit/export、展示 receipt/export result、阻断危险输入与危险 true 字段，并通过 `catalog.test.ts` 204 passed、`App.test.ts` 247 passed、build、lint。
- O6 KR4/O6 KR6/O7 KR4 均只推进子能力，不标完成。当前仍缺真实 annotation API、真实 dataset export、production cloud、真实媒体和长期运营链路。
- O1/O5/O2/O3/O4 不调整；本轮没有新增 WAVE ROVER、真实 4G/TLS、真实路线、电梯/送达或手机验收证据。

## KR 拆解、更新或历史归档

- O6 KR4：新增 local/mock annotation submit 和 task-level export 软件证据，但真实标注 API、生产导出 worker、审计/rollback/autosave 仍未证明。
- O6 KR6：consumer detail 可读取 submit/export 摘要，PC 消费路径增强，但仍不是 production read API 或真实机器人数据流。
- O7 KR4：PC 标注工作台从 blocked receipt 展示推进到 local/mock submit/export 操作闭环，但仍不是真实标注平台完成态。
- 已完成 KR 历史归档：无。本轮不把任何 KR 标为完成或移入历史区。
- 历史记录位置：`docs/process/okr_progress_log.md` 新增 `2026-07-09 06-53｜o6_o7_annotation_submit_export` 条目。

## 本轮核心抓手

核心抓手是让上一轮 `submit_blocked_fail_closed` 后面出现可验证的软件写入和导出结果，同时继续让所有真实能力 fail-closed。O6 负责本地/mock archive write/export 合同，O7 负责 PC adapter/UI 主路径触发与展示。

## 需要做什么

下一步优先级仍应落到真实证据链，而不是继续叠加 local/mock wrapper：

1. 接入真实 `route.csv`、replay JSONL、keyframe 或 rosbag 到 O6 archive，并由 O7 route replay/labeling 主路径消费。
2. 补真实 keyframe/media ref 可访问性 smoke，确认 PC 不是只展示 ref 字符串。
3. 在具备生产 backing 后推进真实 annotation API、真实 dataset export worker、审计日志、rollback/autosave 和训练 split policy。

## 优先级和验收口径

- 当前最高优先级仍是现场 O3 验证 lane，其次 O6、O7。
- O6 下一步验收应要求真实或现场 artifact seed 进入 archive/read model，至少产生可复现 `route.csv`、replay JSONL、keyframe 或 rosbag 消费证据。
- O7 下一步验收应要求真实媒体可访问性或真实 artifact 驱动的回放/标注链路，而不是纯 fixture。
- 本轮验收通过的唯一边界是 `software_proof_local_mock_annotation_only`。

## 对应责任 Engineer

- `robot-software-engineer`：O6 archive、annotation submit/export、真实 artifact seed、生产 backing 前置接口。
- `full-stack-software-engineer`：O7 PC adapter/UI、媒体可访问性、真实 artifact 驱动的回放/标注工作台。
- `robot-algorithm-engineer`：提供 route.csv、replay JSONL、keyframe、rosbag 或现场路线证据，避免 O6/O7 自循环。
- `product-okr-owner`：维护 OKR 保守进度、验收边界和 KR 历史归档。

## 风险、阻塞和证据链缺口

- 本轮不证明真实 annotation API、真实 dataset export、production cloud、真实媒体、真实机器人控制或 delivery success。
- 不证明 production DB/queue、OSS/CDN、TLS/4G、真实隧道、真实机器人数据或生产级查询容量。
- 不证明真实 keyframe/media 可访问性、真实训练数据文件、训练 split policy、rollback、autosave 或审计日志。
- 不证明真实 RTC/视频、ASR/TTS、wheel raw 非零、真实电梯状态链、真实路线长期验收或完整送达闭环。
- 所有危险字段继续保持 false：`safe_to_control: false`、`delivery_success: false`、`primary_actions_enabled: false`、`robot_control_executed: false`。

## 验收证据

引用 engineer report：

- O6 `python3 -m py_compile ...remote_cloud_relay.py`：通过，无输出。
- O6 `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`：`Ran 149 tests in 50.772s`，`OK`。
- O7 `cd pc-tools/workstation && npm run test -- catalog.test.ts`：`Tests  204 passed (204)`。
- O7 `cd pc-tools/workstation && npm run test -- App.test.ts`：`Tests  247 passed (247)`。
- O7 `cd pc-tools/workstation && npm run build`：通过，Vite 仅既有 chunk warning。
- O7 `cd pc-tools/workstation && npm run lint`：通过。

Product closeout 轻量验证已通过：三个收口文件 `test -f` 均退出码 0；关键字段 `rg` 命中 `software_proof_local_mock_annotation_only`、`149 tests`、`204 passed`、`247 passed`、`O6`、`O7`、`safe_to_control: false`、`delivery_success: false`；`git diff --check` 退出码 0、无输出。

## 收口结论

本 sprint 验收通过，证据边界为 `software_proof_local_mock_annotation_only`。O6/O7 可以保守上调，但不得把任何 KR 标为完成或归档。

已更新或待本收口同步更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

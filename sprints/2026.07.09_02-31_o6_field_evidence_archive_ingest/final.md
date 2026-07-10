# O6 Field Evidence Archive Ingest Final

- sprint_type: epic
- close_time: 2026-07-09 05:25 Asia/Shanghai
- product_owner: product-okr-owner
- target_objectives: O6, O7
- evidence_boundary: software_proof_local_mock_archive_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false

## 用户价值和产品北极星

本轮把现场材料从“散落文件”推进到“可 ingest、可查询、可被 PC 主路径消费”的 O6/O7 数据链路。用户价值不是新增控制能力，而是让后续 `route.csv`、replay JSONL、keyframe、manifest 等现场证据可以进入统一 archive/read model，减少现场复盘和训练数据整理的断点。

产品北极星保持不变：让普通用户能把垃圾交给小车并可验证地完成投递。本 sprint 只补可观测和可复盘的数据底座，不声明真实送达、真实生产云或真实机器人动作闭环。

## OKR 映射和方向判断

方向判断：继续 O6/O7，但下一轮必须消费真实路线材料或生产 backing，不能继续只做 wrapper/surface。

- O6 从约 30% 保守上调到约 33%，本轮不再继续上抬。理由：新增 `POST /api/o6/archive/field-evidence`，O6 consumer list/detail 可回读 `field_evidence`，并覆盖 trajectory/events/evidence_refs 和危险字段 fail-closed。
- O7 从约 30% 保守上调到约 31%，本轮不再继续上抬。理由：PC/O7 adapter 能显示 O6 field evidence wrapper，`catalog.test.ts`、`App.test.ts`、build、lint 均通过；但还没有真实回放播放器、标注提交闭环或生产数据流。
- O5/O1/O2/O3/O4 不调整。本轮没有真实 TLS/4G/OSS/production DB、WAVE ROVER HIL、真实路线执行、电梯/送达或手机验收。

## KR 拆解和历史归档

- O6 KR2/KR3/KR6：从“已有 local/mock archive/read proof”推进到“field evidence manifest 可写入并由 consumer read 回读”。
- O7 KR3/KR4：从“缺云端回放/标注数据流”推进到“PC consumer read adapter 可消费 field evidence wrapper”；仍未完成路线逐帧回放、标注 UI 提交和导出训练集。
- 已完成 KR 历史归档：无。本轮只是推进子能力，不足以把 O6 或 O7 任一 KR 标为完成或移入历史区。

## 验收证据

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/scripts/field_route_evidence_manifest.py`：通过，退出码 0。
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`：147 tests OK。
- `cd pc-tools/workstation && npm run test -- catalog.test.ts`：201 passed。
- `cd pc-tools/workstation && npm run test -- App.test.ts`：247 passed。
- `cd pc-tools/workstation && npm run build`：passed，Vite 仅 chunk warning。
- `cd pc-tools/workstation && npm run lint`：passed。
- `git diff --check`：通过，无空白错误。

## 收口结论

本 sprint 验收通过，结论边界为 `software_proof_local_mock_archive_only`。O6 写入、O6 list/detail 回读、O7 wrapper 消费、安全字段关闭三段证据齐全；`side2side_check.md` 中的验收口径成立。

本轮核心抓手是“把现场证据接进 O6/O7 主数据链”，不是“新增控制或送达能力”。因此 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 继续保持。

## 责任 Engineer 和下一步

- `robot-software-engineer`：下一轮补真实 field artifact 到 seed 的可复现入口，优先消费 `route.csv`、replay JSONL、keyframe 或 rosbag。
- `full-stack-software-engineer`：把 O7 从 wrapper 展示推进到历史路线回放和标注工作台的最小可用闭环。
- `robot-algorithm-engineer`：提供可被 O6 ingest 的真实路线/定位/关键帧证据链，避免 O6/O7 继续用纯 mock fixture 自循环。

## 风险和缺口

- 真实生产 DB/queue、OSS/CDN、TLS/4G、真实隧道和真实机器人数据仍未接入。
- 本轮未复跑 cloud-relay Docker smoke，也未单独复跑 targeted local/mock HTTP smoke；新 endpoint 的写入/读回由 `test_remote_cloud_relay` 覆盖。
- `gate_pass=true` 仍不能解释为 `delivery_success`。
- O7 仍缺真实 RTC/视频、真实 ASR/TTS、真实 wheel raw 非零反馈、真实电梯/回放/标注数据流和完整路线长期验收。

## Sprint 文档

- 已补齐本文件作为 epic `final.md`。
- `OKR.md` 已更新 O6/O7 进度、主要缺口和最高优先级说明。
- `docs/process/okr_progress_log.md` 已记录本轮历史进度证据。

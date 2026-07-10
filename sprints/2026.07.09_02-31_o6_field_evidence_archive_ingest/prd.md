# O6 Field Evidence Archive Ingest PRD

## 用户价值

现场作业往往先拿到 `/route.csv`、`replay.jsonl`、关键帧截图、`trashbot.field_evidence_manifest.v1`，但这些材料长期停留在文件系统里，无法自然进入 O6/O7 的统一可观测链路。  
本轮目标是让这些现场材料“可被 ingest、可被查询、可被复用”，让 O6 的任务/事件证据能直接在 O7 主路径被消费者读取，作为后续真实路网与送达能力迭代的统一输入来源。

## OKR 映射

- O6 KR2：任务记录和感知事件持久化到云端数据库。当前阶段用 local/mock file-backed store 证明 schema 和查询链路。
- O6 KR3：大对象走 OSS，数据库只保留 `evidence_ref`。当前阶段只存 basename/安全引用，不保存图片、视频或 base64。
- O6 KR6：REST API 供 PC/手机消费历史任务、详情、轨迹数据、事件流、标注状态。
- O7 KR3：PC 历史路线回放从 O6 consumer read 主路径消费轨迹摘要。
- O7 KR4：PC 标注/打标界面从同一任务详情读取 evidence/labeling 状态。

## 本轮范围（范围内）

1. 在 O6 local/mock 证据链路中接收 `trashbot.field_evidence_manifest.v1`，并可选读取同目录 `route.csv`、`replay.jsonl`/其他离线轨迹片段；
2. 生成并写入 O6 task/trajectory/events/evidence_refs 的可查询读模型（不改写既有字段）；
3. O6 consumer detail 可回读 `field_evidence` 来源，`task_origin=field_evidence_manifest`，并保留安全门控元数据（如 `gate_pass`）；
4. O7 PC consumer detail 通过既有主路径可读取该任务，并展示现场证据摘要（而非实时控制/推送操作）；
5. 强制约束危险字段始终为 `false`：`safe_to_control`、`delivery_success`、`primary_actions_enabled`、`connects_cloud_production`、`robot_control_executed`。

## 范围外

- 不连接真实 production DB/queue、TLS 生产云、4G 外网链路，也不调用真实 OSS/CDN；
- 不连接串口、不发 `/cmd_vel`、不执行导航/送达行为；
- 不把现有 `gate_pass=true` 当作真实投递成功凭据；
- 不在本轮实现 PC 端新建任务、回放播放器、音频播放/发送、标注提交或生产部署脚本；
- 不改动 `/mobile`、`cloud-relay` 编排上线相关发布面，只同步与本 sprint 路径相干的文档与验证路径说明。

## 验收口径

1. 从本地 fixture 生成 `field_evidence_manifest` seed，并完成 O6 local/mock ingest（文件级或内存级）；
2. O6 consumer list/detail 可读回该任务并输出 `field_evidence` 源头字段；
3. O7 主路径（`consumer-read`）可读到同一个任务详情；
4. O6 与 O7 输出的任务能力状态中 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`（以及生产联网/实控相关字段均为 false）；
5. 单元/契约路径有回归：有效 manifest、缺失关键字段、unsafe 声明、非法输入均应 fail-closed；
6. 技术链路在现有 local/mock 条件下可复现，形成 `tech-done.md` 中可核验命令输出。

## Owner 分工

- `full-stack-software-engineer`（主责）：  
  - O6 local/mock archive 与 consumer read 主路径的接入协调，覆盖 `docs/product/` 与 `sprints/.../tech-done.md` 说明更新边界；
  - 主动同步主线验收状态，保持风险字段不变更。  
- `robot-software-engineer`（支持）：  
  - `trashbot.field_evidence_manifest.v1` 的解析与 seed 生成一致性，补齐 O6 侧字段映射、schema 验证和相关测试；
  - 提供可复用的输入输出示例给 O7 side 使用。  
- 该 PRD 为本 sprint 交付定义，不作代码实现。

## 风险边界

- 本 sprint 标记为 `software_proof_local_mock_archive_only`：可验证的是 “读写与查询链路正确性”，不等于生产可交付；
- 真实隧道、生产数据库/队列、真实证书/TLS、真实 4G、真实 OSS、真实机器人运行与现场路线闭环不在本轮范围内；
- 无法将 manifest 的 `gate_pass=true` 解释为 `delivery_success`，也不能解释为机器人已完成投递；
- 字段安全阈值需持续保持 fail-closed；若后续代码路径新增写入源，应纳入 schema 审核；
- 若出现兼容性差异（文件 schema 变化、事件字段新增），以 `tech-done.md` 记录修订并评估是否影响本 sprint 交付。

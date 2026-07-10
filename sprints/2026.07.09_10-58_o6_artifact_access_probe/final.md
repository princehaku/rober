# O6 Artifact Access Probe Final

- sprint_type: epic
- close_time: 2026-07-09 12:00 CST
- product_owner: product-okr-owner
- target_objective: O6 云端核心后端
- secondary_objective: O7 PC 端运营调试与数据训练平台
- evidence_boundary: software_proof_local_mock_artifact_access_probe_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 用户价值和产品北极星

本轮完成了 O6/O7 artifact access probe 的软件侧闭环：O6 不再只保存 artifact ref 字符串，而是在受限本地/mock allowlist root 内生成 `exists`、`size_bytes`、`sha256`、`detected_type`、`blocked_reason` 和 `proof_scope` 摘要；O7 能消费这些摘要并给运营/开发者展示可读的 readiness、blocked reasons 与 next evidence。

产品北极星仍是“普通用户把垃圾交给小车后，小车可验证地完成垃圾投递”。本轮只提升复盘数据可信度，不声明真实送达、真实生产云、真实媒体或机器人控制完成。

## OKR 映射和方向判断

方向判断：继续 O6/O7；不暂停、不替换、不归档 KR。

- O6 从约 39% 保守上调到约 42%。依据是 O6 已实现 `trashbot.o6.artifact_access_probe.v1`，支持 allowlist root 内小文件只读 probe、64KB 上限、sha256/type 摘要、blocked reason，并暴露到 archive detail、field_evidence、artifact_bundle、consumer detail 和 `include=artifact_access_probe`；验证为 `Ran 153 tests in 52.427s OK`、`py_compile` 和 `git diff --check` 通过。
- O7 从约 40% 保守上调到约 42%。依据是 PC/O7 consumer detail 已能读取 O6 `artifact_access_probe`，在 `artifact_bundle_readiness` 和 UI 展示 counts、basename refs、detected_type、size、sha256 prefix、blocked reasons 和 next evidence，并对缺失/unsafe/schema mismatch fail-closed；验证为 `npm run test` 通过 `3 passed` / `472 passed`，`npm run build`、`npm run lint` 和 `git diff --check` 通过。
- O6 KR2/KR3/KR6 与 O7 KR3/KR4 都只是软件侧推进，不标完成。

## KR 拆解、更新或历史归档

- O6 KR2：任务记录和感知事件现在可关联 artifact access 摘要，能区分安全可读小文件、缺失文件和 blocked refs。
- O6 KR3：继续只保存引用和安全摘要，不存原始大对象；sha256/size/type 只证明 allowlist root 内本地/mock 小文件可读，不证明 OSS 存档。
- O6 KR6：archive detail 与 consumer detail 可通过 `include=artifact_access_probe` 回读同一 `task_id` 的 probe。
- O7 KR3/KR4：PC 端从 readiness surface 继续推进到可读 artifact access probe 展示，但仍未完成真实历史路线回放和真实数据标注平台。
- 已完成 KR 历史归档：无。
- 历史记录位置：`docs/process/okr_progress_log.md` 新增 `2026-07-09 10-58｜o6_artifact_access_probe` 条目。

## 本轮核心抓手

核心抓手是“artifact ref 可访问性证据”：把本地/mock artifact ref 放入受限读取规则，用小文件 probe 证明可访问摘要和 blocked reason 都能通过 O6 archive/read 主路径传到 O7。

## 需要做什么

下一轮不要继续堆叠 local/mock wrapper 或 readiness surface。应直接补真实或离线 artifact seed smoke：

1. 由 `robot-algorithm-engineer` 或 `robot-software-engineer` 准备一个真实/离线 `route.csv`、replay JSONL、keyframe 或 rosbag，放入 allowlist root。
2. 由 `robot-software-engineer` 让 O6 对该 seed 生成 artifact access probe，并确认同一 `task_id` 的 archive/detail/consumer detail 回读。
3. 由 `full-stack-software-engineer` 验证 O7 主路径消费同一真实/离线 probe，展示文件摘要和 blocked reasons。

## 优先级和验收口径

当前最高优先级仍是现场 O3 验证 lane；O6/O7 并列为最低 active Objective，下一轮应让真实或离线 artifact seed 进入 O6/O7，而不是继续做只读 surface。

下一轮验收口径：

- 至少一个真实或离线 artifact seed 被 O6 在 allowlist root 内探测，产出 `exists=true`、`size_bytes`、`sha256` 和 `detected_type`。
- 至少一个危险或不可访问 ref 继续 blocked，并返回明确 `blocked_reason`。
- O7 消费同一 `task_id` 的 probe，不暴露绝对路径、token、URL query 或原始媒体内容。
- `safe_to_control: false`、`delivery_success: false`、`primary_actions_enabled: false`、`robot_control_executed: false` 继续保持 false，除非后续现场验收单独证明。

## 对应责任 Engineer

- `robot-software-engineer`：O6 archive/read model、artifact access probe、真实/离线 artifact seed 接入与 O6 验证。
- `full-stack-software-engineer`：O7 consumer detail、readiness/UI 展示与 fail-closed 验证。
- `robot-algorithm-engineer`：提供真实或离线 route.csv、replay JSONL、keyframe、rosbag 或路线材料，避免 O6/O7 在 mock 摘要层自循环。
- `product-okr-owner`：维护 OKR 进度、验收边界、KR 归档判断和历史记录。

## 风险、阻塞和证据链缺口

本轮证据边界明确为 `software_proof_local_mock_artifact_access_probe_only`。

不证明真实 OSS/CDN、production cloud、真实机器人数据、真实媒体访问、真实 annotation API、真实 dataset export、ROS2 runtime、机器人运动或 delivery success；也不证明生产 DB/queue、TLS/4G、公网隧道、真实 RTC/视频、真实 ASR/TTS、wheel raw 非零、真实电梯状态链或完整路线长期验收。

剩余最大产品风险：O6/O7 现在能证明“受限本地/mock 小文件可读”，但真实现场文件还没有进入 allowlist root 并跑完贯通 smoke。下一轮必须补这个证据，否则 O6/O7 会继续停留在软件合同层。

## 验收证据

引用 worker report：

- O6 `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`：通过，无输出。
- O6 `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`：首次失败后修复 blocked reason 判定顺序，复验 `Ran 153 tests in 52.427s`、`OK`。
- O7 `cd pc-tools/workstation && npm run test`：`Test Files  3 passed (3)`、`Tests  472 passed (472)`。
- O7 `cd pc-tools/workstation && npm run build`：首次 TypeScript `TS2783` 重复字段失败后修复，复验通过。
- O7 `cd pc-tools/workstation && npm run lint`：通过，无 ESLint 输出。
- `git diff --check`：通过，无输出。

Product closeout 轻量验证要求：本目录 `side2side_check.md`、`final.md` 存在；`rg` 可命中 `software_proof_local_mock_artifact_access_probe_only`、`153 tests`、`472 passed`、`O6`、`O7`、`safe_to_control: false`、`delivery_success: false` 和 `artifact_access_probe`；`git diff --check` 通过。

## 收口结论

本 sprint 验收通过。O6/O7 都可保守上调到约 42%，但本轮不归档任何 KR，不声明真实生产云、真实媒体、真实 annotation、真实 dataset、ROS2 runtime、机器人运动或 delivery success 已完成。

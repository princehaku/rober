# O7 Route Replay Labeling MVP Side-by-Side Check

- sprint_type: epic
- check_time: 2026-07-09 06:19 CST
- product_owner: product-okr-owner
- primary_engineer: full-stack-software-engineer
- target_objective: O7 PC 端运营调试与数据训练平台
- target_krs: O7 KR3 历史路线回放、O7 KR4 数据标注/打标界面
- evidence_boundary: software_proof_local_mock_consumer_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 用户价值和产品北极星

本轮用户价值是让 PC 工作站从“能看到 O6 field evidence wrapper”推进到“围绕同一个 `task_id` 查看历史路线回放摘要和标注草稿”。这让运营/开发者能基于 trajectory frames、events、evidence/keyframe refs、review item 和 label draft 判断一条任务材料是否可进入复盘或训练数据准备。

产品北极星保持不变：让普通用户把垃圾交给小车后，小车可验证地完成投递。本轮只补 PC 侧复盘和数据训练入口，不声明真实送达、真实控制、真实生产云或真实机器人运动。

## PRD / Tech Plan 对照

| 验收项 | 计划口径 | 实际证据 | 结论 |
| --- | --- | --- | --- |
| O6 consumer detail 主路径 | route replay 与 labeling 必须共用同一 `task_id` 和 detail 来源 | `O7FixturePreviewPanel` 优先消费 detail 派生的 `route_replay_mvp` 和 `labeling_mvp` | 通过 |
| O7 KR3 route replay MVP | 展示 frame count、current frame、pose/velocity、events、evidence/keyframe refs、本地 cursor | `tech-done.md` 记录 server contract、UI 和 `App.test.ts` 覆盖 frame cursor/keyframe refs | 通过 |
| O7 KR4 labeling MVP | 展示 review item、media/evidence ref、current/draft labels、schema、allowed types 和 fail-closed receipt | `tech-done.md` 记录 `labeling_mvp`、`submit_blocked_fail_closed`、draft/schema UI 覆盖 | 通过 |
| Debug fallback 边界 | 旧 archive fixture 只保留为 debug fallback，不能覆盖 consumer detail 主路径 | `tech-done.md` 明确旧 route/labeling 面板状态与 consumer detail 主路径隔离 | 通过 |
| 危险字段 | `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false` | `catalog.test.ts` 断言危险字段 false，合同固定 submit/control/success fail-closed | 通过 |
| 文档同步 | 更新 PC 工作站和 O7/O6 接口文档 | 已只读核对 `docs/product/pc_tools_workstation.md` 与 `docs/interfaces/o7_realtime_operator_console.md` 新增 MVP 字段和边界 | 通过 |

## 验收证据

本收口任务按要求不重新运行 full-stack 验收命令，只引用 `tech-done.md` 记录的结果：

- `cd pc-tools/workstation && npm run test -- catalog.test.ts`：通过，`Tests 201 passed (201)`。
- `cd pc-tools/workstation && npm run test -- App.test.ts`：通过，`Tests 247 passed (247)`。
- `cd pc-tools/workstation && npm run build`：通过，Vite 仅保留 chunk size warning。
- `cd pc-tools/workstation && npm run lint`：通过，`eslint .` 无报错。
- `git diff --check`：通过，无输出。

首次 `App.test.ts` 曾失败 1 个用例，根因是旧 fixture 没有 `route_replay_mvp` 时 optional chain 少一层。full-stack worker 已修复 fallback optional chain 并重跑 `App.test.ts` 到 247 passed。

## OKR 映射和方向判断

方向判断：继续 O7，但下一轮应优先把 route replay / labeling MVP 接到真实 field artifacts、真实媒体可访问性或 annotation submit/export 的最小闭环，不能再只堆叠 preview 文案。

- O7 可从约 31% 保守上调到约 34%。理由：本轮已经从 wrapper 兼容推进到 consumer detail 主路径的历史路线回放和标注 MVP，且有 test/build/lint/diff-check 证据。
- O7 KR3 不标完成。原因：还没有真实云端历史任务数据流、真实地图叠加、真实关键帧媒体可访问性、真实逐帧回放或长期路线验收。
- O7 KR4 不标完成。原因：真实 annotation submit、rollback、autosave、dataset export 和审计日志仍未接通。
- O6/O5/O1/O2/O3/O4 不调整。本轮只消费 O6 detail，不新增真实生产云、真实机器人数据、真实送达或硬件反馈证据。

## 责任 Engineer 和下一步

- `full-stack-software-engineer`：下一轮把 `labeling_mvp` 推进到真实 annotation submit/export 的 fail-open 前置验证，或补真实媒体/keyframe 可访问性 smoke。
- `robot-software-engineer`：提供可稳定进入 O6 consumer detail 的真实 route/replay/keyframe artifact seed。
- `robot-algorithm-engineer`：提供可复用的 route.csv、replay JSONL、keyframe 或 rosbag，让 O7 不再停留在 local/mock consumer。

## 风险和证据链缺口

- 证据边界仍是 `software_proof_local_mock_consumer_only`。
- 未证明真实生产云、真实 DB/queue、OSS/CDN、TLS/4G 或真实机器人数据。
- 未证明真实 RTC/视频、ASR/TTS、wheel raw 非零、电梯状态链、机器人运动或 delivery success。
- 未证明真实 annotation submit/export、真实关键帧媒体加载或完整路线长期验收。

## 验收结论

本 sprint 满足 PRD 和 tech-plan 的软件侧验收口径，可以收口。OKR 只做保守进度更新，不归档 O7 KR3/KR4，也不改变所有危险字段 false 的产品边界。

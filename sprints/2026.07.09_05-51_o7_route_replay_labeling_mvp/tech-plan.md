# O7 Route Replay Labeling MVP Tech Plan

## 目标

把 O7 从 O6 `field_evidence` wrapper 展示推进到历史路线回放与标注工作台最小可用闭环。实现必须可消费 O6 consumer detail 或等价本地 mock，并至少提供：

- `task_id`
- trajectory frames
- events / evidence_refs
- label drafts
- submit receipt 或 fail-closed 状态

本轮不连接真实机器人、真实生产云、真实 4G、OSS/CDN 或真实摄像头。

## 技术方案

1. Server contract：
   - 在 O7 consumer detail 主路径上派生 route replay MVP 摘要。
   - 在同一 detail 上派生 labeling draft / queue / receipt fail-closed 摘要。
   - 复用或扩展 `o7RouteReplayPreview.ts`、`o7LabelingPreview.ts` 的白名单、限量采样和危险字段扫描逻辑。
   - 输入缺失、schema mismatch、危险 true 字段、submit/control/success claim 时必须返回完整 fail-closed contract。
2. Shared contract：
   - 在 `contracts.ts` 增加或收紧 route replay / labeling MVP 的响应类型。
   - 明确固定 false 字段：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
3. Client API：
   - 在 `workstationApi.ts` 暴露消费 consumer detail 的 route replay / labeling MVP 读取方法，或扩展现有 O7 consumer detail client。
   - Vue 组件不得直接拼 URL，不读取本地路径，不跨域访问上位机 Robot API。
4. UI：
   - 主入口选择 `O7FixturePreviewPanel.vue`，因为现有产品边界已定义 O6 consumer read、route replay 和 labeling queue 主路径在该组件内。
   - `TrainingLabelingPanel.vue` 只在实现发现必须复用通用本地 training/labeling 资产展示时做最小必要改动；默认不作为主入口。
   - UI 提供 task selector、route frame cursor、events/evidence refs、label draft/status 或 fail-closed receipt。
   - Play/Pause/Previous/Next/Reset 或等价 cursor 操作只能改浏览器/PC 本地状态，不调用 API 写入、不发送命令。
5. 文档：
   - 更新 PC 工作站产品边界和 O7/O6 接口文档，写清 consumer detail route replay / labeling MVP 的字段、fail-closed 约束和 proof boundary。
   - 更新本 sprint `tech-done.md`，记录实际改动、验证结果、偏差和风险。

## 文件范围

本 planning 子任务只允许创建/修改：

- `sprints/2026.07.09_05-51_o7_route_replay_labeling_mvp/pre_start.md`
- `sprints/2026.07.09_05-51_o7_route_replay_labeling_mvp/prd.md`
- `sprints/2026.07.09_05-51_o7_route_replay_labeling_mvp/tech-plan.md`

后续 full-stack owner 推荐实现范围：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/o7RouteReplayPreview.ts`
- `pc-tools/workstation/src/server/o7LabelingPreview.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_realtime_operator_console.md`
- `sprints/2026.07.09_05-51_o7_route_replay_labeling_mvp/tech-done.md`

若实现时发现 `TrainingLabelingPanel.vue` 已承载唯一可复用的标注草稿 UI，可替换或追加该文件，但必须保持范围最小，并在 `tech-done.md` 说明原因。

## 接口影响

- O7 PC API 可以新增 route replay / labeling MVP 的只读摘要字段或 endpoint，但必须保持本机回环和 fail-closed 限制。
- O7 consumer read adapter 继续只允许本机 HTTP 回环 `baseUrl`，拒绝非 HTTP、非回环、credentials、query/hash、空 task id、schema mismatch、fetch 失败、非 object 响应和危险 true 字段。
- 对 O6 consumer detail 的读取应继续使用：
  - list：`GET /api/o6/consumer/tasks?view=summary&limit=50`
  - detail：`GET /api/o6/consumer/tasks/<task_id>?view=default&include=trajectory,events,evidence,field_evidence,labeling,inference,tunnel`
- route replay 输出只能展示轨迹、事件、证据引用和本地 cursor；不得声明真实 playback available、真实机器人运动或 route execution success。
- labeling 输出只能展示 review/draft/status 或 fail-closed receipt；不得声明真实 annotation API、submit success、rollback success 或 dataset export available。
- 必须保持：
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`
  - `connects_cloud_production=false`
  - `real_cloud_archive_connected=false`，除非后续有生产云证据，本 sprint 不允许打开。

## 验收命令

后续 full-stack 子 agent 必须运行并记录结果：

```bash
cd pc-tools/workstation && npm run test -- catalog.test.ts
cd pc-tools/workstation && npm run test -- App.test.ts
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
git diff --check
```

如果任一命令失败，full-stack owner 必须先定位根因、修复并重新验证；不能把第一轮失败直接作为收口结果。

## OKR 最低优先级核对

当前 `OKR.md` 4.1 节未归档 Objective 完成度：

- O7：约 31%
- O6：约 33%
- O5：约 80%
- O1：约 85%

当前最低进度 Objective：O7。

本 sprint 是否针对该最低 Objective：是，直接针对 O7。

理由：上一轮已经证明 O6 field evidence wrapper 可被 O7 consumer adapter 读取，但 O7 仍缺 KR3 历史路线回放和 KR4 标注/打标界面最小闭环。本 sprint 将 O7 从 wrapper 展示推进到可围绕 `task_id` 消费 trajectory/events/evidence_refs/label drafts 的 PC 工作台，不依赖真实硬件、真实摄像头、真实 4G、OSS/CDN 或生产云。

`final.md` 收口时必须回顾：是否真的产出 route replay / labeling MVP contract 与 UI 证据；是否只是新增 wrapper 文案；是否仍保持所有危险控制和成功字段 false。

## 风险边界

- 本 sprint 目标是 `software_proof_local_mock_consumer_only` 或更强的软件侧 consumer proof，不等于真实生产云、真实送达、真实视频、真实电梯或真实机器人控制。
- `submit receipt` 可以是 fail-closed receipt；没有真实 annotation API 时不得显示提交成功。
- route replay cursor 只是本地浏览器/PC 状态，不得调用机器人控制、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 如果 O6 detail fixture 缺 trajectory/events/evidence/labeling 字段，必须显示具体 blocker，不得用空数组冒充可回放或可标注。
- 代码技术注释必须使用中文，并保持有意义注释比例超过 20%；既有注释规范不能因本轮 TypeScript/Vue 改动退化。
- 文档必须同步更新 `docs/product/pc_tools_workstation.md` 和 O7/O6 接口文档；否则不满足项目文档同步要求。

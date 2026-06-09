# O7 PC Consumer Read Integration Tech Done

## sprint_type

sprint_type: epic

## 实际改动

1. `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
   - 新增 O7→O6 consumer read workstation adapter。
   - 列表主路径固定请求 `GET /api/o6/consumer/tasks?view=summary&limit=50`。
   - 详情主路径固定请求 `GET /api/o6/consumer/tasks/<task_id>?view=default&include=trajectory,events,evidence,labeling,inference,tunnel`。
   - 仅允许本机回环 `http://127.0.0.1|localhost|::1`，并对危险 true 字段做 fail-closed。
2. `pc-tools/workstation/src/server/index.ts`
   - 挂载 `/api/o7/consumer-read/tasks` 与 `/api/o7/consumer-read/tasks/:taskId`。
3. `pc-tools/workstation/src/client/workstationApi.ts`
   - 新增 consumer read list/detail client。
4. `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
   - 新增 `O7 consumer read primary path` 区块。
   - 显示 list/detail query strategy、fail-closed boundary、样本计数和 tunnel temporal alignment。
   - 旧 `Cloud Archive Tasks` 区块保留为 secondary path fixture 预览。
5. `pc-tools/workstation/src/shared/contracts.ts`
   - 新增 O7 consumer read list/detail adapter contract。
6. `pc-tools/workstation/test/App.test.ts`
   - 覆盖 O7 预览页新 list/detail 主路径请求与展示。
7. `pc-tools/workstation/test/catalog.test.ts`
   - 覆盖 adapter builder 与 HTTP endpoint。
8. `docs/product/pc_tools_workstation.md`
   - 同步 O7 consumer read primary path 规则和 software proof 边界。

## 验证结果

### 命令

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
git diff --check
git status --short --branch
```

### 结果摘要

- `npm run build`：通过；Vite 产物输出 `dist/assets/index-C_QjU-TX.js`。
- `npm run test`：通过；`2 passed (2)`、`42 passed (42)`。
- `npm run lint`：通过。
- `git diff --check`：通过。
- `git status --short --branch`：仅剩本 sprint 允许范围内改动与新增 adapter 文件。

## 失败定位与修复

1. 本地缺依赖导致 `tsc/vitest/eslint: command not found`
   - 处理：在 `pc-tools/workstation` 执行 `npm install`，随后重跑验收命令。
2. Vue 模板把 `??` 与 `||` 混用导致解析失败
   - 处理：为 `requested_task_id` 回退表达式补括号。
3. 测试桩未匹配 URL-encoded `include=` 详情请求
   - 处理：将 consumer detail mock 改为 `startsWith(...)`。
4. O7 预览页测试依赖 input 索引，新增字段后脆弱失效
   - 处理：改为按 `aria-label` 定位输入。

## software proof 边界

- 本轮仅证明 PC workstation 已把 O7 任务列表/详情主入口切到 O6 consumer read contract。
- 仍固定 `safe_to_control=false`、`connects_cloud_production=false`、`robot_control_executed=false`。
- 不声明真实云 DB、真实 OSS、真实 4G、真实 robot control、真实 delivery success。

## 剩余风险

1. 当前 consumer read adapter 只接受本机回环 relay，不覆盖公网或生产云环境。
2. detail 端当前展示的是限量样本摘要，不是完整 route replay/labeling/voice/command 真实运行态。
3. 真实 O6 relay contract 若后续字段名漂移，需同步更新 workstation adapter 与测试。

# PC Hardware HIL Material Coverage Tech Plan

## 1. Sprint 和执行策略

- sprint_type: epic
- sprint_id: `2026.05.26_06-07_pc-hardware-hil-material-coverage`
- 执行模式：2 个并行子 agent + Product closeout
- 主责实现：`full-stack-software-engineer`
- 事实咨询：`robot-hardware-engineer`
- Product 收口：`product-okr-owner`

本计划完成后默认进入实现阶段。主节点不得直接写产品代码、测试代码、硬件配置或运行实现测试；必须派发对应 worker。

## 2. 文件范围

### Product 当前已允许修改

- `sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/pre_start.md`
- `sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/prd.md`
- `sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/tech-plan.md`

### Full-Stack 后续允许修改

- `pc-tools/workstation/src/server/**`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/**`
- `pc-tools/workstation/src/App.vue`
- `pc-tools/workstation/src/styles.css`
- `pc-tools/workstation/test/**`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/evidence/README.md`
- 本 sprint 的 `tech-done.md`

### Hardware 后续只读范围

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/**`
- `pc-tools/evidence/fixtures/wave_rover_*`

Hardware 咨询默认不改文件；如必须补硬件文档，需 Product 另行确认范围。

### 禁止修改

- 不修改真实硬件配置、launch 默认、ROS2 控制链路、固件、factory firmware。
- 不恢复 `pc-tools` 旧 Python evidence gate，不新增 `pc-tools/**/*.py`。
- 不修改 `.idea/rober.iml`。
- Product plan 阶段不修改 `OKR.md`、`docs/`、`mobile/`、`pc-tools/`。

## 3. 接口影响

预期新增或扩展本地 PC API：

- 建议新增：`GET /api/hardware/wave-rover/material-coverage`
- 响应必须包含：
  - `source: "software_proof"`
  - `proof_status: "not_proven"`
  - `safe_to_control: false`
  - `delivery_success: false`
  - `primary_actions_enabled: false`
  - `pc_only: true`
  - `fixture_root`
  - `fixture_groups`
  - `required_materials`
  - `coverage_summary`
  - `gaps`
  - `not_proven_boundaries`

字段语义：

- `fixture_groups`：从 `pc-tools/evidence/fixtures/wave_rover_*` 扫描出来的组，包含文件列表、解析状态和分类。
- `required_materials`：required material item 列表，五件套必须精确包含 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report`；execution pack、review decision 只能作为辅助上下文，不替代五件套。
- `coverage_summary`：只统计本地材料覆盖，不输出真实 HIL pass。
- `gaps`：给 Hardware 下一步补材料使用。
- `not_proven_boundaries`：固定说明本轮不证明真机、UART、HIL、LiDAR/ToF、delivery success 或 PR #5 resolved。

UI 入口：

- 可以扩展 Evidence Tools，也可以新增 Hardware HIL Material Coverage panel。
- 不允许出现 Start、Control、Run HIL、Connect Serial、Mark Passed 这类控制/伪验收动作。

## 4. 任务拆分

### Task A：Hardware 只读事实咨询

Owner：`robot-hardware-engineer`

输入：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `pc-tools/evidence/fixtures/wave_rover_*`

输出要求：

1. 已读 vendor 来源。
2. WAVE ROVER/HIL material coverage required item 建议清单。
3. 哪些材料只能说明 software proof，哪些必须保留 `not_proven`。
4. 不足材料和 reviewer follow-up 建议。

验收命令：

```bash
test -f docs/vendor/VENDOR_INDEX.md
find pc-tools/evidence/fixtures -maxdepth 2 -type d -name 'wave_rover_*' -print | sort
find pc-tools/evidence/fixtures -maxdepth 4 -type f -path '*wave_rover_*' -print | sort
```

### Task B：Full-Stack Node/Vue 实现

Owner：`full-stack-software-engineer`

实现要求：

1. 在 `pc-tools/workstation` 中实现 Node/Vue 工作站内的 Node-native scanner，不执行 Python，不调用真实串口。
2. 定义 coverage contract，保持 fail-closed flags。
3. 新增/扩展 API，扫描 `pc-tools/evidence/fixtures/wave_rover_*`。
4. 在 Vue UI 展示 coverage、缺口、fixture group 和 `not_proven` 边界。
5. 补 Vitest 测试，覆盖 scanner/API/UI 文案。
6. 更新 `docs/product/pc_tools_workstation.md` 和 `pc-tools/evidence/README.md`。
7. 在本 sprint `tech-done.md` 写实际改动、验证结果和剩余风险。

建议文件：

- `pc-tools/workstation/src/server/waveRoverMaterialCoverage.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/EvidenceToolsPanel.vue`
- 或新增 `pc-tools/workstation/src/components/WaveRoverMaterialCoveragePanel.vue`
- `pc-tools/workstation/test/waveRoverMaterialCoverage.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/evidence/README.md`
- `sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/tech-done.md`

验收命令：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
find pc-tools -path 'pc-tools/workstation/node_modules' -prune -o -type f -name '*.py' -print
git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md pc-tools/evidence/README.md sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage
```

预期：

- build/test/lint 全部通过。
- `find ... '*.py'` 不输出任何 `pc-tools` 旧 Python 文件。
- UI/API 文案固定保留 `not_proven`、`safe_to_control=false`、`delivery_success=false`。

### Task C：Product Closeout

Owner：`product-okr-owner`

在 Task A/B 返回后执行：

1. 核对改动文件是否在允许范围。
2. 核对 worker 验证日志和失败定位。
3. 核对是否更新 `docs/product/pc_tools_workstation.md` 或 `pc-tools/evidence/README.md`。
4. 核对新增代码技术注释是否中文且比例超过 20%。
5. 更新 `side2side_check.md`、`final.md` 和 `OKR.md`，但只在实现证据足够时调整 Objective 1 进度。
6. 汇总剩余风险，不能把“缺真实硬件材料”作为唯一最终结论；必须列出可执行补齐清单。

Product 验收命令：

```bash
test -f sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/tech-done.md
test -f sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/side2side_check.md
test -f sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/final.md
rg -n "wave_rover|Node-native|not_proven|safe_to_control=false|delivery_success=false|Python gate" pc-tools/workstation docs/product/pc_tools_workstation.md pc-tools/evidence/README.md sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage
git diff --check -- OKR.md sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage docs/product/pc_tools_workstation.md pc-tools/evidence/README.md
```

## 5. 并行启动要求

本 sprint 跨 Full-Stack 和 Hardware 两个 owner，文件范围互不重叠：

- Hardware：只读 vendor/source 和 fixture，输出事实咨询。
- Full-Stack：写 Node/Vue 工作站代码、测试、文档。

因此实现阶段必须并行启动 2 个 worker，不序列化等待。Product 不参与代码实现，只做 closeout。

## 6. 风险边界

- 本轮只证明 PC 工作站能扫描和展示本地材料 coverage，不证明真实 HIL。
- `wave_rover_*` fixture 可能包含 pass 目录，但 UI/API 不得把它升级为真实硬件 pass。
- 如果 Full-Stack 需要硬件 required item 名称，必须使用 Hardware 咨询输出；不得基于文件名硬猜硬件事实。
- 若 `npm run build/test/lint` 失败，worker 必须先定位并修复后重跑，不把第一轮失败直接交差。
- 如果 Docker/ROS2/HIL 未运行，final 必须明确这不影响 PC 工作站软件 gate，但仍是 Objective 1 实机证据缺口。

## 7. OKR 最低优先级核对

当前 `OKR.md` 4.1 快照中，按数值最低 Objective 是 Objective 5 约 76%；Objective 1 约 81%，Objective 2/3/4 约 99%。

本 sprint 不针对全局最低 Objective 5，原因是 CEO 本轮明确要求重心推进 Objective 1 的可执行功能证据链，并且最近多轮 Objective 1 已反复消费“缺真实 WAVE ROVER/UART/HIL/2D LiDAR/ToF/PR #5 材料” blocker。本轮将该 blocker 改造成 PC 工作站可扫描、可展示、可复核的 material coverage 能力，避免继续空转。

本 sprint 针对 Objective 1：打通官方硬件协议、建立可信底盘控制层。交付物若通过验证，应只提升 Objective 1 的材料可执行性，不得宣称真实 WAVE ROVER/UART/HIL pass。

## 8. 本轮文档级验证命令

Product plan 阶段只运行以下文档级验证：

```bash
test -f sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/pre_start.md
test -f sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/prd.md
test -f sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/tech-plan.md
rg -n "OKR 最低优先级核对|Objective 1|pc-tools/workstation|wave_rover|Node/Vue|Full-Stack|Hardware" sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage
```

## 9. 自检

- 计划覆盖用户要求的 Node-native、WAVE ROVER HIL/material coverage、required materials、缺口和 `not_proven` 边界。
- 计划明确不恢复旧 Python evidence gate。
- 计划明确 Full-Stack 实现、Hardware 事实咨询、Product closeout/OKR/sprint 文档。
- 计划明确接口影响、文件范围、验收命令、风险边界和 OKR 最低优先级核对。

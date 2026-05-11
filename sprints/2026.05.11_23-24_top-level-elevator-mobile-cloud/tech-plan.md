# Sprint 2026.05.11 23-24 Top-Level Elevator/Mobile/Cloud Redesign - Tech Plan

## 角色与单线闭环

本轮 CEO 明确"顶层设计，无需多个子 agent 干活"。因此主节点以 `product-okr-owner` 视角单线闭环；不分派子 agent。所有改动严格限制在产品/OKR/产品文档/环境占位文件范围内，**不进入 `src/`、`docs/vendor/`、`docs/hardware/`、`docs/interfaces/`、`docs/acceptance/`、`docs/navigation/`、`docs/vision/`、`docs/superpowers/`、`README.md` 与其他 sprint 目录**。

## 任务拆解

### Task A：OKR.md 顶层段落升级

- 北极星补"跨楼层送垃圾必须做"，移除"H2/高阶场景可以纳入"措辞。
- 战略定位第 4 条"电梯能力是 assisted delivery"改为 MVP 必须能力，保留"小车不按按钮、不改造电梯、人工协助是流程边界"。
- Objective 2 KR6 去掉"H2/受控场景"，写为 MVP 必须。
- Objective 4 KR6 去掉"H2/受控场景"，写为 MVP 必须。
- Objective 5 KR6 去掉"H2/受控场景"，写为 MVP 必须。
- Objective 5 新增 KR7：手机端 UI 美观且能直接使用（视觉、可读、可适配、3 步内主操作、无 ROS topic 暴露）。
- 新增 Objective 6：4G 云通信链路 + OSS/CDN 数据中转产品化，6 个 KR。
- 第 5 节 H2 路线把"阶段 E：电梯 assisted delivery 受控场景"改写为 MVP 阶段，保留"受控场景验证"用语。
- 风险表新增凭证管理与云依赖风险。
- 第 9 节"下一步执行建议"补 4G 云中转服务端、OSS/CDN、手机美观 UI、电梯子状态机入主链路。
- 最后追加新进度快照 "29. 本轮产品方向快照（2026-05-11 23:59）"，明确：本轮只升级方向，不抬实机完成度。

### Task B：docs/product/elevator_assisted_delivery.md 全文重写

- 顶部状态：阶段从 `H2 / 受控场景产品方向` 改为 `MVP / 必须实现，先在受控场景验证`。
- 用户价值段保留低成本和不机械臂边界。
- 状态机部分维持 7 个子状态，但写明这些子状态必须进入主 `task_orchestrator`，不是默认关闭的可选分支。
- 识别要求保留 P0/P1；明确 P0 为 MVP 必交付，P1 为后续增强。
- 验收口径仍为三层（文档合同 / 软件 dry-run / 受控实景），但写明三层均为 MVP 验收路径，不再是可跳过的 H2 拓展。
- "不做什么"保留人工协助边界。

### Task C：docs/product/mobile_user_flow.md 升级

- 新增"Phone UI Quality Bar"段：把"美观、能直接使用、中文优先、3 步内主操作、不暴露 ROS 名"列为产品硬要求。
- 把现有的 "API-first local HTTP service plus a minimal browser page" 段补充：本地 phone-first HTML 仅作 fallback；正式手机入口必须满足 `docs/product/mobile_ui_quality.md` 验收口径。
- 状态表保留，但顶部加一行说明：所有 phone copy 必须有中文文案；speaker prompt 与之保持对应。
- 4G 段引用 `docs/product/remote_4g_mvp.md` 与新增 `docs/product/cloud_4g_infrastructure.md`，说明真实云中转链路。

### Task D：docs/product/remote_4g_mvp.md 升级

- 加一段"Cloud Hosting Baseline"：服务端为 4C 8G 无 GPU，公网入口；运维通过 SSH 端口 7878 管理（不写密码或私钥）。
- 强调小车永远 outbound，cloud 永远做命令/状态/ACK 中转。
- 加"Asset Channel"段：图片/快照/任务记录走 OSS + CDN，云中转 API 只承担 JSON 控制面，不承担大文件下载。
- 加"Secret Management"段：bearer token、OSS AK/SK 全部走 `.env` / 环境变量；任何 tracked 文件不得包含真实密钥。

### Task E：新增 docs/product/cloud_4g_infrastructure.md

- 章节：状态、用户价值、服务端基线（4C 8G 无 GPU、SSH 端口、网络方向、防火墙建议）、OSS contract、CDN contract、凭证管理 contract、失败降级。
- OSS / CDN 占位：bucket 名 `bytegallop`、region `oss-cn-hangzhou`、CDN base URL `https://cdn.bytegallop.com/rober/`、对象前缀 `rober/<robot_id>/<date>/<task_id>/`。
- 凭证以 `${OSS_ACCESS_KEY_ID}` / `${OSS_ACCESS_KEY_SECRET}` 占位形式给出，**绝不写真实 secret**。
- 责任 Engineer：`full-stack-software-engineer` 主责云中转、OSS/CDN 接入；`robot-software-engineer` 配合接行为/diagnostics；`hardware-engineer` 仅 SIM/调制解调器/天线时介入。

### Task F：新增 docs/product/mobile_ui_quality.md

- 验收口径：视觉系统（配色 token、字体、间距、卡片、按钮态）、信息架构（首页主操作、二级状态、诊断入口）、文案口径（中文优先、人话）、可访问性（对比度、可点击区域、字号下限）、性能（首屏可交互 < 3 秒，常驻刷新不卡顿）。
- 明确"美观"不是主观品味，给出 5 条可验证 checklist。

### Task G：环境隔离

- 新增 `.env.example`：`OSS_ACCESS_KEY_ID=`、`OSS_ACCESS_KEY_SECRET=`、`OSS_BUCKET=bytegallop`、`OSS_REGION=oss-cn-hangzhou`、`CDN_BASE_URL=https://cdn.bytegallop.com/rober/`、`REMOTE_CLOUD_BASE_URL=`、`REMOTE_BEARER_TOKEN=`。**只放空值或公开值，不放真实 secret**。
- 更新 `.gitignore` 追加 `.env`。

## 接口影响

- **不改 ROS2 接口、行为状态、launch 参数、硬件协议**。
- 文档接口（OKR/产品 contract）影响：
  - 行为状态机后续要把电梯子状态纳入主链路 → 由 `robot-software-engineer` 在下一个 sprint 落地。
  - 感知 contract 后续要新增电梯门/楼层/驶出证据字段 → 由 `autonomy-engineer` 在下一个 sprint 落地。
  - 手机端 UI 重构 + 4G 云中转客户端 → 由 `full-stack-software-engineer` 在后续 sprint 落地。

## 风险与边界

1. 顶层方向变更可能被外部误读为"已实现"。所有改动文档与 OKR 快照必须明确"本轮只升级方向，不抬实机完成度"。
2. CEO prompt 中给出的 OSS_ACCESS_KEY_SECRET 必须在所有 tracked 文件中以占位形式存在。`final.md` 验收时执行 grep 校验。
3. `.env` 必须进入 `.gitignore`，本轮不创建实际 `.env` 文件。
4. 服务端 SSH 凭证（root 密码）不写入任何文件，仅由运维通过私钥/密码管理器持有。

## 验证计划

1. 文档存在性 + 关键词覆盖：
   - `OKR.md` 含 `Objective 6`、`电梯`、`MVP 必须`、`手机美观`、`OSS`、`CDN`。
   - `docs/product/elevator_assisted_delivery.md` 含 `MVP`、不再以 `H2 / 受控场景产品方向` 作为阶段。
   - `docs/product/mobile_user_flow.md` 含 `美观` 或 `Phone UI Quality Bar`。
   - `docs/product/remote_4g_mvp.md` 含 `14.103.37.144`、`Asset Channel`。
   - `docs/product/cloud_4g_infrastructure.md` 含 `bytegallop`、`cdn.bytegallop.com`、`4C 8G`、`OSS_ACCESS_KEY_ID`（占位形式）。
   - `docs/product/mobile_ui_quality.md` 含 `验收`、`44pt` 或 `44px`、`中文`。
   - `.env.example` 含 `OSS_ACCESS_KEY_ID=`、`CDN_BASE_URL=`。
   - `.gitignore` 含 `.env`。
2. 敏感字符串校验：`rg -n ""` 必须无结果（仅在临时调研中存在于本 sprint 文档之外）。
3. scoped `git diff --check` 通过：
   - 范围：上述允许改动文件。
4. Sprint 六件套存在：`pre_start.md`、`prd.md`、`tech-plan.md`、`tech-done.md`、`side2side_check.md`、`final.md`。
5. 不跑构建、不跑测试、不连服务端（本轮不写代码、不部署）。

## 验收命令

- `rg -n "Objective 6" OKR.md`
- `rg -n "MVP 必须" OKR.md`
- `rg -n "bytegallop" docs/product/cloud_4g_infrastructure.md`
- `rg -n "14.103.37.144" docs/product/remote_4g_mvp.md`
- `rg -n "" .` 必须无结果
- `rg -n "^\.env$" .gitignore`
- `git diff --check -- OKR.md docs/product/elevator_assisted_delivery.md docs/product/mobile_user_flow.md docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md docs/product/mobile_ui_quality.md .env.example .gitignore sprints/2026.05.11_23-24_top-level-elevator-mobile-cloud/`

## 输出要求

- `tech-done.md`：列实际改动、验证结果、密钥隔离结果、剩余风险。
- `side2side_check.md`：对照 prd.md 验收口径逐条核对。
- `final.md`：复盘、OKR 进度判断、技术遗留。

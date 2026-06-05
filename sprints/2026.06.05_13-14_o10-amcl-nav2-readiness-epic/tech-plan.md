# Tech Plan: O10 AMCL/Nav2 Readiness Epic

## sprint_type

sprint_type: epic

## 计划状态

- Product plan：ready for L2 engineer dispatch
- Product owner：`product-okr-owner`
- 代码执行：必须由一线 Engineer 子 agent 执行，Product 不写产品代码、测试代码或硬件配置。
- 本轮主目标：产生 O10 下一段 readiness 材料，而不是重复 latest/readback/status。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的 Objective：O10 受控送达闭环实战，约 7%。
2. 本 sprint 是否针对该最低 Objective：是。
3. 判断理由：12-13 已完成 `KR-O10-Path-Contract-Lock`，但 O10 仍缺 AMCL/Nav2 readiness、PC 浏览器按钮级 workflow、真实/受控电梯图片 eval、stop-first HIL 决策门和 delivery-readiness chain。本轮直接推进 O10 的下一段链式证据，不重复消费已完成的 latest JSON path/readback/status。

## 总体验收边界

本轮所有 owner 必须保留不可外推边界：

- 不证明真实送达、真实跨楼层、真实手机验收、production cloud、PC WASD、HIL pass、robot ACK、continuous radar ready 或 `safe_to_control=true`。
- no-motion 任务必须保持 `safe_to_control=false`、`sends_base_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`。
- 任何硬件、UART、波特率、JSON 指令、反馈协议或现场运动材料必须再次读取 `docs/vendor/VENDOR_INDEX.md` 及其指向 vendor 文件。

## Owner 任务 1：AMCL/Nav2 Readiness

### Owner

- 主责：Robot Algorithm Engineer
- 协作：Robot Software Engineer

### 文件范围

允许 owner 根据实际代码位置在以下范围内改动，范围外需先回报 Product：

- `onboard/src/ros2_trashbot_nav/**`
- `onboard/src/ros2_trashbot_bringup/**`
- `onboard/src/ros2_trashbot_behavior/**`
- `onboard/scripts/**`
- `docs/` 中与 Nav2、map lifecycle、fixed route、readiness 相关文档
- `sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/tech-done.md`

禁止：

- 发布 `/cmd_vel`
- 调用 `/api/base/manual`
- 修改上一轮 12-13 sprint 文件
- 修改 `OKR.md`

### 实现目标

1. 从 canonical latest JSON `/root/rober/onboard/runtime/map_lifecycle_latest.json` 读取 map artifact 指向，确认 map artifacts 位于 `/root/rober/onboard/runtime/maps`。
2. 建立同一 `map` frame waypoint manifest 或 fixed-route dry-run 输入。
3. 增加或复用 map quality gate，输出 resolution、width/height、origin、occupied/free/unknown 概览、route waypoint frame 一致性和失败原因。
4. 在 no-motion 边界内验证 AMCL/Nav2 lifecycle、`/initialpose`、map server、planner/controller 或 fixed-route dry-run readiness。
5. 输出 `robot_runtime_material` 或 `blocked_with_root_cause`，不得写成地图可导航。

### 验收命令

Engineer 必须按实际实现补充精确命令，至少包含：

```bash
bash onboard/scripts/docker_humble_build.sh
```

如 Docker/Humble 环境不可用，必须给出替代最小验证：

```bash
python3 -m compileall -q onboard/scripts onboard/src
python3 -m unittest discover -s onboard/scripts -p 'test_*.py'
python3 -m unittest discover -s onboard/src -p 'test_*.py'
```

如果远端 upper API 可用，补充 no-motion runtime 验收：

```bash
curl -sS -X POST http://192.168.1.11:8787/api/map/proof/refresh
curl -sS http://192.168.1.11:8787/api/map/proof/latest
```

### 通过标准

- `tech-done.md` 写明 map artifact、waypoint manifest、AMCL/Nav2 readiness 状态、root cause、evidence type。
- 无 `/cmd_vel`、无 base manual、无 HIL claim。
- 如果失败，必须定位到 map artifact、frame、waypoint、lifecycle、package dependency 或 remote runtime 中的具体根因。

## Owner 任务 2：PC Browser Button Workflow

### Owner

- 主责：Full-stack Software Engineer

### 文件范围

- `pc-tools/workstation/**`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_direct_upper_pc_api.md`
- `docs/interfaces/o7_live_operator_panel.md`
- `sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/tech-done.md`

禁止：

- 扩大 UI 成新功能大改版
- 写成真实 PC WASD、真实控车或 HIL pass
- 修改上一轮 12-13 sprint 文件
- 修改 `OKR.md`

### 实现目标

1. 浏览器按钮级触发 scan proof refresh、map proof latest、map/localize control readback 中至少两个关键入口。
2. UI 必须展示 canonical path、hz、TF、fallback、artifact status、failure reason、safe/fail-closed 字段。
3. 失败时展示 upper path、HTTP status、adapter/source 或 not_proven reason。
4. 产出 Playwright、浏览器日志或截图材料，证明不是 curl-only。

### 验收命令

```bash
cd pc-tools/workstation
npm test
npm run build
TMPDIR=/tmp PORT=8788 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api
```

另起 shell 或由测试脚本执行：

```bash
curl -sS http://127.0.0.1:8788/api/o7/direct-upper/status
curl -sS http://127.0.0.1:8788/api/o7/direct-upper/radar/scan-proof/latest
curl -sS http://127.0.0.1:8788/api/o7/direct-upper/map/proof/latest
```

如果已有 Playwright 脚本，必须运行对应 browser workflow 测试；如果没有，必须补最小 browser/manual 证据并在 `tech-done.md` 说明截图或日志路径。

### 通过标准

- 至少一条浏览器按钮级 workflow 证据成立。
- UI/API fail-closed 字段清楚展示。
- 未把 HTTP 200 或按钮点击写成 `safe_to_control=true`、PC WASD、HIL 或 delivery success。

## Owner 任务 3：Elevator Image Eval

### Owner

- 主责：Robot Algorithm Engineer

### 文件范围

- `onboard/src/ros2_trashbot_behavior/**`
- `onboard/src/ros2_trashbot_nav/**`
- `pc-tools/evidence/**`
- `docs/product/elevator_assisted_delivery.md`
- `docs/` 中与 elevator field/eval 相关文档
- `sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/tech-done.md`

禁止：

- 用 fixture/template/taxonomy 扩写冒充真实/受控图片 eval
- 写成真实电梯识别完成或跨楼层送达完成
- 修改上一轮 12-13 sprint 文件
- 修改 `OKR.md`

### 实现目标

1. 创建或校验 `trashbot.elevator_image_manifest.v1`，包含图片引用、场景、标签、evidence_ref 和受控边界。
2. 运行 OpenCV eval，输出 false positive、false negative、uncertain、阈值、混淆项和人工接管策略。
3. 无图片资源时，输出 CEO 决策 blocker：需要的资源、样本数量、采集方式、不能继续推进的原因。

### 验收命令

Engineer 必须按现有脚本名补充精确命令，至少包含：

```bash
python3 -m compileall -q onboard/scripts onboard/src
python3 -m unittest discover -s onboard/src -p 'test_*.py'
```

如存在电梯 eval/checker 脚本，必须运行并贴出关键输出；若无脚本，应补最小 checker 后运行。

### 通过标准

- 有真实/受控图片 manifest 并通过 checker，或明确 CEO blocker。
- eval 输出 FP/FN/uncertain 和人工接管策略。
- 不把 field precondition 写成真实电梯完成。

## Owner 任务 4：Stop-First HIL Gate

### Owner

- 主责：Hardware Infra Engineer
- 协作：Full-stack Software Engineer

### 文件范围

- `onboard/src/ros2_trashbot_hardware/**`
- `onboard/src/ros2_trashbot_bringup/**`
- `pc-tools/workstation/**` 中 stop/operator report 相关最小入口
- `docs/vendor/**` 只读引用，除非需要补项目侧说明
- `docs/` 中 HIL、安全、vendor source 相关文档
- `sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/tech-done.md`

禁止：

- 未读 vendor source 就写硬件事实
- 无现场看护、净空、急停/断电、授权时执行运动
- 写成 HIL pass、robot ACK 或 `T=1001` 同场材料，除非实际证据成立
- 修改上一轮 12-13 sprint 文件
- 修改 `OKR.md`

### 实现目标

1. 读取 `docs/vendor/VENDOR_INDEX.md` 和 WAVE ROVER 相关 vendor 文件，确认本轮引用来源。
2. 判断现场看护、净空、急停/断电、授权是否齐备。
3. 条件齐备：执行 stop-first 低速 pulse 流程，记录 preflight、stop、pulse、stop/post-status、operator report。
4. 条件不齐备：产出 CEO 决策 blocker，写明缺哪一项、为什么不能动、下一步需要 CEO 提供什么。

### 验收命令

无论是否运动，必须先运行软件护栏：

```bash
python3 -m compileall -q onboard/scripts onboard/src
python3 -m unittest discover -s onboard/src -p 'test_*.py'
```

如果进入 HIL，Engineer 必须在现场授权后补充实际 stop/pulse/post-status 命令和日志片段；如果不进入 HIL，必须在 `tech-done.md` 写明 `blocked_with_root_cause`。

### 通过标准

- 有 `field_hil_material` 或清晰 CEO blocker。
- vendor source 明确。
- 未授权时无运动命令。
- 未把软件测试或安全说明写成 HIL pass。

## Product 收口任务：Delivery-Readiness Chain

### Owner

- 主责：Product Manager / OKR Owner

### 文件范围

- `sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/tech-done.md`
- `sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/side2side_check.md`
- `sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/final.md`
- 如本轮证据成立且需要阶段更新，后续才允许修改 `OKR.md`

### 收口要求

1. 逐 owner 记录 pass、partial、blocked、timeout 和重试策略。
2. 串联 AMCL/Nav2、PC browser、电梯图片、stop-first HIL 四段证据。
3. 明确每段 evidence type：`robot_runtime_material`、`user_acceptance_material`、`field_precondition_material`、`field_hil_material` 或 `blocked_with_root_cause`。
4. 明确不可外推项。
5. 如新增 KR 或方向调整，写清 Objective、用户价值、owner、验收命令、证据边界、风险和 CEO 决策点。

## 并行派发建议

本轮是真实跨 owner Epic，文件范围可拆，建议同一轮并行启动 3 个一线子 agent，并让 Hardware 作为 P1 是否执行由现场安全条件决定：

| Dispatch | Agent | 任务 |
| --- | --- | --- |
| A | `robot-algorithm-engineer` 或 `worker` | AMCL/Nav2 readiness + 电梯图片 eval；若同一 agent 容量不足，优先 AMCL/Nav2。 |
| B | `robot-software-engineer` 或 `worker` | AMCL/Nav2 ROS2 lifecycle / bringup 集成与 no-motion 验证。 |
| C | `full-stack-software-engineer` 或 `worker` | PC browser button workflow。 |
| D | `robot-hardware-engineer` 或 `worker` | stop-first HIL gate；若现场条件缺失，产出 CEO blocker。 |

如果运行时只能单线执行，优先顺序为 A/B AMCL/Nav2 readiness -> C PC browser workflow -> D HIL gate -> Elevator image eval blocker/manifest。

## 子 Agent Prompt 摘要

主节点派发时必须包含完整角色 prompt、文件范围、验收命令和输出要求。每个子 agent 必须返回：

1. 实际改动的文件列表。
2. 验证命令输出结果。
3. 失败定位。
4. 剩余风险。
5. 证据边界和不可外推项。

## 本轮失败处理

- 测试或构建失败：owner 必须先定位、修复并重跑，不能把第一轮失败交差。
- 资源缺失：必须写成 `blocked_with_root_cause`，包含缺失资源、影响、下一步 owner 和 CEO 决策点。
- 重复消费：若 owner 只重复 latest/readback/status，Product 收口时不得计入 O10 涨分，并要求重派到 AMCL/Nav2、browser workflow、图片 eval 或 HIL gate。


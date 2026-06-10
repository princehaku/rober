# 2026-06-10 09:45 PC Robot Control Console

## sprint_type

micro

## owner

`full-stack-software-engineer`

## 用户价值和产品北极星

用户价值不是再做一个漂亮但空心的 PC UI，而是让运营人员在 PC 端把真实上位机和
Mock 数据源里的机器人证据链看清楚：每个 `task_id` 当前是什么状态、证据来自哪里、
哪些 proof 已经成立、哪些仍是 `not_proven`，以及为什么不能控制机器人。

产品北极星保持不变：把 `rober` 做成一台面向普通手机用户的低成本 ROS2 自主垃圾投递
机器人。PC 端本轮只服务运营调试、证据复盘和后续训练数据准备，不替代手机端，不绕过
云端/Robot API，不把 no-motion proof、Mock replay 或 readback 状态包装成送达成功。

## OKR 映射和方向判断

- 对应 Objective：O7 PC 端运营调试与数据训练平台。
- 关联证据 lane：现场 O3 验证 lane、O6 consumer read / archive / evidence 数据底座。
- 方向判断：`继续`。
- 继续理由：
  - O7 当前仍是低完成度 Objective，主要缺真实/Mock 机器人证据消费、实时状态、回放、
    标注和控制边界，而不是缺更多静态 surface。
  - O3 现场链路已经推进到真实上位机 no-motion map/localization/Nav2 path generation
    proof lane；PC 端必须消费这些 proof 的状态字段和 artifact，而不是继续展示 fixture
    占位。
  - 本地证据显示 `sprints/2026.06.10_09-05_nav2_no_motion_path_generation_proof/tech-done.md`
    已补出 PC/API 可读的 path generation 字段，但 `path_generated=true` 仍未正式证明；
    `sprints/2026.06.10_09-15_managed_nav2_localization_proof/tech-done.md` 则证明了 managed
    no-motion localization。PC UI 必须准确展示这类通过/阻塞差异。

## KR 拆解、更新或历史归档

本轮不迁移 KR 到历史区，也不更新 `OKR.md` 百分比；本轮是 O7 micro sprint 设计稿，
为下一轮工程实现定义最小可验收 KR：

- O7-KR1 状态地图/机器人位置：先展示 Robot API / O6 detail 中的 map、pose、Nav2 proof
  readback 和 artifact source；没有真实 `/tf` 转发时必须显示 `not_proven`。
- O7-KR3 历史路线回放：以 `task_id` 为主键读取 O6 consumer detail 或本地 Mock
  replay JSONL，展示 trajectory/events/evidence/keyframe 摘要；没有 `task_id` 不渲染回放。
- O7-KR4 数据标注准备：展示 evidence refs、keyframe refs、labeling 状态和缺口，不做提交。
- O7-KR6 手控/寻路：第一版只展示 safe command envelope 和禁用原因，不实现真实下发。

已完成 KR 历史记录位置：本轮无新增归档。前序证据来源仍在：

- `sprints/2026.06.10_09-05_nav2_no_motion_path_generation_proof/tech-done.md`
- `sprints/2026.06.10_09-15_managed_nav2_localization_proof/tech-done.md`
- `sprints/2026.06.10_02-05_field-run-bundle-replay-intake/tech-done.md`
- `docs/process/okr_progress_log.md`

剩余风险：这些证据仍不等于真实运动路线、HIL、safe control 或 delivery success。

## 本轮核心抓手

设计一个 PC Robot Control Console V1：以 `task_id` 和 proof artifact 为中心，把
Robot API status、O6 consumer detail、O3 no-motion map/localization/Nav2 证据、Mock
replay fallback 和控制禁用原因聚合到一个运营视图。每个区块都必须有来源、状态、刷新
时间和禁止控制边界。

## 功能点完整清单

### 1. 任务证据选择器

- 输入/选择 `task_id`。
- 显示数据来源：`robot_api`、`o6_consumer_detail`、`local_mock_replay_jsonl`、
  `local_field_evidence_manifest`。
- 显示 `task_status`、`proof_status`、`artifact_status`、`delivery_success=false`、
  `safe_to_control=false`、`primary_actions_enabled=false`。
- 没有 `task_id` 时页面只能显示空状态和下一步提示，不得渲染假任务。

### 2. Robot API 连接状态

- 支持配置或读取 Robot API base URL，默认可使用本机回环或局域网上位机地址。
- Node server 侧代理 Robot API；Vue 不直接跨域访问上位机。
- 展示 Robot API root / unified status / `/api/status` 摘要、HTTP 状态、最后刷新时间、
  schema、错误摘要和 guard flags。
- 网络失败、schema mismatch、危险 true 字段或状态缺失时必须 fail-closed。

### 3. O3 现场 proof 消费

- 展示 map proof、localization proof、Nav2 proof/path generation proof 的 latest 摘要。
- 必须可见字段：
  - `managed_runtime_started`
  - `scan_once_observed`
  - `map_once_observed`
  - `amcl_pose_observed`
  - `localization_tf_observed`
  - `planner_server_active`
  - `path_generation_requested`
  - `path_generation_succeeded`
  - `path_generated`
  - `path_point_count`
  - `root_causes`
  - `not_proven`
- UI 必须把 `path_generated=false`、`path_generation_succeeded=false` 和 blocker 显示出来，
  不得只显示“Nav2 已接入”。

### 4. 路线回放 / Mock fallback

- 优先消费 O6 consumer detail：`GET /api/o6/consumer/tasks/<task_id>` 的
  trajectory、events、evidence、labeling、inference、tunnel 摘要。
- 如果 O6 detail 不可用，允许显式选择本地 Mock replay JSONL 或 field evidence manifest。
- Mock fallback 必须显示 `source=local_mock` 或 `source=software_proof`，并保持
  `delivery_success=false`。
- 回放控件只允许浏览器内存里的 previous/next/play-pause cursor，不调用机器人 API。

### 5. Evidence / keyframe / 标注准备

- 展示 `evidence_ref`、keyframe basename、artifact path summary、capture time、schema、
  label status 和缺口。
- 允许只读查看待标注状态和下一步证据清单。
- 禁止实现 submit、rollback、export、upload、train 或任何会写云端/本地数据集的动作。

### 6. 手动控制和自动寻路边界

- 展示 safe command envelope、manual/navigate goal 未来接口、幂等 key、确认策略、
  robot ACK 缺口和 timeout/cancel/stop/recovery 缺口。
- 第一版所有真实控制入口必须 disabled：
  - 前进、后退、左转、右转
  - 速度 slider / joystick
  - 键盘方向键
  - map click goal
  - Navigate to point
  - `/api/base/manual`
  - `/cmd_vel`
  - Nav2 `NavigateToPose` / `FollowPath`
- 可以显示 locked placeholder，但文案必须说明需要 safety lock、HIL gate 和 robot ACK
  证据后才能放开。

### 7. Camera / LiDAR / Base readback

- Camera：展示 `/api/camera/health`、`/api/camera/devices` 和可选 preview 状态。
- LiDAR：展示 `/api/radar/status`、latest scan proof、raw packet proof。
- Base：展示 `/api/base/status` 和 latest feedback samples。
- 允许的按钮仅限 refresh/read latest/proof readback。任何 start/stop/manual/motion 类按钮
  必须禁用或不渲染。

## 必须实现

- 必须有 `Robot Control` 或等价 PC 控制台入口。
- 必须以 `task_id` 驱动任务详情、路线回放和 evidence 区块。
- 必须显示真实/Mock 数据来源和 artifact/proof source。
- 必须消费 Robot API 或 O6 consumer detail 中的状态字段，而不是前端硬编码成功状态。
- 必须在 Robot API 不可达、O6 detail 不可达、Mock 缺失、schema mismatch 或危险 true
  字段出现时 fail-closed。
- 必须保留 `safe_to_control=false`、`delivery_success=false`、
  `primary_actions_enabled=false` 的可见状态。
- 必须同步更新 `docs/product/pc_tools_workstation.md`，记录 V1 证据消费和禁止控制边界。
- 所有新增技术注释必须使用中文，且注释比例超过 20%。

## 禁止实现

- 禁止绕过 Robot API 或云端/O6 直接连 ROS2、串口、WAVE ROVER UART 或 `/cmd_vel`。
- 禁止把 Mock replay、no-motion proof、readback proof 写成真实路线通过。
- 禁止默认启动 map/radar/nav2/base runtime。
- 禁止真实手控、真实速度控制、真实转向控制、真实键盘控制、真实自动寻路下发。
- 禁止 TTS 发送、speaker 播放、标注提交、训练导出、云端生产写入。
- 禁止在没有 `task_id`、状态字段和 evidence source 的情况下渲染“任务成功”或“可控制”。

## 文件范围

下一轮实现允许 `full-stack-software-engineer` 修改：

- `pc-tools/workstation/src/App.vue`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/WorkstationTabs.vue`
- `pc-tools/workstation/src/components/*Robot*`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/server/*Robot*`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/styles.css`
- `pc-tools/workstation/test/*`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
- 新实现 sprint 的 `sprints/<new_round>/tech-done.md`

下一轮实现不得修改：

- `onboard/**`
- `firmware/**`
- `docs/vendor/**`
- WAVE ROVER/ESP32/Orange Pi UART、波特率、JSON 指令、速度映射、反馈协议等硬件事实
- 任意会默认启用机器人运动的 launch、service 或 runtime 配置

如果实现中发现 Robot API 缺字段，Full-Stack Engineer 只能先 fail-closed 展示缺字段；
不得自行修改 `onboard/scripts/upper_robot_api.py`，应另开 Robot Software sprint。

## 优先级和验收口径

优先级：`P0`。

工程实现验收必须同时满足：

1. PC 页面存在控制台入口，并且任务证据选择器、Robot API 状态、O3 proof、路线回放、
   evidence/标注准备、控制边界、Camera/LiDAR/Base readback 七个区块可见。
2. 至少一条真实或 Mock `task_id` 能驱动详情、状态、trajectory/events/evidence 摘要。
3. 所有状态都显示 source、schema/status、刷新时间和 fail-closed reason。
4. Robot API / O6 detail 不可达时，页面仍能显示阻塞状态，不出现误导性成功。
5. `/api/base/manual`、`/cmd_vel`、Nav2 goal、map start、radar start、键盘控制和 map click
   goal 默认禁用或不渲染。
6. 文档同步到 `docs/product/pc_tools_workstation.md`。
7. 新增技术注释为中文，且注释比例满足项目要求。

## 验收命令

Product 设计阶段必须运行：

```bash
git status --short --branch
test -f sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md
rg -n "sprint_type|功能点|验收|owner|文件范围|O7|task_id|状态|控制|禁止|Mock|真实" sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md
```

下一轮 Full-Stack Engineer 实现阶段至少运行：

```bash
git status --short --branch
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
rg -n "Robot Control|task_id|O7|Mock|真实|状态|safe_to_control|primary_actions_enabled|delivery_success|/api/base/manual|cmd_vel|path_generated" pc-tools/workstation docs/product/pc_tools_workstation.md pc-tools/README.md
```

如实现了本地 server smoke，追加：

```bash
cd pc-tools/workstation && npm run dev
curl -sS http://127.0.0.1:<port>/api/health
curl -sS http://127.0.0.1:<port>/<robot_control_proxy_or_summary_path>
```

## 对应责任 Engineer

- 主责：`full-stack-software-engineer`
- 咨询：默认不并行派单。若 Robot API 合同缺字段，由 `robot-software-engineer` 另开 micro
  sprint；若涉及硬件真实控制边界，由 `rober-hardware-engineer` 只读确认 vendor/硬件事实。

## 风险、阻塞和需要补齐的证据链

- O3 path generation lane 当前仍存在 `path_generated=true` 未正式证明的风险；PC 必须显示
  blocker，而不是隐藏差异。
- O7 控制台本轮仍不证明真实 RTC/视频、真实 ASR/TTS、真实手控/寻路、真实地图电梯状态、
  真实云端生产链路或上车 delivery success。
- Mock fallback 有产品风险：如果 UI 不显式标注来源，运营人员会误以为真实机器人已完成。
- 后续要提升 O7 完成度，必须继续补齐 `task_id` 对应的真实 field run bundle、map.yaml、
  route.csv、keyframe、rosbag、replay JSONL 或真实/Mock delivery result。

## 需要创建或更新的 sprint 文档

- 本轮是 micro sprint，只强制维护本文件：
  `sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md`
- 下一轮工程实现必须创建自己的 micro sprint `tech-done.md`，记录实际改动、验证结果、
  失败定位和剩余风险。

## 本轮实际改动

- 更新 `sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md`。
- 未修改 `docs/product/pc_tools_workstation.md`，因为本轮仍是工程前产品设计；产品边界已在
  sprint 设计中明确，下一轮实现时再同步产品文档。
- 未修改产品代码、测试代码、硬件配置、launch 参数、firmware 或 vendor 文件。

## 本轮验证结果

已运行用户指定验收命令：

```text
git status --short --branch
## master...origin/master
 M docs/hardware/board_sensor_stack_smoke.md
 M docs/navigation/fixed_route_workflow.md
 M onboard/scripts/upper_robot_api.py
 M sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md
?? sprints/2026.06.10_14-40_nav2_path_generation_artifact_stabilization/
```

说明：本轮只修改 `sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md`。
其余工作区改动为本轮开始前或并行上下文中已有的非本轮范围改动，未被本轮回滚或覆盖。

```text
test -f sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md
```

结果：通过，无输出。

```text
rg -n "sprint_type|功能点|验收|owner|文件范围|O7|task_id|状态|控制|禁止|Mock|真实" sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md
```

结果：通过，命中 `sprint_type`、`owner`、`功能点完整清单`、`O7`、`task_id`、
`状态`、`控制`、`禁止实现`、`Mock`、`真实`、`文件范围`、`验收命令` 等关键段落。

## 失败定位

暂无。三条指定验收命令均通过。

## 剩余风险

- 本轮只完成产品设计和 sprint 留档，不交付 PC UI。
- 真实/Mock 数据接入、Node proxy、Vue 区块、测试和产品文档同步仍需下一轮
  `full-stack-software-engineer` 实现。
- 本轮未运行 `pc-tools/workstation` build/test/lint，因为用户明确要求不要写产品代码；
  这些命令属于下一轮工程实现验收。

记录时间：2026-06-10 09:45 CST。

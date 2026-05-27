# Mock OKR 90 Acceptance Tech Plan

## 目标

在 CEO 新口径下，组织工程侧产出可复验 mock evidence，使 Objective 1、Objective 5、Objective 6、Objective 7 均达到 90%+ `mock/software completion`。真实材料缺口必须继续标记为 `not_proven`，不能把 mock/software proof 写成真实硬件、真实公网、真实 4G、production DB、OSS/CDN live traffic 或真实手机/browser 已完成。

## OKR 最低优先级核对

`OKR.md` 4.1 当前进度从低到高：

1. Objective 7：约 48% software proof。
2. Objective 6：约 62% software proof。
3. Objective 5：约 80%。
4. Objective 1：约 83%。

本 sprint 针对最低 Objective：是。Objective 7 是最低完成度 Objective，本轮 Task D 专门把 O7 PC 端运营调试平台推进到 90%+ mock/software completion。同时，本轮按 CEO 要求覆盖所有未达 90% 的 Objective 1、Objective 5、Objective 6、Objective 7。

## 用户新口径对完成度判断的影响

上一轮判断：O1/O5 因缺真实材料不能超过 90%，O6/O7 只能按 software proof 增长。

本轮判断：CEO 明确允许 mock 数据替代真实效果，因此 Product Owner 在后续 closeout 中可将完成度拆成：

- `mock/software completion`：mock 数据、stub、离线 bundle、本地 Docker/API smoke、browser-like 测试和 fail-closed UI 证据可计入 90%+。
- `real material completion`：真实 WAVE ROVER、真实 UART/HIL、真实公网/4G、production DB/queue、OSS/CDN live traffic、真实手机/browser、真实 RTC/ASR/TTS 和真实手控/Nav2 不因 mock 证据而完成，继续标为 `not_proven` 或 `真实材料未完成`。

后续 `OKR.md` 如更新，必须使用类似表述：`90%+ mock/software completion; real material not_proven`。

## 并行策略

本 sprint 是 Epic，覆盖 4 个 Objective 和 4 个工程 owner，文件范围互不完全重叠，验收证据可独立产出，因此进入实现时应并行派发 Task A-D。Task E 在 A-D 返回后由 Product Owner 收口。

Codex 运行时若可用 `spawn_agent(agent_type=worker)`，主节点必须按 AGENTS.md 的五段 prompt 派发；若运行时缺少子 agent 工具，不得假装派发，只能保留本计划并说明无法执行实现。

## Task A - Objective 1 Mock Hardware Evidence

Owner：`robot-software-engineer` 主责，`rober-hardware-engineer` 只读复核 vendor/boundary。

目标：

- 用 mock serial、virtual HIL packet 或单元/集成测试证明 O1 软件链路达到 90%+ mock/software completion。
- 证据覆盖 JSON newline 编码、`T=1` wheel command、反馈解析、IMU/battery 发布、坏帧容错和参数边界。
- 明确真实 WAVE ROVER、真实 UART/HIL、真实 Orange Pi 串口、真实 IMU/battery 标定仍是 `not_proven`。

允许文件范围：

- `onboard/src/ros2_trashbot_hardware/**`
- `onboard/src/ros2_trashbot_bringup/**`
- `docs/interfaces/**`
- `docs/hardware/**`
- `sprints/2026.05.28_00-04_mock-okr-90-acceptance/tech-done.md`

禁止：

- 不改 vendor 原始资料。
- 不写真实串口路径、引脚、电压或机械尺寸新结论；真实硬件事实必须引用 `docs/vendor/VENDOR_INDEX.md`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test
rg -n "Objective 1|90|mock|software proof|not_proven|WAVE ROVER|UART|HIL" onboard/src/ros2_trashbot_hardware docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
git diff --check -- onboard/src/ros2_trashbot_hardware onboard/src/ros2_trashbot_bringup docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

## Task B - Objective 5 Mock Cloud Control Evidence

Owner：`full-stack-software-engineer`。

目标：

- 用本地/mock control plane smoke 证明 O5 达到 90%+ mock/software completion。
- 覆盖 commands/status/ack、bearer/env credential、mock 4G 中断、mock DB/queue、mock OSS/CDN graceful degradation。
- 保留真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser `not_proven`。

允许文件范围：

- `cloud-relay/**`
- `docs/interfaces/**`
- `docs/product/cloud_4g_infrastructure.md`
- `sprints/2026.05.28_00-04_mock-okr-90-acceptance/tech-done.md`

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s cloud-relay/tests
rg -n "Objective 5|90|mock|software proof|not_proven|4G|production DB|OSS|CDN|live traffic" cloud-relay docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
git diff --check -- cloud-relay docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

## Task C - Objective 6 Mock Archive 90 Evidence and Runtime State Fence

Owner：`full-stack-software-engineer` 主责；`robot-software-engineer` 仅补 onboard publisher 接口事实或测试。

目标：

- 把 O6 archive task/event/annotation/inference/query 做成单命令或少命令可复验 mock evidence。
- 验证机器人侧 publisher、algorithm feed、cloud archive core 的 schema 兼容。
- 明确 `o6_cloud_archive_state.json` 或同类 runtime state 不落仓库根目录。优先使用 `TRASHBOT_O6_ARCHIVE_STATE` 指向 `/tmp` 或测试临时目录；如需要默认路径，必须落在明确 ignored runtime 目录，不得污染仓库根。
- 真实安全隧道、production DB/queue、真实 OSS upload、真实推理 runtime、live O6 API 继续 `not_proven`。

允许文件范围：

- `cloud-relay/**`
- `onboard/src/ros2_trashbot_behavior/**`
- `onboard/src/ros2_trashbot_nav/**`
- `docs/interfaces/**`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/navigation/**`
- `docs/vision/**`
- `sprints/2026.05.28_00-04_mock-okr-90-acceptance/tech-done.md`

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s cloud-relay/tests
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_archive_event_publisher.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_algorithm_evidence_feed.py
test ! -e o6_cloud_archive_state.json
rg -n "Objective 6|90|mock|software proof|not_proven|trashbot.archive.v1|o6_cloud_archive_state|TRASHBOT_O6_ARCHIVE_STATE|production DB|OSS" cloud-relay onboard/src/ros2_trashbot_behavior onboard/src/ros2_trashbot_nav docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
git diff --check -- cloud-relay onboard/src/ros2_trashbot_behavior onboard/src/ros2_trashbot_nav docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

## Task D - Objective 7 Mock Operations Console 90 Evidence

Owner：`full-stack-software-engineer` 主责；`robot-algorithm-engineer` 提供 mock archive feed 或接口事实。

目标：

- O7 PC console 六区均有 mock/live-like evidence：实时地图/位置、电梯状态、历史路线回放、数据标注、推理摘要、ASR/TTS stub、手控/寻路 stub。
- PC 端可消费 O6 mock archive bundle 或 mock bearer API 输出。
- 安全边界 fail-closed，真实控制不执行，真实 RTC/视频、真实 ASR/TTS、真实手控/Nav2、真实 browser/手机继续 `not_proven`。

允许文件范围：

- `pc-tools/**`
- `cloud-relay/**`
- `onboard/src/ros2_trashbot_nav/**`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/**`
- `sprints/2026.05.28_00-04_mock-okr-90-acceptance/tech-done.md`

验收命令：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_algorithm_evidence_feed.py
rg -n "Objective 7|90|mock|software proof|not_proven|实时地图|电梯状态|历史路线回放|数据标注|ASR|TTS|手控|寻路|safe_to_control|robot_control_executed" pc-tools cloud-relay onboard/src/ros2_trashbot_nav docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
git diff --check -- pc-tools cloud-relay onboard/src/ros2_trashbot_nav docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

## Task E - Product Acceptance and OKR Closeout

Owner：`product-okr-owner`。

目标：

- 汇总 Task A-D 的实际改动、验证结果、失败定位和剩余风险。
- 更新本 sprint `tech-done.md`、`side2side_check.md`、`final.md`；如证据充分，再更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
- 所有完成度写成 `90%+ mock/software completion`，并保留 `真实材料未完成` / `real material not_proven`。

允许文件范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.28_00-04_mock-okr-90-acceptance/**`

验收命令：

```bash
rg -n "Objective 1|Objective 5|Objective 6|Objective 7|90|mock/software completion|software proof|真实材料|not_proven|Task A|Task B|Task C|Task D|o6_cloud_archive_state" OKR.md docs/process/okr_progress_log.md sprints/2026.05.28_00-04_mock-okr-90-acceptance
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

## 总体验收命令

工程 Task A-D 完成后，主节点或 Product Owner 做收口时至少复核：

```bash
test ! -e o6_cloud_archive_state.json
rg -n "sprint_type: epic|mock|90|Objective 1|Objective 5|Objective 6|Objective 7|software proof|真实材料|not_proven|验收命令|文件范围|o6_cloud_archive_state" sprints/2026.05.28_00-04_mock-okr-90-acceptance
git diff --check -- sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

## 风险边界

- 本轮计划允许 mock 数据替代真实效果，但只适用于 `mock/software completion`，不适用于 `real material completion`。
- Objective 1 的真实硬件事实仍以 `docs/vendor/VENDOR_INDEX.md` 及其指向资料为准；真实集成阶段必须再次查阅 vendor 文件。
- Objective 5 不证明真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic 或真实手机/browser。
- Objective 6 不证明真实安全隧道、production DB/queue、真实 OSS upload、真实模型 runtime 或 live O6 API。
- Objective 7 不证明真实 RTC/视频、真实 ASR/TTS、真实手控/Nav2、真实地图/电梯数据流或真实 browser/手机。
- 若任何 Task 验证失败，负责 Engineer 必须先定位、修复并重跑；不能把首轮失败作为最终交付。

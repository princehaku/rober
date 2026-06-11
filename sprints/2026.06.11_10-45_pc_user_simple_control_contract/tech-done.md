# PC User Simple Control Contract

## sprint_type

micro

## 本轮目标

CEO 明确不接受 PC 页面继续变成工程/debug 风格。本轮只做产品设计收口，不写功能代码：
把 PC 端“普通用户简易首屏 + 完整控制能力逐步解锁”的契约写清楚，作为后续
Full-Stack / Robot Software 实现和验收边界。

## 已读材料

- `AGENTS.md`
- `OKR.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.06.11_10-30_pc_simple_user_interface_restore/tech-done.md`
- `sprints/2026.06.11_08-20_pc_plain_user_home_second_restore/tech-done.md`
- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/tech-done.md`
- `sprints/2026.06.11_10-50_pc_radar_cold_start_refresh_stabilization/tech-done.md`

## 实际改动

- `docs/product/pc_tools_workstation.md`
  - 新增 `PC 普通用户简易控制契约 V1`。
  - 锁定默认首屏不可变契约：`Rober 小车控制台`、一个短地址输入、五张普通用户卡片。
  - 明确默认可见动作只允许连接/刷新、打开/关闭画面、刷新雷达、刷新地图、地图列表、停止。
  - 明确工程词、证据词、调参项、方向点动、Nav2/路径检查、HIL/proof/raw/readback 不得回流首屏。
  - 明确实时图传、雷达刷新、建图、定位/路径检查、手动移动/导航的渐进解锁规则。
  - 写入后续编码验收口径、owner 和最短执行路径。
- `sprints/2026.06.11_10-45_pc_user_simple_control_contract/tech-done.md`
  - 新增本轮 micro sprint 留档。

未修改 `OKR.md`：本轮只建立产品契约，没有新增真实上位机、真实 browser 或真实现场 artifact，
因此不调整 O7 百分比。

未修改任何 PC UI/CSS/代码、测试、onboard、hardware 或 vendor 文件。

## 普通用户首屏不可变契约

- 首屏标题固定为 `Rober 小车控制台`。
- 首屏只允许五张卡片：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。
- `移动/导航` 卡片默认只显示普通状态和 `停止`，不显示方向按钮、速度/时长、路径检查、
  自动导航、HIL checklist 或最近证据摘要。
- 所有工程材料必须在默认关闭的 `高级诊断` / `高级工具` 内。

## 渐进解锁

- 实时图传：首屏只打开/关闭和显示可读状态；帧级证据、近黑判断、peer/ICE/SDP 只进高级诊断。
- 雷达：首屏只 `刷新雷达`；start/stop、scan hz、raw packet、TF、blocked reasons 只进高级诊断。
- 建图：首屏只 `刷新地图` / `地图列表`；开始建图、保存地图、map_name、artifact_path 只进高级诊断。
- 定位/路径检查：定位重置、路径生成、导航目标预检都只作为高级诊断 readiness，不执行导航。
- 手动移动：stop 常驻首屏；非 stop jog 只在现场材料齐备后进入高级诊断，并且只能 exactly one
  低速短时 jog 后立即 stop。

## 后续编码验收口径

- `.simple-user-console` 作用域必须持续断言五张卡片存在，禁词不存在。
- 新增任何能力都必须同时验证：普通首屏未被污染，高级诊断能力存在且 fail-closed 字段不漂移。
- Browser/DOM smoke 必须覆盖默认首屏；不能只用关闭的 details 文本或单元测试替代。
- 真实 evidence capture 要按雷达、实时图传、建图、定位/路径检查、手动移动分别保存 artifact。

## 下一步 owner 和最短执行路径

- 主责 owner：`full-stack-software-engineer`。
- 协作 owner：涉及上位机 endpoint 事实时由 `robot-software-engineer` 补接口事实；不要让工程细节进入首屏。
- 最短路径：保持五卡片首屏不变，先补固定首屏回归测试和 Browser smoke；然后按
  图传可见内容、雷达 no-motion scan proof、地图材料、定位/路径预检、一次低速短时 jog 的顺序推进。

## 验证结果

- `git diff --check`：通过，输出为空。
- 不运行 PC build/test/lint：本轮不允许改代码，且实际未修改 PC 代码或测试。

## 剩余风险

- 本轮是产品契约收口，不产生新的真实硬件、真实 browser 图传、真实地图、真实定位或真实运动证据。
- 后续工程实现如果只补功能、不补 `.simple-user-console` 禁词测试和 Browser smoke，仍可能再次污染首屏。
- 雷达、摄像头、建图、定位和运动各自真实证据仍需后续 owner 逐项采集。

## 完成前反思

- 满足 CEO 对普通用户简易风格的方向要求：把首屏作为不可变合同，而不是临时 UI 偏好。
- 没有把 PRD/文档当作 O7 进度提升证据，未调整 OKR 百分比。
- 文件改动限定在允许范围内；没有修改 UI/CSS/代码实现、测试、onboard、hardware 或 vendor 文件。

## 当前运行时间

2026-06-11 10:45:00 CST

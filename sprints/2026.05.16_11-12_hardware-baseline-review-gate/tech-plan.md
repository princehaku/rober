# Sprint 2026.05.16_11-12 Hardware Baseline Review Gate - Tech Plan

## 1. 目标

把 PR #5 Codex Review 对硬件基线的 P1/P2 反馈转成可执行、可验证的 product/hardware baseline gate。计划阶段只创建 sprint 三份计划文档；后续实施由 Hardware / Robot / Autonomy / Full-stack 分工执行。

本计划不是 hardware proof、不是 LiDAR/ToF vendor proof、不是 Objective 5 external proof。当前可用证据边界仍是 plan + local software/process proof，不证明真实 WAVE ROVER、真实 2D LiDAR、真实 ToF、HIL、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic 或 production DB/queue。

## 2. OKR 最低优先级核对

当前 live `OKR.md` 4.1 table：

- Objective 5：约 66%，当前最低。
- Objective 1：约 73%。
- Objective 2：约 78%。
- Objective 3：约 78%。
- Objective 4：约 80%。

本 sprint 不直接主攻最低 Objective 5。理由：

- Objective 5 的主要缺口是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
- 当前开发主机只有 Docker；上一轮 final 已明确 `software_proof_docker_mobile_field_material_retest_request_gate` 不能替代真实外部 O5 材料。
- 继续堆本地 O5 metadata 不会提高真实 O5 完成度，且会重复消费外部证据 blocker。

本 sprint 转向 Objective 4 / Objective 1 的可行动作：修复 PR #5 暴露的硬件 baseline gate。该动作能消除低成本量产边界和硬件事实可追溯的矛盾，为后续真实设备采购、bringup、Nav2/SLAM、电梯 evidence contract 和手机状态展示提供统一口径。

最低 Objective 审查规则：所有后续 sprint 的 `OKR 最低优先级核对` 必须读取 live `OKR.md` 4.1 table，不得沿用旧 final、旧 PR diff 或 narrative line。

## 3. Team Owner / File Split

本轮计划文档已创建，后续实施按以下 owner/file split 并行启动 2-4 个子 agent：

| Owner | 责任 | 可改文件范围 | 不可越界 |
| --- | --- | --- | --- |
| `hardware-engineer` | 主责硬件 baseline 文档修复，统一默认硬件集与 mandatory baseline，补清 vendor/source attribution 边界 | `docs/product/production_hardware_boundary.md`、必要时 `docs/vendor/` 只读引用或补新增本地采购资料文档 | 不写产品代码，不声明 LiDAR/ToF 已实测 |
| `robot-software-engineer` | 检查 bringup/launch/diagnostics contract，确保传感器数量、frame id、阈值、设备路径参数化 | ROS2 bringup、diagnostics、hardware config 相关文件和对应 docs | 不硬编码未证明设备路径或通道数 |
| `autonomy-engineer` | 检查 Nav2/SLAM、电梯语义证据、ToF 近场安全 responsibility split | nav、vision、behavior 自主能力 contract 和相关 docs | 不把 ToF 写成主建图输入，不宣称 field pass |
| `full-stack-software-engineer` | 检查手机端是否需要只读展示硬件基线缺口和 `not_proven` 状态 | `mobile/web`、operator gateway API docs、phone-safe copy docs | 不解锁 Start / Confirm Dropoff / Cancel |
| `product-okr-owner` | 维护 OKR、验收口径、sprint 收口链路 | `OKR.md`、`sprints/`、`docs/product/` | 不把计划文档当业务结果 |

如果实施阶段发现接口强耦合，Robot Platform Engineer 负责最终集成验收，其他 owner 以并行咨询/事实补充方式参与。

## 4. 工程任务

### Task A - Hardware Baseline Document Gate

Owner：`hardware-engineer`

目标：

- 修复 `docs/product/production_hardware_boundary.md` 中 `Default Hardware Set` 与 `Navigation/Sensing Baseline` 的矛盾。
- 明确 2D LiDAR / ToF 是产品 mandatory baseline、采购待补证、还是 optional enhancement。
- 引用 `docs/vendor/VENDOR_INDEX.md`，说明当前本地 vendor 资料覆盖 Orange Pi Zero 3、WAVE ROVER、UART JSON、WAVE ROVER mechanical references、vendor camera tutorials；不覆盖 2D LiDAR / ToF 已实测来源。

验收：

- 文档中没有一处把 2D LiDAR / ToF 写成 vendor 已实测。
- BOM / default hardware / mandatory baseline 不再互相矛盾。
- 若保留 ToF 2 路/4 路数字，必须写清来源或改成待采购/待实测建议。

### Task B - Robot Bringup Contract Gate

Owner：`robot-software-engineer`

目标：

- 检查 ROS2 bringup、diagnostics、hardware config 是否受 baseline 影响。
- 若新增传感器 contract，只允许通过 launch/params 暴露，不写死设备路径、frame id、阈值或通道数。
- 保持硬件相关注释为中文，且复杂逻辑说明“为什么”。

验收：

- `rg` 可证明没有新增硬编码 Orange Pi UART、LiDAR/ToF 设备路径或未证明 channel count。
- 任何 diagnostics 输出都保持 `not_proven` / `hardware_material_pending` 边界，不触发控制或 ACK。

### Task C - Autonomy Sensor Responsibility Gate

Owner：`autonomy-engineer`

目标：

- 把 responsibility split 写成可执行 contract：2D LiDAR 负责 SLAM/Nav2 主链，monocular 负责电梯门/楼层语义证据，ToF 负责近场 safety gate。
- 明确 ToF 不是主建图输入，未接硬件前不宣称 real field pass。
- 与 Objective 2/3 的 route/elevator evidence chain 保持 same `evidence_ref` 和 `software_proof` / real field proof 边界。

验收：

- 相关 docs 或 contract 不出现“LiDAR/ToF 已实测”“delivery_success=true”“field pass”这类无证据结论。
- 可用静态 gate 检查 `not_proven`、`software_proof` 和 real proof 的 copy 边界。

### Task D - Phone-Safe Hardware Baseline Status

Owner：`full-stack-software-engineer`

目标：

- 若手机端需要消费硬件 baseline 状态，只做只读展示：硬件基线缺口、采购待补证、`not_proven`、下一步材料。
- 不改变 Start / Confirm Dropoff / Cancel gating。
- 不暴露 raw ROS topic、raw JSON、硬件 jargon 或未证明成功文案。

验收：

- mobile/web 测试保持通过。
- UI copy 不把计划文档或 `docs/vendor/VENDOR_INDEX.md` 写成 hardware proof。

### Task E - Product Closeout and OKR Gate

Owner：`product-okr-owner`

目标：

- 实施完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`。
- 如硬件 baseline 文档矛盾被修复，可在 Objective 4 / Objective 1 记录“产品/文档 gate 改善”；没有真实硬件证据时不提升 HIL、LiDAR/ToF vendor proof 或 O5 external proof。
- 更新 `OKR.md` 时必须读取 live table，不得沿用历史 narrative。

验收：

- final 明确写出是否调整 OKR 百分比和证据边界。
- `OKR.md` 4.1 与 narrative 一致。

## 5. 验证围栏

计划阶段必须运行：

```bash
rg -n "PR #5|production_hardware_boundary|2D LiDAR|ToF|docs/vendor/VENDOR_INDEX.md|Objective 5|O5|Docker|software_proof|OKR 最低优先级核对" sprints/2026.05.16_11-12_hardware-baseline-review-gate
git diff --check -- sprints/2026.05.16_11-12_hardware-baseline-review-gate
```

后续实施阶段建议围栏：

```bash
rg -n "Default Hardware Set|Navigation/Sensing Baseline|2D LiDAR|ToF|docs/vendor/VENDOR_INDEX.md|not_proven|hardware_material_pending" docs/product/production_hardware_boundary.md
rg -n "2D LiDAR|ToF|delivery_success=true|field pass|hardware proof|Objective 5 external proof" docs mobile onboard pc-tools
git diff --check -- docs/product/production_hardware_boundary.md sprints/2026.05.16_11-12_hardware-baseline-review-gate
```

如改到代码，再由对应 Engineer 加跑 focused unit test、`py_compile`、`node --check`、mobile targeted tests 或 Docker/Humble build。不要用 broad regression 代替本轮 fenced validation。

## 6. 风险边界

- 不把本计划文档当成 hardware proof。
- 不把 `docs/vendor/VENDOR_INDEX.md` 当成 LiDAR/ToF vendor proof；它目前只确认本地硬件事实来源和已覆盖资料范围。
- 不把 local Docker 或 `software_proof` 当成真实 Objective 5 external proof。
- 不把 mandatory product baseline 写成已采购、已安装、已接线、已标定或已 HIL 通过。
- 不因修复文档矛盾就宣称 delivery success、field pass、真实手机设备通过或真实公网链路通过。

## 7. 下一步实施分工

下一步进入 implementation 时，必须由子 agent 执行：

- 并行启动 `hardware-engineer` 和 `robot-software-engineer`。
- 如 Hardware 修复牵涉 Nav2/SLAM/电梯感知 contract，同时并行启动 `autonomy-engineer` 做只读/轻量 contract 补充。
- 如需要 phone-safe 状态展示或 copy，启动 `full-stack-software-engineer`，并保持 Start / Confirm / Cancel fail-closed。
- Product 只做验收、sprint 文档链路和 OKR 更新，不替 Engineer 写实现。

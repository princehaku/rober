# Sprint 2026.05.19_00-01 Elevator Assist Action Feedback Mainline - PRD

## 1. 用户价值

普通手机用户或现场 operator 不应等任务结束后才知道小车处于哪个电梯子阶段。电梯 assisted delivery 已经被 PR #4 / PR #5 拉进 MVP 主线，本轮要把行为层实时 feedback 从粗粒度 `delivering` 推进到电梯阶段可观测，方便手机端、远程诊断和现场人员理解“正在等门、正在进电梯、正在请求按楼层、正在等目标楼层、正在驶出”。

## 2. OKR 映射

- Objective 2：补齐电梯 assisted delivery 主链路的 action feedback 可观测性，支撑状态机和失败恢复可解释。
- Objective 4：让手机/用户触点可以消费更细的用户可读状态，但本轮不直接改手机 UI 或打开主操作 gating。
- Objective 5：不推进；缺真实 external proof。
- Objective 1：不推进；缺真实 WAVE ROVER/UART/HIL 和 PR #5 真实传感器材料。

## 3. 范围

本轮只做 Robot 行为层实时 feedback 和对应文档/收口：

- 在电梯 dry-run / rehearsal artifact 驱动路径里发布 `TrashCollection.Feedback`。
- 保持 task record 现有 `elevator_assist` 记录结构兼容。
- 增加或调整现有围栏测试，不新增大测试矩阵。
- 同步产品/接口文档，说明 feedback 字段和证据边界。

不做：

- 不读取真实电梯、真实手机、Nav2 runtime、serial/UART、WAVE ROVER 或云服务。
- 不改变 Start Delivery / Confirm Dropoff / Cancel gating。
- 不新增硬件默认值、传感器 SKU、串口参数、波特率、接线或电压假设。
- 不宣称 delivery success 或真实现场通过。

## 4. 验收标准

1. 默认 dry-run 成功路径中，goal feedback 列表包含电梯阶段 feedback，`current_step` 或 `event/message` 能区分关键子阶段。
2. Rehearsal artifact 成功路径中，feedback 按 artifact 阶段顺序输出，并沿用 safe `evidence_ref` 的 software-proof 口径。
3. Rehearsal artifact 失败或 dry-run 失败路径中，最后反馈能表达人工接管/失败阶段，且 task record 仍 fail-closed。
4. 文档明确这是 `software_proof`，不等于真实电梯、HIL、真实 Nav2/fixed-route 或送达成功。

## 5. 责任分工

- `robot-software-engineer`：实现 feedback、调整围栏测试、同步接口/产品文档。
- `product-okr-owner`：更新 sprint 收口、OKR 进度口径和 progress log，确认不虚增真实材料进度。

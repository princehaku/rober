# O1 Manual HIL Gate Current Evidence Intake PRD

## 用户价值

用户最终需要小车在真实场地中低速、安全、可回放地完成垃圾送达。本轮不直接发车，而是把一次真实 PC proxy / 上位机 HIL gate 材料收束成可复验合同，让后续现场人员不用从散乱 JSON 中判断能否做低速短动：系统应明确显示哪些 safety precondition 已满足、哪些仍缺、为什么非 stop motion 被拒绝，以及 stop 路径是否可用。

## 产品范围

本 sprint 范围是 O1 硬件可信底盘证据链的 material intake：

- 消费已有真实 PC proxy / 上位机 readback artifact。
- 生成只读 summary，不回显敏感 URL、token、绝对路径、raw frame 或 traceback。
- 继续固定所有安全/成功字段为 false。
- 输出下一次现场 HIL 需要补齐的 evidence 列表。

不在本轮范围内：

- current live HIL pass。
- 实机非 stop 点动。
- wheel direction confirmation。
- IMU/battery calibration。
- Nav2 route execution。
- O5 production cloud cutover。

## OKR 对齐

- Objective：O1 打通官方硬件协议，建立可信底盘控制层。
- 当前缺口：current live HIL pass、轮速方向、IMU/battery 标定、same-run path generation success、Nav2 route execution success。
- 本轮贡献：把 manual HIL gate 的真实 readback 材料接入 O1 当前 bundle，形成 fail-closed、可复验、可脱敏的准入材料合同。

## 验收标准

- 默认 CLI 读取既有 artifacts 并输出 `manual_hil_gate_current_evidence_material_present=true`。
- 输出 `manual_hil_gate_status=blocked` 与缺口列表，且缺口至少包含 external video / camera visible / wheel feedback L/R nonzero / LiDAR motion delta。
- 输出 stop safety smoke 已转发、非 stop manual request 被本地拒绝、远端 base manual 未调用。
- 输出 T1001 feedback observed count 和 vendor source 摘要。
- 输出 operator structured report material-only 状态，不能让 nested delivery claim 打开顶层 `delivery_success`。
- 单元测试覆盖正向、缺关键 artifact、remote manual 被调用、dangerous true、unsafe value、operator claim 泄漏等路径。

## 用户可见结论

最终 closeout 必须用普通产品语言说明：

- 本轮新增了什么证据读取能力。
- 为什么仍不能认为小车已经安全可控。
- 下一次现场要补什么材料才能从 gate intake 进入真实短动 HIL。

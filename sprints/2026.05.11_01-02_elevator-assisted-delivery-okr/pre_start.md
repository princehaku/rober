# Sprint 2026.05.11 01-02 Elevator Assisted Delivery OKR - Pre Start

## 状态

- 阶段：pre_start completed。
- 时间：2026-05-11 01:02 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 本轮性质：产品/OKR/文档更新，不改代码、不改硬件配置。

## 背景

CEO 要求把“进出电梯”纳入 OKR：小车识别电梯是否开门，进入电梯后语音请求好心人帮忙按 1 楼，持续识别是否到目标楼层，并在目标楼层开门时快速驶出。

## 目标

- 把电梯 assisted delivery 纳入北极星、战略定位、Objective/KR、风险和下一步建议。
- 新增产品文档，明确最小用户流程、语音提示、状态机边界、识别要求、人工协助边界和验收口径。
- 保持既有定位：普通手机用户、低成本、trash delivery，不默认机械臂或昂贵硬件。

## Owner

- 主责：`product-okr-owner`。
- 后续实现 owner：
  - `robot-software-engineer`：行为状态机。
  - `autonomy-engineer`：电梯门/楼层/驶出感知证据。
  - `full-stack-software-engineer`：手机状态与语音提示。
  - `hardware-engineer`：仅在涉及硬件事实、安装、电气或串口时介入。

## 范围

允许改动：

- `OKR.md`
- `docs/product/`
- `sprints/2026.05.11_01-02_elevator-assisted-delivery-okr/`

明确不改：

- `src/`
- `docs/vendor/`
- `docs/hardware/`
- `README.md`
- `sprints/2026.05.11_01-02_hardware-proof-param-gate/`
- 范围外任何文件

## 风险

- 电梯能力容易被误读为当前 MVP 已完成或全自动控制电梯。
- 楼层识别、门开识别和驶出安全需要后续真实证据。
- 本轮不做硬件事实判断，不新增引脚、电压、UART、波特率或机械安装假设。

## 验收口径

- OKR 中明确 H2/受控场景定位。
- 产品文档覆盖流程、语音、状态、识别、人工协助和验收。
- Sprint 六件套完整存在且无占位符。
- 最小文档验证命令通过。

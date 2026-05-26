# O7 RTC Realtime Foundation Pre-Start

## sprint_type: epic

## 1. 启动原因

CEO 追问“视频 RTC 不需要机器上协议打通吗？板子上的代码够了？”后，本轮 O7 推进必须先校正方向：PC 端运营调试平台不能只补页面壳，实时视频、ASR/TTS 和手控/寻路都必须先有板端、云端、PC 端的契约边界。

本轮是跨 owner Epic。目标不是声明视频 RTC 已经真实可用，而是把 O7 实时链路的最小可验证基础打出来：板端能报告 RTC/媒体能力和缺口，云端能承载信令/状态契约，PC 端只消费云端契约并 fail closed。

## 2. 上轮事实和当前证据

- `OKR.md` 中 O7 当前为 0%，KR1-KR6 覆盖实时地图、电梯状态、历史回放、标注、ASR/TTS、手控/寻路。
- `docs/product/pc_tools_workstation.md` 明确当前 PC 工作站是 Node/Vue 只读 software proof，不直接控制机器人，不访问真实 ROS graph、串口或云端生产链路。
- `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER vendor 上位机参考包含 Flask、Socket.IO、`aiortc`、`/offer`、`/video_feed`、视频采集和 `audio_ctrl.py` TTS/音频播放参考，但这只是 vendor Raspberry Pi 应用资料，不等于项目 Orange Pi / ROS2 / cloud-relay 已集成。
- 项目 `cloud-relay/README.md` 当前主要覆盖 command/status/ack、phone-safe API、静态 mobile shell、生产 preflight；未看到已完成的 RTC 信令面或视频中继契约。
- 项目 `onboard/src/ros2_trashbot_vision` 已有 ROS2 camera topic consumer 和样本沉淀能力，但不是 RTC 推流服务。

## 3. 本轮 owner

- `robot-software-engineer`：板端 RTC/媒体状态 contract、ROS2/进程边界、launch/bringup 不触发真实推流的最小软件 proof。
- `robot-hardware-engineer`：Orange Pi / WAVE ROVER vendor 资料核查，摄像头、音频、CPU/资源和 vendor WebRTC/TTS 事实来源边界。
- `full-stack-software-engineer`：cloud-relay 信令/status API contract 和 PC workstation viewer/debug panel，全部走云端契约，不直连小车。
- `product-okr-owner`：阶段验收和 OKR 是否提升的最终判断，本轮默认不提升 O7 百分比，除非工程证据覆盖明确 KR 子能力。

## 4. 验收口径

- 明确回答 CEO 问题：视频 RTC 需要板端协议/服务打通，现有项目代码不足以声明“够了”。
- 给出最小板端-云端-PC 契约，覆盖视频 RTC、ASR/TTS 状态、地图/电梯/回放/标注/手控/寻路与云端接口的关系。
- 所有 UI 和 API 必须保持 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不修改 `docs/vendor/**`、不改硬件配置、不声明真实摄像头、真实麦克风、真实喇叭、真实 RTC、真实公网或真实控制已经通过。

## 5. 风险

- 如果先做 PC 端页面，会把 O7 错误推进成空心 UI。
- vendor 的 WebRTC 示例基于 Raspberry Pi 上位机应用，不能直接外推到 Orange Pi Zero 3。
- RTC 会引入公网 HTTPS/TURN/STUN、NAT、CPU 编码、摄像头独占、音频设备和隐私边界，均需要后续真实上车验证。

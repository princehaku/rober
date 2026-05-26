# O7 RTC Realtime Foundation PRD

## 1. 用户价值

PC 端运营调试平台的价值是让开发者和运营人员实时看见机器人状态、回放历史、标注数据、调试语音并通过云端发起受控操作。视频 RTC 如果没有板端和云端契约，只会变成无法落地的 PC 页面。因此本轮先建立实时媒体与调试链路的产品边界。

## 2. 目标

建立 O7 实时能力的最小产品骨架：

- 板端必须能报告实时媒体能力和缺口，而不是默认被 PC 端假设为在线。
- 云端必须定义信令/status/command draft 契约，让 PC 端不绕过云端直连小车。
- PC 端必须展示实时地图、电梯状态、历史回放、标注、ASR/TTS 和手控/寻路的最小入口，但所有入口都由后端契约驱动并 fail closed。

## 3. 非目标

- 不证明真实 WebRTC 视频已经可看。
- 不证明真实摄像头、麦克风、喇叭、Orange Pi 设备路径或 CPU 编码能力。
- 不接真实公网 HTTPS/TURN/STUN 或 production DB/queue。
- 不允许 PC 端直接访问机器人 IP、ROS graph、`/cmd_vel`、串口或 WAVE ROVER 底盘协议。
- 不更新 OKR 百分比，除非实现和验证证据足以支撑非常保守的子进度。

## 4. KR 对齐

| O7 KR | 本轮推进 | 本轮不证明 |
| --- | --- | --- |
| KR1 实时地图与机器人位置 | 定义 PC 从云端消费实时 pose/map summary 的入口和延迟字段 | 不证明真实 `/tf` 云端转发延迟 < 2 秒 |
| KR2 电梯状态展示 | 定义 elevator phase/current floor evidence/manual takeover reason 的实时和回放字段 | 不证明真实电梯门/楼层识别 |
| KR3 历史路线回放 | 定义 trajectory frames/keyframe refs/status transition 的 PC 回放 contract | 不证明云端历史库已生产可用 |
| KR4 数据标注 | 定义 annotation tasks/result draft/export readiness 字段 | 不证明真实标注服务或训练数据导出 |
| KR5 ASR/TTS | 定义 ASR stream status、TTS command draft、speaker playback acknowledgement 需要的板端/云端字段 | 不证明真实 ASR、真实喇叭播放 |
| KR6 手控/寻路 | 定义 manual control/nav goal draft 只能走云端 command API 的 contract | 不证明真实底盘运动或 Nav2 执行 |

## 5. 必须回答的产品问题

1. 视频 RTC 是否需要机器上协议打通？
   - 是。至少需要板端媒体 agent、摄像头/音频设备状态、编码/推流状态、云端信令、PC viewer 状态和错误回执。
2. 现有板子代码是否够？
   - 当前只能说 vendor 资料存在 WebRTC/TTS 参考，项目自身代码尚不足以声明 O7 RTC 打通。
3. PC 端是否可以先做？
   - 可以做 cloud-contract driven 的 fail-closed viewer/debug panel；不可以把它说成真实 RTC 或真实控制。

## 6. 验收标准

- 有工程实现或文档契约明确 `board -> cloud -> PC` 三段字段。
- PC 和 cloud 契约显式拒绝直连小车。
- 板端契约显式区分 vendor reference、project software proof、real device not proven。
- 验证命令至少覆盖 Node/Vue build/test/lint、cloud relay focused tests 或 Python compile、ROS2/package focused tests 中与改动相关的部分。
- sprint `tech-done.md` 必须记录实际改动、验证结果和剩余风险。

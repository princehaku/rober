# Sprint 2026.05.10 06-07 Side-to-side Check

## 对照检查

- 对照 OKR：本轮直接推进 Objective 3 KR3/KR5，fixed-route dry-run/status 能在运动前暴露全路线 keyframe 覆盖问题。
- 对照用户要求：功能往前走优先，测试作为护栏；本轮没有只做测试或文档。
- 对照硬件纪律：本轮未修改 WAVE ROVER、ESP32、Orange Pi、UART、GPIO、电压、波特率或底盘协议；已先读 `docs/vendor/VENDOR_INDEX.md`，没有新增硬件假设。
- 对照 sprint 留档：本轮已创建并更新 `pre_start.md`、`prd.md`、`tech-plan.md`、`tech-done.md`、`side2side_check.md`。

## 待验收

- 用户可优先看 `debug_status_file` 中的 `keyframe_preflight`，确认 route/keyframe 采集是否完整。
- 下一轮建议推进 Objective 4：将 route keyframe 写入 vision manifest，并让 operator diagnostics 直接汇总路线关键帧证据。

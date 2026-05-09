# Sprint 2026.05.10_00-01 PRD

## 需求

fixed-route dry-run 需要从“只验证路线读取”升级为“可选择验证视觉门控准入”。当用户或 launch 配置启用 `enable_visual_gate` 时，即使处于 dry-run，也必须检查当前 checkpoint 是否具备 keyframe 与 live frame 条件；条件不满足时写出等待/失败原因，不能把任务标成 completed。

## OKR 对齐

| OKR | 对齐点 |
| --- | --- |
| Objective 3 KR3 | dry-run 验证路线读取、关键帧匹配和状态输出 |
| Objective 3 KR5 | 调试状态展示当前位置、目标点、匹配状态和失败原因 |
| Objective 2 KR4 | 送达路径不能把未满足视觉准入误报为成功 |

## 用户故事

1. 作为研发，我可以在没有 Nav2/硬件时关闭 visual gate，只验证 route 文件解析和状态输出。
2. 作为研发，我可以打开 visual gate，让 dry-run 暴露 keyframe 缺失或 camera frame 缺失，而不是假成功。
3. 作为维护者，我可以从 status JSON 看到当前 checkpoint、门控状态和失败原因。

## 验收标准

- 缺 keyframe 且 `enable_visual_gate=true`：状态为 `waiting_visual_gate`，`last_error`/`failure_reason` 指向 checkpoint。
- `enable_visual_gate=false`：现有 dry-run success 流程保持可用。
- 测试覆盖上述两种路径。

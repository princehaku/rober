# O6/O7 Clean Baseline Nav2 Path Material PRD

## 用户问题

运营和研发已经有一份真实上位机 clean-baseline Nav2 no-motion path proof：首次 20s 窗口失败并定位 TF/root-cause，重试 30s 窗口成功生成 31 点 path，最终 cleanup readback 无残留进程和串口占用。但这份证据目前仍停在 sprint artifacts，不能被 O6 按 `task_id` 存档，也不能被 O7 在同一个 consumer detail 中和 route/material checklist 对齐展示。

## 目标用户

- 研发：需要知道下一次真实 route execution 前，Nav2 path generation 哪些条件已满足，哪些仍阻塞在 no-motion 边界之后。
- 运营调试：需要在 PC 端看到 first failure、retry success、path points、cleanup 和 next evidence，不再人工翻多个 artifact。
- 产品验收：需要清楚区分 preflight material、route execution、delivery success 和 hardware HIL。

## 验收口径

- O6 同一 `task_id` detail 可回读 `clean_baseline_nav2_path_material`。
- O7 consumer detail 可展示该 section，并把 status、first failure、retry success、path point count、cleanup summary、blocked reasons 和 next required evidence 用只读形式呈现。
- 对 bad schema、task mismatch、proof scope mismatch、危险 true、unsafe text/raw/base64/绝对路径/URL/token/traceback/response body，O6/O7 必须 section-local fail-closed。
- 任何情况下不得把该材料解释成 route execution success、delivery success、safe_to_control 或 primary action enabled。

## 非目标

- 不做 production cloud、DB/queue 或 OSS/CDN 实探。
- 不新增真实机器人运动、Nav2 action execution、FollowPath、controller/BT 执行或 delivery 操作。
- 不变更硬件协议、串口、WAVE ROVER 参数、launch 默认值或安全控制策略。

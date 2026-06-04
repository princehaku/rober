# Pre Start: Runtime Material Followup

## sprint_type

sprint_type: epic

## 启动原因

上一轮 `19-20_runtime-material-continue` 明确 O2/O3 仍是最低产品主线，但 Robot Software、Full-Stack、Hardware owner 因任务过宽超时。本轮继续同一方向，但把每个 owner 缩小为单一 evidence task，避免继续用大而全 prompt 消耗迭代。

## 本轮目标

- O2: 查找真实/受控电梯图片 manifest；没有则形成 blocker evidence，禁止 fixture 涨分。
- O3: SSH 上位机做非运动 ROS2/radar/map/localize readback，获得 fresh material 或明确 hook blocker。
- O7: 验证 PC same-origin operator-report readback 到真实上位机 8787。
- O1: 做 stop-first HIL preflight 和非运动 feedback material，未满足安全条件时禁止 pulse。
- O8: 收口 owner notes、evidence type 和 blocker，不让子 agent timeout 变成口头状态。

## 安全边界

本轮不执行 `/api/base/manual`、不发布 `/cmd_vel`、不发送 WAVE ROVER 运动命令、不做 forward/back/left/right pulse。Hardware 仅允许 `T=130` 非运动反馈请求，且必须写清 vendor feedback material 边界。

## 最近 blocker

- O2: 缺真实/受控电梯图片 manifest。
- O3: 上位机 ROS2 安装存在，但 runtime graph 缺 `/scan`、`/map`、AMCL、TF，live hooks 仍可能是 dry-run。
- O7: operator report write 已通，但 readback 和 PC same-origin flow 仍需复核。
- O1: 缺现场看护、物理净空、人工急停和明确授权，不能做 HIL pulse。

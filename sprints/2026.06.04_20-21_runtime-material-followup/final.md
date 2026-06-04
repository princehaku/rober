# Final: Runtime Material Followup

## sprint_type

sprint_type: epic

## 收口结论

方向判断：**继续，但产品主线只小幅推进 O7/O8；O2/O3 不涨分**。

本轮按上一轮复盘缩小 owner 粒度，四个 owner 最终都有 evidence note。O2 明确 blocked 在缺真实/受控电梯图片 manifest；O3 明确 blocked 在 live 8787 没有配置 ROS2 radar/map/localize/Nav2 hook 且 ROS graph 为空；O1 刷新了非运动 `T=130 -> T=1001` vendor feedback material；O7 新增并验证了 PC same-origin operator-report GET readback 到真实上位机 8787。

## OKR 进度

| Objective | 当前比例 | 本轮变化 | 说明 |
| --- | --- | --- | --- |
| O2：送垃圾任务 + 电梯 assisted delivery | 约 72% | 不变 | blocker 更明确：没有真实/受控图片 manifest，不能跑 OpenCV field eval。 |
| O3：建图、定位、Nav2 与固定路线 | 约 73% | 不变 | SSH/8787/ROS2 可达，但无应用 topic；hooks 为 dry-run stub。 |
| O7：PC 运营调试平台 | 约 90% | 从约 89% 小幅上调 | PC/8787 operator-report POST/GET artifact route 可读写，仍非 PC WASD/HIL。 |
| O1：硬件协议可信底盘 | 约 95.5% | 不变 | `T=130 -> T=1001` fresh material 增强，但非运动、不等于 ACK/HIL。 |
| O5：云中转控制面 | 约 84% | 不变 | 本轮未触达 production live material。 |
| O6：云端核心后端 | 约 82% | 不变 | 本轮未触达 production archive/runtime。 |
| O8：Epic 交付节奏与证据治理 | 约 42% | 从约 40% 小幅上调 | 本轮修正上一轮 owner timeout，形成完整 owner notes、evidence type 和 blocker 收口。 |

## 本轮反思

- 有效：小 owner task 比上一轮好，最终四条证据链都可审计。
- 仍需改进：Full-Stack 初始 worker 仍超时，后续 verifier 才完成收口；下一轮继续要求单命令链和单 artifact，不做宽 prompt。
- 产品判断：O2/O3 当前 blocker 已经不是“再写一点代码”能解决，必须现场采集图片或启动上位机 ROS2 runtime hook。

## 下一步

1. O3/O7：在上位机配置或启动 radar/map/localize/Nav2 hook，先拿 fresh `/scan` once/hz，再推进 `/map`、AMCL、TF。
2. O2：采集真实/受控电梯图片，回填 `trashbot.elevator_image_manifest.v1`，通过 checker 后再跑 OpenCV eval。
3. O1/O7：如果现场安全条件满足，按 stop-first HIL 做低速 pulse；否则继续明确升级 blocker，不写成 HIL pass。
4. O1/O7 接口：处理 fresh feedback endpoint 与 stale status artifact 的口径冲突，避免 PC/status 误导 operator。

## 未完成事项和风险

- 未证明真实电梯识别、楼层 OCR、进出电梯、跨楼层送达。
- 未证明 fresh ROS2 `/scan`、`/map`、AMCL、TF、Nav2 lifecycle。
- 未证明 PC WASD、底盘 HIL、robot ACK、`safe_to_control=true` 或 delivery success。
- 本轮 `o1_lidar_scan_proof_collector.py` 修复还需要同步到上位机 runtime 后才会影响 live artifact collector。

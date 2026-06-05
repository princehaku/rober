# Final: O10 AMCL/Nav2 Readiness Epic

## sprint_type

sprint_type: epic

## 收口结论

本轮 O10 Epic 取得一段有效的受控送达 readiness chain：PC proof 从 curl/API smoke 推进到浏览器按钮级 workflow，Nav2 侧新增 canonical map proof 输入护栏，电梯图片 eval 和 stop-first HIL 都收成清晰 CEO blocker。

这推动 O10 从 Path Contract 进入下一段 readiness 判断，但仍不是 AMCL/Nav2 runtime、HIL 或真实送达。

## 逐 Owner 结果

| Owner | 结果 | Evidence type | 证据 |
| --- | --- | --- | --- |
| Robot Software Engineer | Partial pass | `software_guard` | `/api/nav2/status.amcl_nav2_readiness` 只读 canonical latest JSON 和 map artifacts，输入齐备时给出 `map_inputs_ready_for_no_motion_nav2_collector`。 |
| Full-stack Software Engineer | Pass | `browser_workflow_button_level` | `pc-tools/workstation/.workstation-runtime/o7-direct-upper-browser-workflow.json` / `.png`，覆盖四个浏览器按钮动作，`safe_to_control=false` 可见。 |
| Robot Algorithm Engineer | Blocked | `blocked_with_root_cause` | 缺真实/受控电梯图片 manifest；新增 blocker artifact 和采集样本要求。 |
| Hardware Infra Engineer | Blocked | `blocked_with_root_cause` | 已读 vendor source，确认缺现场四项安全条件，不执行运动。 |

## OKR 更新

| Objective | 调整 | 理由 |
| --- | --- | --- |
| O7：PC 运营调试平台 | 约 93% -> 约 94% | browser button workflow 有 JSON/截图和 8788 live readback，已超过 curl-only。 |
| O8：Epic 交付节奏与证据治理 | 约 49% -> 约 50% | 四 owner 并行，证据类型、验证结果和 blocker 都完成收口。 |
| O10：受控送达闭环实战战役 | 约 7% -> 约 10% | browser workflow、Nav2 输入护栏、elevator/HIL 两个 blocker 和 delivery-readiness chain 成立。 |

O1/O2/O3/O5/O6/O9 保持：本轮没有 HIL、电梯真实/受控 eval、AMCL/Nav2 runtime、生产云或新的 O9 breakthrough material。

## 下一轮最高价值抓手

1. Robot Software + Algorithm：把 `amcl_nav2_readiness` 从输入护栏推进到 no-motion AMCL/Nav2 runtime collector，至少证明 map server / AMCL / planner/controller lifecycle readback。
2. CEO/现场：提供真实/受控电梯图片 manifest，解除 `blocked_missing_real_or_controlled_images`。
3. CEO/现场：提供 operator、净空、急停/断电、授权和 evidence_ref，解除 stop-first HIL gate。
4. Full-stack：保持 browser workflow，但下一轮不要再只加 readback；除非进入真实建图/定位按钮 workflow 或 HIL 现场控车边界。

## 不得越界

本轮不证明 continuous radar、AMCL/Nav2 consumption、PC WASD、HIL、robot ACK、`T=1001` 同场材料、真实电梯识别、真实跨楼层、delivery success、真实手机验收、production cloud 或 `safe_to_control=true`。

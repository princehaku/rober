# O3 No-Motion Nav2 Runtime Repair PRD

## 用户价值

普通用户最终需要的是手机或 PC 上一键发车前的可靠自动驾驶准备状态。当前真实板已经能证明 `/scan` 到位、managed map basename 可读，但 Nav2/map/AMCL runtime 没有 ready，导致无法生成同轮路线和后续送达证据。先恢复 no-motion runtime，是从诊断走向真实路线材料的必要前置。

## OKR 对齐

- 直接推进临时激活的现场 O3 验证 lane：可验证导航与固定路线。
- 间接解锁 O1 的 same-run path generation / route execution 缺口，以及 O6/O7 后续可消费的 same-task route materials。
- 不直接推进 O5。O5 只有真实 production external evidence 才能加分，本轮不再消费 support-only cloud readiness blocker。

## 需求范围

必须做到：

1. 对齐 `/api/nav2/start`、`o11_nav2_lifecycle.sh`、`autonomous.launch.py nav2_stack_only:=true` 和 `/api/nav2/proof/refresh` 的 no-motion 调用链。
2. 若发现脚本路径、默认参数、启动确认、环境变量、map 参数或 refresh body 漂移，进行最小修复。
3. 保留所有危险字段 fail-closed：`safe_to_control=false`、`delivery_success=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`。
4. 产出本地测试和真实板 artifact；真实板失败也必须给出可复核新根因。
5. 同步更新 `docs/navigation/field_route_evidence_preflight.md` 或相邻导航文档，记录新的 repair/runbook 边界。

不做：

- 不改 O5/O6/O7 relay/archive/workstation surface 合同。
- 不发真实运动命令，不执行 NavigateToPose goal，不做 delivery success 宣称。
- 不把 historical 或 cross-run path 覆盖 same-run `path_generated=false` 结论。

## 验收口径

- 本地静态/单元测试通过。
- 若真实上位机可达，必须运行 no-motion repair + refresh 链路，并把 raw/pretty/summary artifact 放入本 sprint `artifacts/`。
- 如果拿到 `path_generated=true`，只能声明 no-motion path generation/runtime proof；仍不得声明 route execution success、safe-to-control、HIL 或 delivery success。
- 如果没有拿到 `path_generated=true`，本轮价值只计为 repair/root-cause evidence，不调整 OKR 百分比。

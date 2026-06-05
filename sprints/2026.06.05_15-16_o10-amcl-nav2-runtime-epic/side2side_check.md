# Side2Side Check: O10 AMCL/Nav2 Runtime Collector Epic

## sprint_type

sprint_type: epic

## 对照结论

本轮目标是把 AMCL/Nav2 runtime 缺口落成 live 8787 可回放 blocker artifact。
实际结果符合该边界：collector、upper API route、本地测试、远端部署和 live readback
均成立，但 payload 明确是 `blocked_with_root_cause`，不是 runtime success。

| 验收项 | 结果 | 说明 |
| --- | --- | --- |
| no-motion collector | Pass | 已新增 `o10_amcl_nav2_runtime_proof.py`，只读检查 map inputs、Nav2/AMCL 包、lifecycle 和 topic 边界。 |
| upper API refresh/latest | Pass | `POST /api/nav2/proof/refresh` 与 `GET /api/nav2/proof/latest` 远端可访问，latest artifact `status=loaded`。 |
| live blocker artifact | Pass as blocked material | refresh 返回 `blocked_with_root_cause`，root causes 包含 `nav2_amcl_missing`、`nav2_planner_missing`、`nav2_controller_missing` 和 lifecycle/topic 未激活。 |
| canonical map inputs | Pass as input only | YAML/PGM 可读，source evidence 是既有 map runtime material；不证明 map quality 或可导航。 |
| no-motion 安全边界 | Pass | `safe_to_control=false`、`sends_base_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`。 |

## OKR 口径

- O10 可从约 10% 上调到约 12%：新增 no-motion AMCL/Nav2 runtime proof collector、
  8787 refresh/latest route 和 live root-cause artifact，推动 readiness chain 从输入护栏
  进入 runtime blocker 定位。
- O8 可从约 50% 上调到约 51%：Epic 证据、远端部署、root cause、不可越界和下一步 owner
  抓手完成收口。
- O3/O9 不涨：AMCL/Nav2 runtime blocked，不是 localization、path generation、
  path execution、fixed route 或新的真实材料 breakthrough。
- O7 不涨：本轮 endpoint/readback 在 upper 8787 成立，但未做 PC 端消费或 browser workflow。

## 不可外推

本轮不证明 map 可导航、AMCL localization、Nav2 path generation/path execution、HIL、
delivery success、PC WASD、WAVE ROVER ACK、真实电梯识别、真实手机验收、
production cloud 或 `safe_to_control=true`。

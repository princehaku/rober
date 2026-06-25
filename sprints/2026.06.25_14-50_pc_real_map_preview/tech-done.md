# PC Real Map Preview

sprint_type: micro

## 实际改动

- 上位机 `upper_robot_api.py` 新增只读 `/api/map/preview`：从 `runtime/maps` 内选择安全 YAML/PGM，解析 P5 PGM，并用 Python 标准库输出 PNG data URL；所有路径都限制在地图目录内。
- PC Node 代理新增 `GET /api/robot-control/map/preview?baseUrl=...`：固定转发到上位机 `/api/map/preview`，校验 PNG data URL 和危险 true 字段，响应继续固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 普通首屏地图视口优先显示真实地图图片，并新增 `刷新地图画面`；缺图或失败时继续回退到状态网格，雷达和定位 marker 仍只展示短状态。
- 同步更新 PC 产品说明和 fixed-route 工作流文档，明确该链路只读，不触发建图、Nav2、manual、keyboard、delivery 或 `/cmd_vel`。

## 验证结果

- 已通过临时本地 PGM/YAML 调用 `UpperRobotApi.map_preview("test_map")`，确认返回 `loaded`、`2x1`、PNG data URL，且安全/控制字段为 false。
- 已通过 targeted workstation 测试：`npm test -- -t "map lifecycle|renders Robot Control V1"`。
- 已通过 `python3 -m py_compile onboard/scripts/upper_robot_api.py`。
- 已通过完整 `npm test`：2 个测试文件、152 个测试全部通过。
- 已通过 `npm run lint`。
- 已通过 `npm run build`。
- 已通过 `git diff --check`。
- 已部署到真实上位机 `192.168.1.11:8787`，原脚本已备份；只读 `GET /api/map/preview` 返回 `fixed_free_cells_20260622_0112`、`256x129`、`free=394`、PNG data URL、控制/安全字段 false。
- 已重启 PC workstation 到 `0.0.0.0:7001`，只读 PC 代理 `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 返回 `preview_forwarded`、真实地图图片摘要、`hard_dangerous_true_fields=[]`。

## 剩余风险

- 该轮未自动点击真实上位机的建图、Nav2 execution、manual、keyboard、delivery 或 stop 等控制接口；真实机器人运动仍需要现场人员按安全流程确认后单独验收。
- `/api/map/preview` 当前只支持二进制 P5 PGM，若未来地图文件改成其它格式，需要扩展解析器。

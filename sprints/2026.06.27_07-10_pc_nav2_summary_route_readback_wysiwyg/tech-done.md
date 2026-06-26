# PC Nav2 Summary Route Readback WYSIWYG

sprint_type: micro

## 实际改动

- 将 `safe_command_boundary.nav2_goal_label` 的 ready 文案从“图上路线可执行”收敛为“路线读数已准备，先看地图画面”，避免 summary 在没有地图预览渲染证据时过度宣称。
- 同步更新合同类型、catalog 测试断言和 PC 工作站产品文档；普通首屏的真正 `执行图上路线` 仍由当前地图 overlay、机器人 map 位姿和安全确认共同决定。

## 验证结果

- 通过：`npm test -- --run test/catalog.test.ts`，`1 passed / 115 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 仍提示主 chunk 超过 500 kB 的既有体积警告。
- 通过：重启 `0.0.0.0:7001` 后读取 live summary，`nav2_goal_ready=true`、`nav2_goal_label=路线读数已准备，先看地图画面`、`path_point_count=36`、`robot_pose_status=map_pose_observed`、`robot_control_executed=false`。

## 剩余风险

- 本轮不执行真实 Nav2 发车、不执行自由移动；真实小车运动仍需要现场 operator 明确安全确认后再跑。

# PC Current Facts Route WYSIWYG

sprint_type: micro

## 实际改动

- 普通首屏“当前事实”的行程文案改为按真实地图画面分层：
  - 只读到 Nav2 路线读数但地图未画出当前路线时，显示“路线读数已准备，先刷新地图画面”。
  - 地图已显示当前路线但没有小车 map 位姿时，显示“图上路线已显示，先重新定位”。
  - 地图已显示当前路线且小车位置可见时，才显示“图上路线可执行”。
- 补充 App 测试，防止“路线读数已准备”再次被事实条说成“图上路线可执行”。
- 同步更新 `docs/product/pc_tools_workstation.md`，记录事实条的 WYSIWYG 边界。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts`，`1 passed / 152 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 仍提示主 chunk 超过 500 kB 的既有体积警告。
- 通过：重启 `0.0.0.0:7001` 后读取 live 状态，Node 监听 `*:7001`，`/api/health` 返回 `pc_only_readonly_workstation`；live summary 返回 `camera_status=source_first_frame_failed`、`camera_source_usage=not_in_use`、`nav2_goal_label=路线读数已准备，先看地图画面`、`path_point_count=36`、`robot_control_executed=false`。

## 剩余风险

- 本轮只修 PC 普通首屏 WYSIWYG 文案，不执行真实 Nav2 发车、不执行自由移动、不改变摄像头或雷达硬件服务。

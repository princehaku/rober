# PC keyboard chord arrows micro sprint

sprint_type: micro

## 实际改动

- 普通 PC “移动/导航”方向按钮收敛为 `↑`、`←`、`→`、`↓`，保留停止按钮；aria 与提示文案改成“上下左右 + W+A 组合转弯”。
- 前端键盘手控从单一方向改为 pressed-key set：按住会持续发送短脉冲；加按 `A`/`D` 不再先 stop，而是在下一次 pulse 中切成前进/后退 + 角速度组合。
- PC Node 固定 manual 代理新增 `linear_x_mps` / `angular_z_radps` 限幅透传；上车 `/api/base/manual` 在 ROS 模式下把可选 twist 映射为 WAVE ROVER `T=13` 的 `X` / `Z`。
- 补充 App、catalog 与上车 API 测试覆盖 W+A 连续按住、ROS twist 限幅代理和上车 `T=13` 映射。
- 同步更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`。硬件协议来源采用 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER `CMD_ROS_CTRL` / `T=13` 文档。

## 验证结果

- `npm test -- test/App.test.ts --run`：通过，244 tests passed。
- `npm test -- test/catalog.test.ts --run`：已通过，196 tests passed。
- `python3 -m unittest onboard/scripts/test_upper_robot_api_free_roam.py`：通过，Ran 14 tests，OK。
- `npm run build`：通过，Vite production build 完成；仍有既有 chunk size warning。
- 7001 工作站验证：重启 `HOST=0.0.0.0 PORT=7001 npm run api` 后，`lsof` 显示 Node 监听 `*:7001`；`GET /api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、默认小车 `http://192.168.1.11:8787`；首页 `HEAD /` 返回 200。

## 剩余风险

- 本轮完成软件与 mock/API contract 验证；真实车体 HIL 仍需在 7001 页面上按住 `W+A` 复验左转弧线运动和 stop 后静止。

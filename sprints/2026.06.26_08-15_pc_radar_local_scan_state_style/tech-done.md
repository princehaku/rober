# PC 雷达局部点云状态样式

sprint_type: micro

## 实际改动

- PC 普通首屏地图里的局部雷达点云小窗新增 `data-state=实时局部点/最近局部点`，让实时 scan 点和最近记录 scan 点在 DOM 上可直接验收。
- 前端样式新增两套局部点云状态：实时局部点保持绿色实时口径，最近局部点使用琥珀色边框、点位和虚线十字，避免 operator 把已停雷达的最近记录误看成实时扫描。
- 测试覆盖缺 map 位姿时的实时局部点和雷达已停时的最近局部点，断言 DOM 状态、点数、文案和 CSS 选择器。
- 产品文档同步记录该展示边界：只影响 PC 前端呈现，不启动雷达、不刷新 proof、不执行 Nav2/manual/keyboard/stop/delivery，也不调用 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "shows local radar scan dots instead of fake map dots when pose is missing|keeps recent local radar scan visible when lidar is currently stopped"`，`2 passed | 190 skipped`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 产物生成成功。
- 通过：`npm test`，`192 passed`。
- 通过：全量测试改写的两个旧 smoke artifact `checked_at` 已恢复到原值，未纳入本轮改动。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true`，`node ... TCP *:7001 (LISTEN)`。

## 剩余风险

- 当前仍是 PC 前端/mock 合同验证；未触发真实小车运动，未做真实 LiDAR HIL。

# PC Free Roam 下一步聚焦

sprint_type: micro

## 实际改动

- 修正 PC 普通首屏 `自由移动 / 建图` 卡片的下一步聚焦逻辑：相机或雷达未 ready、但低速自由移动可用时，`下一步：启用键盘自由移动` 聚焦自由移动键盘按钮，不再优先跳到相机探针或雷达刷新。
- 保留建图模式的原有顺序：相机和雷达都 ready、当前目标切到可建图/扫图时，下一步仍引导先开始地图记录。
- 补充 Vitest 断言，锁定相机无首帧 + 雷达未 ready 的 live 形态下，下一步聚焦键盘自由移动且不触发 manual、Nav2 或 `/cmd_vel`。
- 同步更新 `docs/product/pc_tools_workstation.md`，记录自由移动和建图验收在焦点导航上的分离。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts -t "splits free movement from mapping acceptance when camera and radar are not ready"`，1 passed、170 skipped。
- 通过：`cd pc-tools/workstation && npm test -- --run`，2 个测试文件、300 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript 与 Vite build OK；仅保留既有 chunk size warning，产物为 `assets/index-Bgk-kwwe.js` / `assets/index-DkzBjvNI.css`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`git diff --check`。
- 通过：`curl -s http://127.0.0.1:7001/ | rg -o 'assets/index-[^" ]+' || true`，7001 返回新构建资产 `assets/index-Bgk-kwwe.js` / `assets/index-DkzBjvNI.css`。

## 剩余风险

- 本轮只验证 PC 端焦点导航和 mock 回包，不触发真实小车移动，也不证明真实 wheel raw L/R 非零、Nav2 完整路线执行或 delivery success。

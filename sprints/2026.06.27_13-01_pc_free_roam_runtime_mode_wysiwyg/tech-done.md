# sprint_type: micro

## 实际改动

- 修正 PC 普通首屏 free-roam 运行态优先级：`/free-roam/autonomy/start` 已转发成功后，运行状态不再被“地图记录未启动，键盘扫图锁定”覆盖。
- 将 free-roam 启动后的地图 marker、准备卡、草图 caption 和步骤条从硬编码“自动扫图”改为按当前模式显示“自由移动”或“自动扫图”。
- 增加测试断言：当 `confirm_mapping_active=false` 的低速自由移动启动成功后，UI 必须显示“自由移动状态机已启动 / 自由移动低速运行中”，且不得显示“自动扫图状态机已启动”。
- 同步更新 `docs/product/pc_tools_workstation.md`，记录自由移动运行态和建图记录态的 WYSIWYG 分层。

## 验证结果

- `npm test -- --run App.test.ts -t "starts low-speed free roam through the fixed proxy"`：通过，1 个测试通过。
- `npm test`：通过，2 个测试文件、287 个测试通过。
- `npm run build`：通过，Vite 保留既有 chunk size warning。

## 剩余风险

- 本轮未触发真实自由移动，只验证 PC 端状态优先级和固定代理调用行为。
- 真实车是否移动仍以后端 free-roam runtime、停止兜底和 wheel/raw 或现场 HIL 证据为准。
- 摄像头 live 仍为首帧失败，因此当前真实环境仍只能按自由移动记录，不能按可验收建图收口。

# 触点性能实际交付

状态：implemented_and_verified；执行环境为 Windows 10.0.22631、Node v24.12.0、Python 3.13。所有执行均使用本地 DOM、mock fetch/媒体与可控时钟，未访问真实机器人、串口或部署环境。

## 实际改动

- PC：`pc-tools/workstation/src/App.vue`、`components/O7LiveOperatorPanel.vue`、`server/o7LiveOperatorPanel.ts`、`server/o7DirectUpperApi.ts`、`shared/contracts.ts`。Stop/Space 独立派发；manual/operator 的迟到回执无法覆盖 Stop；ACK 后后台读取状态；刷新保持 WebRTC 组件和媒体会话；同一采样生成 live/direct 摘要；HTTP 409 `serial_busy` 与 `preempted` 保留。
- PC 测试与采集：`test/App.test.ts`、新增 `test/controlStatusPerformance.test.ts`、`scripts/control-status-performance-probe.mjs`。probe 输出文件名为 `ui-performance.json` 时，依次运行 PC 与手机动态测试后生成聚合证据。
- 手机：`mobile/web/app.js`、新增 `diagnostics.js`、`index.html`、`service-worker.js`。使用顶层符号引用闭包迁移诊断声明，原 Start/Confirm/Cancel 安全表达式保留；同页按需 script 和 template 加载详情一次，核心事件不重复绑定。同一渲染周期复用派生安全输入；状态不变不重绘。前台请求结束后 2 秒读取，4 秒超时，错误退避上限 30 秒，后台中止与恢复前台立即更新；状态请求最大并发 1。控制 POST 在途期间全组动作锁定，完成后废弃旧 GET 并读取新状态，失败后的相同 JSON 也会刷新本地提示。
- 手机测试：两套 `test_mobile_web_entrypoint.py` 显式组合 core/diagnostics 源码，保留原安全断言；新增 `test_mobile_performance.mjs` 使用真实 script 元素和 ResourceLoader，在同一浏览器全局词法环境验证实际 DOM 行为。
- 同步文档：`mobile/README.md`、`docs/product/mobile_user_flow.md`、`pc_tools_workstation.md`、`docs/interfaces/o7_live_operator_panel.md`、`o7_direct_upper_pc_api.md`。

## 验证结果

| 命令 | 实际结果 |
| --- | --- |
| `npm.cmd test -- --run`，workstation 目录 | 110 / 110 passed |
| `npm.cmd run build` | passed；TypeScript、Vite 与服务端构建通过 |
| `npm.cmd run lint` | passed |
| `node scripts/control-status-performance-probe.mjs --output ../../sprints/2026.09.17_00-01_control-status-performance-epic/evidence/ui-performance.json` | exit 0；PC 7 / 7 + 手机 9 / 9，聚合 artifact 已生成 |
| `node --test mobile/web/test_mobile_performance.mjs` | 9 / 9 passed，0 skipped |
| `python -m unittest mobile.test_mobile_web_entrypoint mobile.web.test_mobile_web_entrypoint` | 415 条：405 passed、10 errors；修改前基线与最终结果一致，未增加失败、未 skip 或删除断言 |
| `git diff --check` | passed；仅 Windows LF/CRLF 提示 |

10 个已有 errors 都来自缺失的 `pc-tools/evidence/phone_browser_acceptance_gate.py` 或 `cloud_hosted_pwa_installability_gate.py`，未重建范围外历史工具。因此手机历史套件没有全绿；本轮新增行为已单独完整验证。

## 性能证据

唯一整合入口为 `ui-performance.json`，独立材料为 `ui-pc-baseline.json`、`ui-pc-performance.json`、`ui-mobile-performance.json`。PC 改前请求计数通过实际 fake fetch 观测；手机改前只保留源码结构计数，`baseline_observed=false`，无虚构前后 CPU 或动态耗时数据。

- 手机默认 JS 未压缩源码：3,931,297 → 253,304 bytes，减少约 93.6%；诊断模块 3,682,451 bytes 仅按需加载。总功能保留，未把源码体积当网络 transfer 或 CPU 降幅。
- 每次状态渲染入口的源码调用结构：215 → 14 个核心 render；默认诊断模块下载 0、重面板执行 0，实际挂载 section 为 14。相同状态连续两次读取，renderStatus 调用 0；变化状态渲染 1 次。
- 诊断重复展开：脚本加载 1 次、核心和被检查的诊断按钮监听各 1 个。下载失败可人工重试；重开详情可读；无未捕获错误。
- 手机最大状态请求并发 1、后台请求 0；POST 期间变化状态不会重开按钮，重复提交调用只产生一个 POST。动作前 GET 被中止并追加新读，旧数据迟到无效果。
- PC 每轮板端 status 请求 2 → 1；刷新媒体 unmount/close 各 0；manual/operator 未结束时 Stop 均可派发；旧响应未覆盖停车；ACK 不等状态，状态回读最大在途数 1。

## 失败定位与反思

- 诊断真实 DOM 展开暴露旧的 `normalizeList` 未定义异常；改成局部 `Array.isArray` 归一化，不扩大控制授权，完整诊断可创建。
- PC 修复 Windows/Linux 可选依赖混用、可选布尔类型和测试 lint；最后 `npm ci` 恢复锁定依赖并完整复验，package/lock 未修改。
- 手机缓存版本相关断言随新版壳同步；诊断静态脚本从宽泛 `/diagnostics` 动态匹配中明确排除，API 仍 no-store。Robot owner 负责实际静态白名单与 HTTP 测试。
- 本轮生成的 PC 临时 `.log` 已由创建者逐项删除，保留精简 md/json。未改旧未跟踪 sprint，未发现新增 TODO/FIXME，未提交或切分支。
- 新增手机调度/加载代码中文注释占非空行约 21.2%，新增行为测试约 21.1%；PC 新增代码约 20.18%。迁移的诊断历史内容未做无关重写。

## 剩余风险与验证边界

- 未测真实手机 CPU、内存峰值、实际网络压缩传输量、4G RTT、物理 Stop 时延或 HIL。软件字段和 mock 证据不表示送达完成。
- 诊断详情仍保留较大历史逻辑，打开后使用人工刷新材料快照；默认状态轮询不触发完整诊断渲染。后续可按用户价值继续淘汰历史面板。
- 手机主入口与诊断共享经典脚本词法环境，发布必须同步更新 core、diagnostics、HTML 和 service worker。诊断网络失败保留核心入口和人工重试。
- PC 状态结果仅用于展示与请求去重；过期/unknown/无反馈不得通过 HTTP 200 变成控制授权。Stop 抢占与串口顺序的真实硬件表现仍须由 Robot/HIL 验证。

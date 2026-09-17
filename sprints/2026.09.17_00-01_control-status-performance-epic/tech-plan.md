# 控制与状态性能技术计划

## 状态与实施顺序

- 状态：ready_for_implementation；前置 pre_start、PRD 已完成，2026-09-17。
- 两个独立 owner 并行；Robot 负责最终集成。计划完成即实现，无需再次请求用户确认。
- 先修采样和控制阻塞，再做状态缓存与请求合并；Full-stack 同步处理 PC 交互与手机渲染。
- 工程 owner 先记录现状，再实现、测试、修复、输出 artifact。性能结论以实测或结构性计数为准。

## Owner 与精确文件范围

| Owner | 可修改范围 | 不可修改范围 |
| --- | --- | --- |
| Robot Software Engineer | `onboard/scripts/upper_robot_api.py`、`local_webrtc_camera_smoke.py`、`test_upper_robot_api.py`、`test_local_webrtc_camera_smoke.py`；新增 `onboard/scripts/upper_robot_io.py`、`test_upper_robot_performance.py`、`control_status_performance_probe.py`；`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 仅修改 `MOBILE_WEB_STATIC_FILES`，及 `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` 对应静态入口测试；`docs/interfaces/o7_upper_robot_api.md`、`o1_upper_robot_api_base_feedback.md`、`o7_local_webrtc_camera_smoke.md`；本 sprint `evidence/robot-*` | PC/手机代码、硬件配置、其他 ROS 包、旧 sprint；remote bridge/storage 行为 |
| Full-stack Software Engineer | `pc-tools/workstation/src/` 中本次涉及的 Vue/API；`pc-tools/workstation/test/App.test.ts`、新增 `test/controlStatusPerformance.test.ts`；新增 `pc-tools/workstation/scripts/control-status-performance-probe.mjs`；必要的 `pc-tools/workstation/package.json` 与锁文件；`mobile/web/app.js`、`index.html`、`styles.css`、`service-worker.js`、新增 `diagnostics.js` 与 `test_mobile_performance.mjs`；`mobile/web/test_mobile_web_entrypoint.py`、`mobile/test_mobile_web_entrypoint.py`；`mobile/README.md`、`docs/product/mobile_user_flow.md`、`docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_live_operator_panel.md`、`o7_direct_upper_pc_api.md`；本 sprint `evidence/ui-*` | Robot owner 文件，包括静态托管器；其他范围外文件 |
| Product / 主节点 | 本 sprint 计划与后续收口文档；OKR 更新须待工程证据与另行派单 | 产品、测试、硬件配置 |

你与其他 owner 共享代码库，不回滚他人改动。新增/修改技术注释使用中文，有意义的中文注释比例超过 20%。

## 方案与接口边界

1. 串口阻塞工作移出 async handler 的事件循环。单进程单串口仲裁，受控后台执行完整动作：方向写入、可中断 pulse、finally 停车、至多 50ms 短片反馈。Stop 抢占普通反馈等待；非 Stop 并发 busy 拒绝，不积压旧运动。显式停止取消尚未完成的点动，Stop 后旧运动不再写。请求取消与异常都不能跳过停车。收到有效反馈及时结束普通请求；完整采样保留独立入口。保留所有限速、时限、自动停车和错误反馈。
2. CPU 采样复用 psutil Process，预热与有效数据区分；进程失效重建，不伪造 0% 有效样本。
3. 摄像头健康独立采集，状态 GET 读取带采样时间的缓存；冷启动/过期/异常明确标注，不沿用旧成功授权控车。保持旧字段兼容，新增可选 freshness/采样时间字段由 Robot 在 docs 与 artifact 记下准确名称并告知 Full-stack。
4. PC 单次刷新共用状态 promise/结果；忙碌状态不卸载 WebRTC；Stop 不受普通动作 busy gate 阻塞，状态回读移出动作确认关键链。
5. 手机任务与核心安全状态走轻量主路径；诊断采用 `diagnostics.js` classic script 按需加载一次，按依赖闭包拆分，不复制安全 gate。共用派生状态并跳过未变化渲染。自动刷新单实例、无重叠、后台暂停；动作后的刷新并入同一调度源。分模块后同时更新缓存版本与静态资产清单，Robot 为 `diagnostics.js`/实际存在的 `state-poll.js` 同步托管白名单。
6. 保持端点 URL、动作请求与 ACK 语义；禁止把 accepted 当 delivery success。缓存新增字段为可选，老消费者保持可用。

## 实施入口校正（2026-09-18）

- 草案白名单名称 `MOBILE_WEB_ASSETS` 更正为源码已有的 `MOBILE_WEB_STATIC_FILES`；变更仅新增 `diagnostics.js` 托管入口。
- 手机动态测试最终采用 `test_mobile_performance.mjs`，替代草案名称 `test_mobile_runtime.cjs`；轮询留在 `app.js`，无需新增 `state-poll.js`。
- PC 测试实际位于 `test/`，明确纳入 `App.test.ts` 和新增 `controlStatusPerformance.test.ts`。
- 性能 probe 固定原始基线 SHA，避免提交后默认 HEAD 漂移；PC 独立证据与聚合证据使用不同输出名。采样次数为每组 10 次，camera cold start 单独 1 次。
- Python 性能探针走直接 API + fake UART/camera，未包含 HTTP 传输；HTTP 并发正确性由独立工程测试覆盖。以下命令是最终可复跑入口。
- Robot 与 Full-stack 仍为两个责任 owner；Robot 内部分派 CPU 采样，Full-stack 内部分派 PC，责任 owner 分别集成并冻结证据。
- 实际可选字段：camera `sampled_at_ms/sample_age_ms/stale/refreshing`；CPU `sample_window_ms/sampled_monotonic_s` 与无有效样本时的 `available=false/reason=warming_up`；PC envelope `upper_accepted/preempted/upper_error` 和 live panel 的 `direct_upper_status`。普通动作并发使用 HTTP 409 `serial_busy`，被抢占动作保留 accepted 并追加 `preempted=true`，消费者显示中断原因。
- PC 聚合采用同一在途采样，不引入 TTL 或跨请求状态缓存；独立 status 入口继续读取新数据。

## 验收命令

仓库根目录，由 Robot owner 执行：

```powershell
python -m unittest onboard.scripts.test_upper_robot_api onboard.scripts.test_local_webrtc_camera_smoke
python -m unittest onboard.scripts.test_upper_robot_performance
python -m unittest discover -s onboard/scripts -p 'test_*.py'
python onboard/scripts/control_status_performance_probe.py --baseline-ref 869dfe5aaf95bcd1759583752a1a433b9ff1e83c --samples 10 --output sprints/2026.09.17_00-01_control-status-performance-epic/evidence/robot-performance.json
```

`pc-tools/workstation/` 目录，由 Full-stack owner 执行：

```powershell
npm test -- --run
npm run build
npm run lint
node scripts/control-status-performance-probe.mjs --output ../../sprints/2026.09.17_00-01_control-status-performance-epic/evidence/ui-pc-performance.json
node scripts/control-status-performance-probe.mjs --output ../../sprints/2026.09.17_00-01_control-status-performance-epic/evidence/ui-performance.json
```

仓库根目录，由 Full-stack owner 执行：

```powershell
python -m unittest mobile.test_mobile_web_entrypoint mobile.web.test_mobile_web_entrypoint
node --test mobile/web/test_mobile_performance.mjs
git diff --check
```

新增 probe 必须可离线使用 fake serial/fake camera/fake fetch，不接真实设备。若 unittest 受模块导入环境限制，owner 记录等价执行入口与原因；失败先定位修复，范围外既存失败单独列证据。

## 性能与正确性证据

- Robot artifact：baseline/after 的普通有效反馈等待、慢反馈 Stop 排队/写入延迟、事件循环 heartbeat 最大间隙、状态 GET 延迟；用明确延迟的 fake serial/camera 重复采样，输出次数及 p50/p95/p99。CPU 采样给出对象创建次数、预热次数和有效样本数。
- UI artifact：单次刷新请求计数 baseline/after、WebRTC mount/unmount 数、Stop 在普通动作未返回时是否发出；手机默认重面板调用数、诊断展开后的可用性、状态未变化渲染次数和轮询最大并发。
- 结构性硬门槛：默认重面板执行为 0；状态刷新不销毁既有视频会话；状态轮询最大并发为 1；Stop 不等待整个普通反馈窗口；事件循环可持续服务；CPU 连续采样对象可复用。
- 时延数值用于本地软件比较；记录运行环境和注入条件，不将其作为实机停止时延或手机 CPU 降幅。
- 集成：Robot 等待 UI owner 返回实际变更与证据，再确认旧 payload、安全字段与缓存字段兼容；发现失败交原 owner 修复后复验。

## 风险与验收围栏

- 并发串口可能引入乱序/读错归属；用慢反馈、Stop、并发点动、请求取消、超时与异常测试守住顺序和自动停车，并验证 Stop 后旧运动不再写。外部驱动对同一串口的竞争不在 mock 证据范围内。
- 缓存必须可见采样年龄，过期不显示为新鲜硬件证据；后台采集任务需要生命周期退出处理。
- 手机现有静态合同测试较多；保留入口与语义，更新只能针对结构迁移，不删除安全断言。
- 不打开真实串口、不执行真实控车、不部署。mock 软件证据不等于 HIL、4G、手机真机、ROS runtime 或送达成功。
- 无实机材料不作为本轮 blocked 结论；剩余风险进入 final，避免再次消费旧 blocker。

## OKR 最低优先级核对

`OKR.md` 4.1 当前最低为 **O10，约 12%**；其次 O9 约 22%、O8 约 51%。本轮直接面向 O7 控制与触点性能，并支撑 O10 后续操作链质量。优先级调整依据是 CEO 明确要求落实性能首批。O10 的 Nav2 runtime、真实图片与 HIL 保持原验收要求；本轮 mock 性能不提高任何产品 Objective 百分比。final 必须复核这一理由及证据边界。

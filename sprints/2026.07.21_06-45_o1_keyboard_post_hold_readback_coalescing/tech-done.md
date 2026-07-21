# O1 Keyboard Post-Hold Readback Coalescing - Tech Done

## Sprint metadata

- `sprint_type: micro`
- Owner：`full-stack-software-engineer`
- 状态：`complete_software_and_loopback_browser_proof`
- 证据边界：`real_in_app_chromium_to_loopback_mock_upper_only`
- `loopback_mock_only=true`
- `live_nonzero=0`
- `physical_latency_not_measured=true`
- `hil_pass=false`
- `safe_to_control=false`

## 实际改动

键盘 release stop 仍立即发送且等待 stop 回包；成功后 UI 立即保留 `stop_sent:*`。原先同步执行的轮速样本和全量
summary 改成 `400 ms` idle-debounce：每个快速 release 只推后 timer，新 keydown、地址切换或卸载会取消尚未开始的
批次并让 running 批次的 generation 失效。慢 readback 不能阻塞下一次 manual/stop，也不能覆盖新的 hold 状态。

readback 的 scheduled/running/completed/failed/superseded 状态与 stop 结果分开。只读失败显示结构化原因，但成功 stop
不会降级为停止失败；手动“复查手控条件”成功后可以恢复。blur、page hidden、pointer cancel/leave 和卸载仍先走 stop，
卸载仅取消只读 timer。普通页新增 `data-post-hold-readback-*` 属性和独立状态文案，原
`post_hold_summary_refresh_required=true` 合同保持不变。

测试新增 deterministic 100-cycle、running stale generation、只读失败恢复和 unmount stop/timer 边界，并把三项旧的
同步读回断言改为显式 `scheduled -> 400 ms -> completed`。产品设计文档同步了执行时机、数据属性和证据边界。

## 验证结果

- 定向：46 passed、209 skipped、0 failed；覆盖 keyboard/manual/stop/watchdog/coalescing/pointer、blur、page hidden、unmount。
- 完整单测：5 files、539/539 passed，45.75 s。
- 构建：TypeScript app + Vite（34 modules）+ TypeScript server 通过；仅保留既有的大 chunk warning。
- Lint：ESLint 通过。
- deterministic 100-cycle：manual=100、stop=100；400 ms idle 前 feedback/summary 增量均为 0，idle 后完整批次=1；
  新 hold 让旧 running generation 的 UI 写入=0。
- 按 `git diff --unified=0` 统计新增 Vue 非空行 170，其中中文技术注释 37 行，增量注释比例 21.76%。

真实 in-app Chromium 使用完全隔离拓扑 `15174 -> 17002 -> 18082`，从 raw/guard 0 行开始采样。10 个 reload-level
cold 与同页 100 个 warm 全部回到“已停止”；raw 中 manual=110、stop=110、cold=10、warm=100、unique trace=110，
manual/stop 顺序配对通过，parse error/dropped/non-loopback 均为 0。

`keydown -> mock Upper ingress` 的 cold p50/p95/max 为 `2.800/4.000/4.000 ms`，warm 为
`2.100/2.600/8.200 ms`，继续通过 `p50 <= 10 ms`、`p95 <= 20 ms`。PC guard -> mock ingress 的 warm
p50/p95/max 为 `0/1/6 ms`，mock ingress -> body parsed 为 `0.083/0.112/0.170 ms`。

warm 100 轮的 support readback 区间分布从基线 total `4158`、p50 `45`、p95 `46`、mean `41.58` 降至
total `1024`、p50 `8`、p95 `9`、mean `10.24`，分别下降 `75.37%/82.22%/80.43%/75.37%`。完整
post-hold 批次共 2 个：cold 最后一轮空闲后 1 个、warm 最后一轮空闲后 1 个；rapid warm 中间没有逐 tap 启动完整批次。

## 失败定位与修复

新增测试首轮有两项因精简 feedback fixture 缺 `sample_key_values` 失败，补为完整安全 0/0 fixture 后通过；三个旧测试
仍期待 keyup 同步读回，改为 fake timer 的 scheduled/400 ms 断言后定向和 full 全绿。

第一轮浏览器 after 采样期间发生纯注释 HMR，导致同页 warm 第一轮 trace 被重新标为 cold（11/99），故明确排除。
随后复用 15173 的 after_v2 又被旧标签自动重连，在零行 gate 前产生 134 行背景请求，也明确排除。最终 after_v2b
改用独立 `15174/17002/18082`，从零行开始且整个采样期间代码/文档冻结，得到有效 10/100 证据。

验证结束后向三个精确受控会话发送 SIGINT；15174/17002/18082 listener 均为 0，现场 `192.168.1.11` 活动连接为 0，
原 7001 PID `21549` 未停止、未重启。两个测试机械更新的历史 smoke `checked_at` 已在主节点明确授权后用 apply_patch
精确恢复，相关路径最终无 diff。

## 剩余风险

本轮只证明真实浏览器到本机 loopback mock 的请求时序、前端并发安全和 support readback 降噪。没有触达 SSH、ROS、
UART、WAVE ROVER、电机或轮子；没有测量现场 Wi-Fi、Upper、bridge、ESP32 和物理轮子 onset，因此不能宣称现场端到端
“按键到轮动”已经改善。`robot_control_executed=false`、`hil_pass=false`、`safe_to_control=false`、
`route_execution_success=false`、`delivery_success=false`；O1/KR 不因本轮软件证明提升或归档。

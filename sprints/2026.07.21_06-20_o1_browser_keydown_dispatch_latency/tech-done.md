# O1 Browser Keydown Dispatch Latency - Tech Done

## Sprint metadata

- `sprint_type: micro`
- Owner：`full-stack-software-engineer`
- 状态：`complete_loopback_browser_profile`
- 证据边界：`real_in_app_chromium_to_loopback_mock_upper_only`
- `loopback_mock_only=true`
- `live_nonzero=0`
- `physical_latency_not_measured=true`
- `hil_pass=false`
- `safe_to_control=false`

## 实际改动

本轮仅在当前 sprint 新增隔离 fixture、raw/guard/summary、进程安全 manifest 与本 `tech-done.md`。没有修改产品源码、
测试、`docs/`、OKR 或其它 sprint；没有停止或重启现有 7001 PID `21549`。

隔离拓扑使用真实当前产品代码：in-app Chromium → Vite `127.0.0.1:15173` → 当前 Node PC API
`127.0.0.1:17001` → 只记录请求的 mock Upper `127.0.0.1:18081`。Fixture Vite resolve hook 只在本轮进程中把
产品默认上位机地址覆盖为 `http://127.0.0.1:18081`；PC 进程另有 fetch guard，任何非 loopback 上游都会 fail closed
并留痕。Mock 不导入 ROS/串口/硬件包，所有危险证据字段固定 false。

## 真实浏览器采样

主节点通过 browser skill 连接真实 in-app Chromium，以 DOM snapshot 和唯一 locator 核对：

- `[data-testid=robot-api-default-address]` 显示 `127.0.0.1:18081`；
- 首屏 `data-open-page-safety-mode=site_safe_by_default`，当前产品安全确认是默认 true，visible checkbox count 为 0；
- `[data-testid=keyboard-control-panel]` 进入 armed/等待按键态；
- 使用真实 browser keyboard `press('w')` 产生 keydown+keyup，每轮等待 `[data-testid=keyboard-live-status]` 回到“已停止”。

样本共 110 轮：10 个 reload-level cold（不是 10 个独立 Chromium process）与同页 100 个 warm。Raw 中 manual=110、
stop=110；每一对满足 `manual_i < stop_i < manual_i+1`。110 个 trace id 全部唯一，schema、browser timeOrigin、
keydown perf、hold session/sequence 完整且和实际 hold identity 一致；errors=0、dropped=0。

## 延迟结果与瓶颈判断

`keydown -> mock Upper ingress` 同机 wall envelope：

| 样本 | n | p50 | p95 | max |
| --- | ---: | ---: | ---: | ---: |
| cold reload-level | 10 | 2.500 ms | 3.200 ms | 3.200 ms |
| warm | 100 | 0.500 ms | 1.100 ms | 14.800 ms |

Warm p50 `0.500 ms <= 10 ms`、p95 `1.100 ms <= 20 ms`，目标全部通过。PC fetch guard 到 mock ingress 的
warm p50/p95/max 为 `0/1/1 ms`；mock ingress 到 JSON body parse 的 warm p50/p95/max 为
`0.078/0.123/0.155 ms`。因此 browser/PC loopback 主路径不是当前“按下后轮子明显晚动”的主要瓶颈。

唯一 warm max `14.800 ms` 出现在 trace `5d9666ee-d167-403d-ac1a-253372405c97`；同次 PC fetch guard → mock
ingress 为 `0 ms`、mock body parse 为 `0.072 ms`，所以该离群点发生在 PC outbound guard 之前的组合区间（browser
事件/请求构建、fetch 调度、Vite proxy 或 PC ingress/validation），但当前证据不能再可靠拆分，不能猜成其中某一层。
100 个 warm 的 p95 仍只有 1.100 ms。

Browser-side `keydown -> fetch dispatch` 没有单独报告精确分位数：raw payload 有 browser 同 clock 的 keydown 点，但本轮未
冻结与 trace 一一对应的 browser Resource Timing fetch start 点。用 browser wall 与 Node `Date.now` 倒算会出现约 1 ms
量化误差甚至小负值，不满足“同一 clock 可靠取得”的条件。完整 browser→mock envelope 已覆盖该段且仍显著低于目标。

## 验证结果

- Fixture `.mjs` 静态语法检查：PASS；Vite/PC/mock health 与端口/PID gate：PASS。
- 真实 in-app Chromium DOM/locator、keydown/keyup、reload cold 与 warm 采样：PASS。
- Raw JSONL 7038 行逐行 parse：PASS；其中 manual 110、stop 110、support readback 6818。
- Network guard JSONL 7038 行逐行 parse：PASS；host 仅 `127.0.0.1`，non-loopback=0。
- Summary/process manifest JSON parse：PASS；trace uniqueness、manual/stop pairing、threshold、errors/dropped gate：PASS。
- 采样前后 `192.168.1.11` 活动连接均为 0；SSH/ROS/UART/Nav2/route 均为 0。
- 精确 SIGINT 清理后 15173/17001/18081 listener 均为 0；7001 仍是 PID `21549`。

## 失败、修复与剩余风险

- 本子会话最初没有可用 iab，因此没有换 Playwright/jsdom 冒充；由已连接 iab 的主节点完成真实 Chromium 交互。
- 第一轮后台 shell 启动的 fixture 被执行环境随 shell 回收；改为三个受控长会话后 health/端口稳定，采样使用的是修复后的
  PID `46521/46645/46522`。一次直接探测 Vite `/@fs/` 被 allow-list 返回 403；随后通过实际编译模块 import 路径确认
  loopback override，产品页面本身正常返回 200。
- 页面背景只读刷新产生 6818 条 support readback；它没有造成 manual/stop drop，warm p95 仍为 1.100 ms，但可能增加
  调度噪声。仅凭一个 14.800 ms 离群点不能证明其因果关系。
- 本轮只证明 browser/PC 本机链路，不覆盖现场 Wi-Fi、Upper 进程、bridge HTTP、ESP32、UART、电机驱动或轮子起转；
  `physical_latency_not_measured=true`，不能据此声明现场端到端延迟已经优化。
- `live_nonzero=0`、`robot_control_executed=false`、`hil_pass=false`、`safe_to_control=false`、
  `route_execution_success=false`、`delivery_success=false`；O1 不因本轮提升，KR 不归档。

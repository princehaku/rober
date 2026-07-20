import type { RobotControlLatencyTrace, RobotControlPcLatencyTiming } from "../shared/contracts";

export const ROBOT_CONTROL_LATENCY_TRACE_SCHEMA = "trashbot.keyboard_wheel_latency_trace.v1" as const;

// trace 只接受短、可打印的关联键；它不是授权 token，也不能携带 URL 或任意日志文本。
const SAFE_TRACE_TOKEN = /^[A-Za-z0-9._:-]+$/;
const TRACE_ID_MAX_LENGTH = 96;
const SESSION_ID_MAX_LENGTH = 96;

function safeToken(value: unknown, maxLength: number): string | null {
  // 统一白名单可避免代理反射控制字符、超长 body 或敏感 endpoint。
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim();
  return normalized.length > 0 && normalized.length <= maxLength && SAFE_TRACE_TOKEN.test(normalized)
    ? normalized
    : null;
}

function finiteNonNegative(value: unknown): number | null {
  // 时间值只做本进程关联，不参与跨机裸相减；负数和非有限数直接拒绝。
  return typeof value === "number" && Number.isFinite(value) && value >= 0 ? value : null;
}

export function normalizeRobotControlLatencyTrace(value: unknown): RobotControlLatencyTrace | null {
  // 缺 envelope 保持旧客户端兼容；一旦提交 envelope，则必须完整通过固定 schema 校验。
  if (value === undefined || value === null) {
    return null;
  }
  if (typeof value !== "object" || Array.isArray(value)) {
    throw new Error("latency_trace_invalid_object");
  }
  const payload = value as Record<string, unknown>;
  const latencyTraceId = safeToken(payload.latency_trace_id, TRACE_ID_MAX_LENGTH);
  const holdSessionId = safeToken(payload.hold_session_id, SESSION_ID_MAX_LENGTH);
  const keydownPerfMs = finiteNonNegative(payload.client_keydown_perf_ms);
  const timeOriginMs = finiteNonNegative(payload.client_time_origin_ms);
  const holdSequence = finiteNonNegative(payload.hold_sequence);
  const sampleKind = payload.sample_kind;
  if (
    payload.schema !== ROBOT_CONTROL_LATENCY_TRACE_SCHEMA
    || !latencyTraceId
    || !holdSessionId
    || keydownPerfMs === null
    || timeOriginMs === null
    || holdSequence === null
    || !Number.isInteger(holdSequence)
    || holdSequence > 1_000_000_000
    || (sampleKind !== "cold" && sampleKind !== "warm")
  ) {
    throw new Error("latency_trace_invalid_fields");
  }
  // 未知字段有意丢弃，防止 trace 被扩成任意数据回显通道。
  return {
    // schema 固定后，Upper 可以拒绝未来不兼容 envelope，而不猜字段含义。
    schema: ROBOT_CONTROL_LATENCY_TRACE_SCHEMA,
    // trace id 只负责把各段 artifact 关联起来，不能作为控制授权。
    latency_trace_id: latencyTraceId,
    // keydown 点位属于 browser performance clock，只能在浏览器作用域内求差。
    client_keydown_perf_ms: keydownPerfMs,
    // timeOrigin 供离线关联和校时诊断，不承诺与 Node/Upper 墙钟一致。
    client_time_origin_ms: timeOriginMs,
    // session/sequence 让 trace 与现有 watchdog 顺序合同对齐，不能另起运动语义。
    hold_session_id: holdSessionId,
    hold_sequence: holdSequence,
    // cold/warm 必须分账，避免首次加载开销污染稳定热路径分位数。
    sample_kind: sampleKind,
  };
}

export function monotonicNs(): bigint {
  // Node 只使用单调时钟计算本进程 span，不和浏览器或 upper 的 monotonic 值直接相减。
  return process.hrtime.bigint();
}

function spanMs(start: bigint, end: bigint): number {
  // 纳秒先相减再转毫秒，避免把大整数直接转 Number 丢失差值精度。
  return Number(end - start) / 1_000_000;
}

export function buildPcLatencyTiming(input: {
  receive: bigint;
  validationDone: bigint;
  forwardStart: bigint;
  upstreamHeaders: bigint;
  responseDone: bigint;
}): RobotControlPcLatencyTiming {
  // 对外同时给作用域明确的原始字符串和已经计算好的 local spans。
  return {
    // clock_id 明确限制所有原始 ns 点位的可比较范围。
    clock_id: "node_process_hrtime",
    // receive 与 validation 覆盖 body 进入代理后到白名单校验完成。
    pc_receive_mono_ns: input.receive.toString(),
    pc_validation_done_mono_ns: input.validationDone.toString(),
    // forward 点位紧贴固定 upstream fetch，不包含只读 summary/readback。
    pc_forward_start_mono_ns: input.forwardStart.toString(),
    // headers 与 done 分开，便于识别网络等待还是 JSON 解析拖慢回包。
    pc_upstream_headers_mono_ns: input.upstreamHeaders.toString(),
    pc_response_done_mono_ns: input.responseDone.toString(),
    // 这些 span 已在同一 hrtime clock 内相减，调用方无需处理 BigInt。
    pc_receive_to_validation_ms: spanMs(input.receive, input.validationDone),
    pc_validation_to_forward_ms: spanMs(input.validationDone, input.forwardStart),
    // forward-to-headers 仍包含 PC 到 Upper 的网络往返一部分，不冒充单向耗时。
    pc_forward_to_headers_ms: spanMs(input.forwardStart, input.upstreamHeaders),
    // headers-to-done 只表示 PC 读取/解析响应的本地可观察窗口。
    pc_headers_to_response_done_ms: spanMs(input.upstreamHeaders, input.responseDone),
    // proxy total 是 Node receive 到完整 upstream response，仍不是 wheel onset。
    pc_proxy_total_ms: spanMs(input.receive, input.responseDone),
  };
}

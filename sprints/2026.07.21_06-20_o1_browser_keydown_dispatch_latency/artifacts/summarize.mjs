import fs from "node:fs";

const [rawPath, guardPath, outputPath] = process.argv.slice(2);
if (!rawPath || !guardPath || !outputPath) {
  throw new Error("usage: node summarize.mjs RAW_JSONL NETWORK_GUARD_JSONL SUMMARY_JSON");
}

const lines = fs.readFileSync(rawPath, "utf8").split(/\r?\n/).filter(Boolean);
const records = lines.map((line, index) => {
  try {
    return JSON.parse(line);
  } catch (error) {
    throw new Error(`invalid_jsonl_line_${index + 1}:${error instanceof Error ? error.message : "parse_failed"}`);
  }
});
const manual = records.filter((record) => record.kind === "manual");
const stop = records.filter((record) => record.kind === "stop");
const guardLines = fs.readFileSync(guardPath, "utf8").split(/\r?\n/).filter(Boolean);
const guardRecords = guardLines.map((line, index) => {
  try {
    return JSON.parse(line);
  } catch (error) {
    throw new Error(`invalid_guard_jsonl_line_${index + 1}:${error instanceof Error ? error.message : "parse_failed"}`);
  }
});
const manualForwards = guardRecords.filter((record) => new URL(record.url).pathname === "/api/base/manual");

function percentile(values, fraction) {
  if (values.length === 0) {
    return null;
  }
  const sorted = [...values].sort((left, right) => left - right);
  return sorted[Math.min(sorted.length - 1, Math.ceil(sorted.length * fraction) - 1)];
}

function stats(values) {
  // nearest-rank 与目标 p50/p95 口径一致；保留三位小数即可区分浏览器/代理级毫秒差。
  const finite = values.filter(Number.isFinite);
  return {
    count: finite.length,
    p50_ms: percentile(finite, 0.50),
    p95_ms: percentile(finite, 0.95),
    max_ms: finite.length ? Math.max(...finite) : null,
  };
}

function browserToMockEnvelope(record) {
  // 同机 wall envelope 用 timeOrigin+keydown perf 对齐 ingress wall；它包含 wall-clock 不确定性，不是单调时钟 span。
  const trace = record.latency_trace;
  if (!trace || !Number.isFinite(trace.client_time_origin_ms) || !Number.isFinite(trace.client_keydown_perf_ms)) {
    return null;
  }
  return record.ingress_wall_ms - (trace.client_time_origin_ms + trace.client_keydown_perf_ms);
}

const samples = manual.map((record) => ({
  sequence: record.sequence,
  trace_id: record.latency_trace?.latency_trace_id ?? null,
  sample_kind: record.latency_trace?.sample_kind ?? null,
  hold_session_id: record.hold_session_id,
  hold_sequence: record.hold_sequence,
  browser_to_mock_wall_envelope_ms: browserToMockEnvelope(record),
  mock_ingress_to_body_parsed_ms: record.ingress_to_body_parsed_ms,
  // 两个 Node 进程共用本机 wall clock；该差值只作为 loopback forward envelope，不是单向网络真值。
  pc_fetch_guard_to_mock_ingress_wall_ms: manualForwards[manual.indexOf(record)]
    ? record.ingress_wall_ms - manualForwards[manual.indexOf(record)].at_ms
    : null,
}));
const cold = samples.filter((sample) => sample.sample_kind === "cold");
const warm = samples.filter((sample) => sample.sample_kind === "warm");
const traceIds = manual.map((record) => record.latency_trace?.latency_trace_id).filter(Boolean);
const parseErrors = records.filter((record) => record.parse_error);
const nonLoopback = guardRecords.filter((record) => record.allowed !== true);
const paired = manual.length === stop.length && manual.every((record, index) => (
  stop[index]?.sequence > record.sequence
  && (index + 1 >= manual.length || stop[index].sequence < manual[index + 1].sequence)
));
const expectedManualCount = 110;

const summary = {
  schema: "trashbot.o1.browser_keydown_dispatch_latency.summary.v1",
  generated_at: new Date().toISOString(),
  source: "real_in_app_chromium_to_loopback_mock_upper",
  loopback_mock_only: true,
  counts: {
    raw_records: records.length,
    manual: manual.length,
    stop: stop.length,
    support_readback: records.length - manual.length - stop.length,
    cold: cold.length,
    warm: warm.length,
    unique_trace_ids: new Set(traceIds).size,
    duplicate_trace_ids: traceIds.length - new Set(traceIds).size,
    parse_errors: parseErrors.length,
    guard_records: guardRecords.length,
    manual_forward_guard_records: manualForwards.length,
    non_loopback_guard_records: nonLoopback.length,
  },
  browser_to_mock_wall_envelope: {
    cold: stats(cold.map((sample) => sample.browser_to_mock_wall_envelope_ms)),
    warm: stats(warm.map((sample) => sample.browser_to_mock_wall_envelope_ms)),
    clock_boundary: "browser performance.timeOrigin+performance.now versus mock Date.now on the same Mac",
    uncertainty: "Includes browser event handling, request construction, fetch scheduling, Vite proxy, PC validation/forwarding, loopback transport, and wall-clock alignment uncertainty; it is not physical wheel latency."
  },
  mock_ingress_to_body_parsed: {
    cold: stats(cold.map((sample) => sample.mock_ingress_to_body_parsed_ms)),
    warm: stats(warm.map((sample) => sample.mock_ingress_to_body_parsed_ms)),
  },
  pc_fetch_guard_to_mock_ingress_wall_envelope: {
    cold: stats(cold.map((sample) => sample.pc_fetch_guard_to_mock_ingress_wall_ms)),
    warm: stats(warm.map((sample) => sample.pc_fetch_guard_to_mock_ingress_wall_ms)),
    clock_boundary: "PC guard Date.now versus mock Upper Date.now on the same Mac",
  },
  threshold: {
    warm_p50_target_ms: 10,
    warm_p95_target_ms: 20,
    warm_p50_pass: warm.length > 0 && stats(warm.map((sample) => sample.browser_to_mock_wall_envelope_ms)).p50_ms <= 10,
    warm_p95_pass: warm.length > 0 && stats(warm.map((sample) => sample.browser_to_mock_wall_envelope_ms)).p95_ms <= 20,
  },
  integrity: {
    trace_unique: traceIds.length === new Set(traceIds).size,
    all_manual_have_trace: traceIds.length === manual.length,
    manual_stop_ordered_pairing_pass: paired,
    manual_stop_pairing_note: "Each keydown cycle is paired when manual_i < stop_i < manual_i+1; stop intentionally has no latency trace envelope.",
    dropped: Math.max(0, expectedManualCount - manual.length),
    errors: [
      ...parseErrors.map((record) => ({ sequence: record.sequence, error: record.parse_error })),
      ...(manual.length === expectedManualCount ? [] : [{ error: `manual_count_expected_${expectedManualCount}_actual_${manual.length}` }]),
      ...(stop.length === expectedManualCount ? [] : [{ error: `stop_count_expected_${expectedManualCount}_actual_${stop.length}` }]),
      ...(paired ? [] : [{ error: "manual_stop_ordered_pairing_failed" }]),
      ...(nonLoopback.length === 0 ? [] : [{ error: `non_loopback_guard_records_${nonLoopback.length}` }]),
    ],
  },
  samples,
};

fs.writeFileSync(outputPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
process.stdout.write(`${JSON.stringify(summary.counts)}\n`);

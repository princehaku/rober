# Agent Proactive KR Reward Rule Tech Done

## Sprint Type

sprint_type: micro

## Actual Changes

- Updated `AGENTS.md` with a repo-wide proactive discovery and KR reward rule:
  - Agents are encouraged to discover problems before the CEO, fix them, propose new verifiable KR, and push Objective progress.
  - New KR proposals must include Objective mapping, user value, owner, acceptance command/evidence, evidence boundary, and risk/decision needs.
  - Unverified ideas may be recorded as suggestions or candidate KR, but cannot raise completion percentage.
- Updated `docs/process/iteration_velocity.md` with a dedicated `主动发现与 KR 奖励机制` section and synchronized reference consistency rules.
- Updated `.codex/registry.toml` with machine-readable `proactive_reward` and `proactive_kr_reward_rule` fields plus a new red-line entry.
- Updated all five `.codex/agents/*.toml` role prompts so Product/OKR Owner and every L2 engineer share the same proactive KR incentive boundary.

## Verification

- `git diff --check -- AGENTS.md docs/process/iteration_velocity.md .codex/registry.toml .codex/agents/*.toml sprints/2026.06.04_10-11_agent-proactive-kr-reward-rule/tech-done.md`
  - Result: passed with no whitespace errors.
- `python3 - <<'PY' ... tomllib.load(...) ... PY` for `.codex/registry.toml` and all `.codex/agents/*.toml`.
  - Result: passed; parsed `.codex/registry.toml` and all five role TOML files.
- `rg -n "主动发现与 KR 奖励机制|proactive_kr_reward_rule|优厚奖励|候选 KR" AGENTS.md docs/process/iteration_velocity.md .codex/registry.toml .codex/agents sprints/2026.06.04_10-11_agent-proactive-kr-reward-rule/tech-done.md`
  - Result: passed; confirmed the rule appears in `AGENTS.md`, process rules, registry, all five agent prompts, and this sprint record.

## Remaining Risks

- This is a process and agent-prompt change only; it does not itself create or complete a product KR.
- Future KR proposals still need Product/OKR Owner review before changing `OKR.md` completion numbers.

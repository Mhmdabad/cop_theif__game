# PRD — Reporting (Internal JSON + Gmail Delivery)

- **Mechanism:** Internal game report + toggleable delivery sinks.
- **Version:** 1.00 · **Parent:** `PRD.md` §3.7 · **Plan:** `PLAN.md` ADR-7, §4.3
- **Related:** [[PRD_mcp_orchestration]], [[scope-decisions]]

## 1. Background & Theory
Assignment §9 requires that, at the end of a full game, the agent holding the **Cop role** triggers an
automatic summary emailed to the instructor. This is a **core** requirement (independent of the bonus).
Reporting is split behind a `ReportSink` abstraction so delivery is pluggable and the JSON is always
persisted locally regardless of email settings.

## 2. Requirements
- **Internal report** (`results/game_report.json`), **JSON-only body** (no free text) so it can be parsed
  by an automated grader. Fields: `group_name`, `students`, `github_repo`, `agent_a_mcp_url`,
  `agent_b_mcp_url`, `timezone`, `sub_games[]` (each with `cop_agent`/`thief_agent`, `winner`, `moves`,
  `cop_score`, `thief_score`), `totals` (`by_role` + `by_agent`).
- **Sinks:** `FileReportSink` (always writes to `results/`); `GmailReportSink` (emails via Gmail API when
  `reporting.email_enabled` is true).
- **Auth:** Gmail uses **token-based OAuth** (client secret + stored `token.json`), never a password;
  secrets git-ignored.
- **Technical-loss rule:** only 6 **valid** sub-games are reported; technically-failed ones are re-run.

## 3. Interface (I/O)
- **Input:** completed sub-game logs + config. **Output:** validated JSON report on disk; optional email.
- **Setup:** `email_enabled`, `instructor_email`, `gmail_credentials_path`, `gmail_token_path`.

## 4. Performance & Cost
- Report assembly is trivial. One outbound Gmail API call per game (only when enabled).

## 5. Constraints, Alternatives & Rationale
- **Toggle (ADR-7):** always-email rejected (blocks offline dev); file-only rejected (violates §9); the
  toggle satisfies both. Schema field names `agent_a/b_mcp_url` deliberately diverge from the spec's
  role-fixed `cop/thief_mcp_url` because agents swap roles locally — a conscious, documented deviation.

## 6. Success Criteria & Test Scenarios
- Report validates against the schema; `totals` (by_role + by_agent) are arithmetically correct.
- `FileReportSink` always writes the file; `GmailReportSink` sends only when enabled (Gmail client mocked
  in tests; one manual real send verified).
- Missing/invalid Gmail credentials degrade gracefully with a clear error.
- Module coverage ≥ 85% (Gmail I/O mocked).

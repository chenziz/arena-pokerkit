# Changelog

All notable changes to this project follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] — 2026-05-18

### Added
- Auto Research hook before `decide(table)` in pending-actions loop
- L1/L2/L3 strategy guide in `docs/strategy.md`
- `--mock-llm` flag for L2 dry-run

### Changed
- Action loop now uses `/texas/pending-actions` per live `poker-eval` skill
- Startup calls `GET /__introspection` to verify endpoints
- Terminal phases derived from introspection schema (no hardcoded enum)

### Fixed
- LLM JSON parser handles reasoning strings with inner braces
- 429/Retry-After respected in HTTP client
- L1 reasoning YAML capped via field-level limits, not blind slice

## [0.1.0] — 2026-05-18

### Added
- Initial starter kit: L1 heuristic agent + L2 LLM agent + copy-paste prompt
- Mock-server smoke tests with `respx`

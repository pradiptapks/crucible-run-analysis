# crucible-run-analysis

## Overview

Profile-driven benchmark run analysis engine and Claude plugin for crucible. Analyzes benchmark results from `/var/lib/crucible/run/`, detects anomalies via configurable thresholds, correlates tool metrics with benchmark performance, and generates actionable reports.

## Architecture

The project has two components:

1. **Engine** (`bin/analyze-run.py`): Self-contained Python script that loads CDM metric data, applies analysis profiles, and outputs formatted reports (markdown/json/summary)
2. **Plugin** (`plugins/crucible-analysis/`): Claude plugin with a thin SKILL.md that invokes the engine and displays output verbatim

## Key Directories

| Path | Purpose |
|------|---------|
| `bin/` | Analysis engine (`analyze-run.py`) |
| `profiles/` | YAML analysis profiles organized by benchmark |
| `profiles/_base.yaml` | Universal system metrics (sysstat, procstat) |
| `profiles/trafficgen/` | Trafficgen profiles (astf-ovsdpdk, astf-sriov, stl-ovsdpdk, stl-sriov) |
| `profiles/vllm/` | vLLM inference profiles (cpu-smoke, cpu-functional, gpu-full) |
| `plugins/crucible-analysis/` | Claude plugin (SKILL.md, plugin.json) |
| `examples/` | Sample analysis reports (single-run, comparison) |
| `docs/` | Architecture and CLI reference documentation |

## Profile System

Profiles are YAML files that define:
- `match`: Auto-detection rules (tags, tool presence)
- `primary_metrics`: Benchmark KPIs to extract and evaluate
- `tool_correlations`: Tool metrics to correlate with benchmark performance
- `profiler_correlations`: TRex profiler time-series (when available)
- `patterns`: Cross-tool composite anomaly conditions

The engine auto-detects the correct profile based on run-file.json tags and tool-params.json.

### Glob Source Matching

Profile `source` and `type` fields support glob patterns (`*`, `?`). This is required for tools where the metric source name varies by deployment context:
- **dpdk**: Source is `dpdk-ovs` or `dpdk-testpmd` (read from `engine-env.txt`), falling back to `dpdk` for legacy data. Use `source: "dpdk*"` to match all variants.
- **ebpf-dpdk**: Source includes an instance suffix (e.g., `ebpf-dpdk-ovs`, `ebpf-dpdk-testpmd`). Use `source: "ebpf-dpdk*"` to match all instances.

The engine automatically splits results per actual source, so each instance gets its own section in the report.

Pattern conditions also support glob source matching for cross-tool anomaly detection.

## Trafficgen Mode Detection

- `trex-astf`: Tag `trafficgen_backend=trex-astf` or presence of `connections-per-second` metric
- `trex-txrx` / `trex-txrx-profile`: Tag `trafficgen_backend` in [trex-txrx, trex-txrx-profile] or presence of `lost-rx-pps` metric
- Profiler data: Only present in `trex-txrx-profile` mode (source `trafficgen-trex-profiler`)

## Datapath Detection

- OVS-DPDK: `ovs` present in tool-params.json
- SR-IOV: `ovs` absent from tool-params.json

## vLLM Tier Detection

- `cpu-smoke`: Tag `tier=cpu-smoke` — mock server pipeline validation, no real inference
- `cpu-functional`: Tag `tier=cpu-functional` — real vLLM CPU inference with small models
- `gpu-full`: Tag `tier=gpu-full` — production GPU inference with nvidia tool correlations

Primary metrics: `output-tokens-per-sec`, `requests-per-sec`, `total-tokens-per-sec`, TTFT/ITL/E2E latency percentiles (mean, p50, p90, p99). Source: `vllm`.

## Adding New Profiles

See `docs/architecture.md` for the extension guide. Key steps:
1. Identify benchmark post-processor metric types
2. Create profile YAML with match rules, primary metrics, tool correlations, and patterns
3. Test with `python3 bin/analyze-run.py --run-dir <path> --profile <name>`

## Dependencies

- Python 3.6+ (stdlib + PyYAML)
- No container dependencies — runs on the host

# CLI Reference -- analyze-run.py

## Synopsis

```
analyze-run.py --run-dir PATH [OPTIONS]
```

## Required Arguments

| Argument | Description |
|----------|-------------|
| `--run-dir PATH` | Path to a crucible run directory (e.g., `/var/lib/crucible/run/latest`). The directory must contain valid run data including `run/iteration*/sample*/result-summary.json` and associated metric data. |

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--profiles-dir PATH` | User-defined profiles directory. Must be an absolute path. When specified, this directory is searched first before falling back to the bundled profiles directory. | Bundled profiles at `<script-dir>/../profiles` |
| `--profile NAME` | Override auto-selected profile. Specify as `benchmark/variant` (e.g., `trafficgen/astf-sriov`). Bypasses auto-detection entirely. | Auto-detected from run metadata |
| `--format FORMAT` | Output format. Accepted values: `markdown`, `json`, `summary`. | `markdown` |
| `--section SECTION` | Comma-separated list of sections to include in the output. Accepted values: `overview`, `metrics`, `alerts`, `patterns`, `tools`, `recommendations`, `all`. | `all` |
| `--compare PATH` | Path to another run directory for comparison. Produces a delta analysis showing regressions and improvements between the two runs. | None |
| `--top N` | Limit per-instance tables to the top N entries, sorted by value in descending order. | `10` |
| `--no-color` | Disable status indicators (warning/critical markers) in markdown output. Useful when piping to tools that do not support inline markers. | Indicators enabled |
| `--verbose` | Show progress messages on stderr during analysis. | Off |
| `--quiet` | Suppress all stderr output. This is the default behavior when invoked from the crucible skill. | Off |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success -- full analysis completed with all requested sections populated. |
| `1` | Error -- invalid path, missing run data, profile not found, or required dependency (PyYAML) not installed. |
| `2` | Partial success -- some metrics were unavailable but the report was still generated with available data. |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CRUCIBLE_HOME` | Crucible installation directory. Used to locate bundled profiles when `--profiles-dir` is not specified. | `/opt/crucible` |

## Profile Resolution Order

The engine resolves which profile(s) to apply using the following precedence:

1. **`--profiles-dir /absolute/path`** -- If provided, this directory is searched first for matching profile YAML files.
2. **`--profile NAME`** -- If provided, the named profile is loaded directly, bypassing auto-detection.
3. **Auto-detection** -- The engine inspects run tags (e.g., `trafficgen_backend`) and the set of tools present in the run to select the best-matching profile automatically.
4. **Fallback** -- If no profile matches, only `_base.yaml` is applied, providing generic metric extraction without benchmark-specific thresholds or alert rules.

## Examples

### Analyze latest run (auto-detect profile)

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest
```

### Analyze specific run with JSON output

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/trafficgen--2026-06-05_06:37:33_UTC--8ab97461-5b1b-45bf-a0b6-ac0d0b99e8ba --format json
```

### Analyze with explicit profile override

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest --profile trafficgen/stl-sriov
```

### Use user-defined profiles directory

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest --profiles-dir /home/user/my-profiles
```

### Compare two runs for regression detection

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest \
    --compare /var/lib/crucible/run/trafficgen--2026-06-04_10:00:00_UTC--abc12345-...
```

### Only show alerts and patterns

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest --section alerts,patterns
```

### Quick summary for scripting

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest --format summary
```

### Silent mode for skill invocation

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest --format markdown --quiet
```

## Output Format Specifications

### Markdown Format

The markdown output is organized into the following sections:

- **Run Overview** -- Run ID, benchmark name, start/end timestamps, duration, tags, and iteration/sample counts.
- **Primary Metrics** -- A table of the benchmark's primary performance metrics with columns for metric name, value, unit, and status (OK/WARN/CRITICAL). Per-instance sub-tables are included when multiple instances exist, limited by `--top`.
- **Alerts** -- Threshold violations and anomalies grouped by the tool that reported them. Each alert includes severity, metric name, observed value, threshold, and a short description.
- **Detected Patterns** -- Behavioral patterns identified across the run, such as throughput degradation over time, latency spikes correlated with CPU events, or steady-state detection results.
- **Tool Summaries** -- Per-tool summaries for each data collection tool present in the run (e.g., mpstat, sar, ovs, profiler). Includes key statistics and notable observations.
- **Recommendations** -- Actionable tuning or investigation suggestions derived from the alerts and patterns. Each recommendation references the evidence that triggered it.

### JSON Format

The JSON output follows this schema:

```json
{
  "run_info": {
    "run_id": "string",
    "benchmark": "string",
    "tags": {},
    "start_time": "ISO-8601",
    "end_time": "ISO-8601",
    "iterations": 0,
    "samples": 0
  },
  "primary_metrics": [
    {
      "name": "string",
      "value": 0.0,
      "unit": "string",
      "status": "ok|warn|critical",
      "instances": []
    }
  ],
  "alerts": [
    {
      "severity": "warning|critical",
      "tool": "string",
      "metric": "string",
      "observed": 0.0,
      "threshold": 0.0,
      "description": "string"
    }
  ],
  "patterns": [
    {
      "type": "string",
      "description": "string",
      "evidence": {}
    }
  ],
  "tool_summaries": {
    "tool_name": {
      "metrics_collected": 0,
      "alerts": 0,
      "summary": "string"
    }
  },
  "recommendations": [
    {
      "priority": "high|medium|low",
      "action": "string",
      "evidence": "string"
    }
  ]
}
```

### Summary Format

A single line suitable for scripting and dashboards:

```
STATUS: benchmark (run-id-short) primary-metric=value [delta if compare]
```

Where `STATUS` is one of:

- **OK** -- All metrics within acceptable thresholds.
- **WARN** -- One or more metrics exceeded warning thresholds but no critical violations.
- **CRITICAL** -- One or more metrics exceeded critical thresholds.

When `--compare` is used, the delta is appended showing the percentage change from the baseline run.

## Trafficgen Mode Examples

### trex-astf run (OVS-DPDK)

When the run contains the tag `trafficgen_backend=trex-astf` and the tool set includes `ovs`, the engine auto-selects the `trafficgen/astf-ovsdpdk` profile. This profile defines:

- Primary metrics: TCP transaction rate, TCP connection rate, TCP latency
- OVS-specific tool analysis: datapath flow counts, upcall rates, PMD CPU utilization
- Alert thresholds tuned for ASTF workloads over OVS-DPDK bridges

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/trafficgen--2026-06-05_06:37:33_UTC--8ab97461-...
```

Auto-detection logic: tag `trafficgen_backend=trex-astf` + tool `ovs` present --> profile `trafficgen/astf-ovsdpdk`.

### trex-txrx-profile run (SR-IOV)

When the run contains a tag indicating `trex-txrx-profile` as the backend and `ovs` is absent from the tool set, the engine auto-selects the `trafficgen/stl-sriov` profile. This profile defines:

- Primary metrics: throughput (Mpps), packet loss rate, latency percentiles
- SR-IOV-specific analysis: per-flow distribution, NIC queue balance
- Profiler time-series data integration when profiler tool data is available, providing CPU cycle breakdowns correlated with traffic phases

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/trafficgen--2026-06-05_12:00:00_UTC--...
```

Auto-detection logic: tag `trafficgen_backend=trex-txrx-profile` + no `ovs` tool --> profile `trafficgen/stl-sriov`.

### trex-txrx run

Runs using the `trex-txrx` backend follow the same STL profile selection as `trex-txrx-profile`. The engine auto-selects `trafficgen/stl-sriov` (or `trafficgen/stl-ovsdpdk` if `ovs` is present). The difference from `trex-txrx-profile` is that profiler time-series data is not available, so CPU cycle breakdowns and traffic-phase correlation sections are omitted from the report.

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/trafficgen--2026-06-05_14:00:00_UTC--...
```

Auto-detection logic: tag `trafficgen_backend=trex-txrx` + no `ovs` tool --> profile `trafficgen/stl-sriov` (without profiler sections).

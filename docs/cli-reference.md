# CLI Reference

## Skill Invocation

The primary interface is the Claude skill:

```
/crucible-analysis:analyze-run <target> [options]
```

### Target Resolution

| Target | Description | Example |
|--------|-------------|---------|
| `latest` | Resolves symlink `/var/lib/crucible/run/latest` | `/crucible-analysis:analyze-run latest` |
| Partial UUID | Matches run directory by UUID prefix | `/crucible-analysis:analyze-run 8ab97461` |
| Full path | Uses the absolute path directly | `/crucible-analysis:analyze-run /var/lib/crucible/run/trafficgen--2026-06-05_...` |

### Skill Options

| Option | Description | Example |
|--------|-------------|---------|
| `--profile NAME` | Override auto-detected profile | `/crucible-analysis:analyze-run latest --profile trafficgen/stl-sriov` |
| `--profile /path` | Use a custom profiles directory | `/crucible-analysis:analyze-run latest --profile /home/user/my-profiles` |
| `--compare TARGET` | Compare against another run | `/crucible-analysis:analyze-run latest --compare 079069ba` |
| `--section LIST` | Limit output sections | `/crucible-analysis:analyze-run latest --section overview,metrics,alerts` |

---

## Engine CLI -- analyze-run.py

### Synopsis

```
python3 bin/analyze-run.py --run-dir PATH [OPTIONS]
```

### Required Arguments

| Argument | Description |
|----------|-------------|
| `--run-dir PATH` | Path to a crucible run directory (e.g., `/var/lib/crucible/run/latest`) |

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--profiles-dir PATH` | User-defined profiles directory (absolute path, searched first) | Bundled `<script-dir>/../profiles` |
| `--profile NAME` | Override auto-selected profile (e.g., `trafficgen/astf-sriov`) | Auto-detected |
| `--format FORMAT` | Output format: `markdown`, `json`, `summary` | `markdown` |
| `--section SECTION` | Comma-separated sections: `overview`, `metrics`, `alerts`, `patterns`, `tools`, `recommendations`, `all` | `all` |
| `--compare PATH` | Compare against another run directory | None |
| `--top N` | Limit per-instance tables to top N entries | `10` |
| `--no-color` | Disable status indicators in output | Enabled |
| `--verbose` | Show progress messages on stderr | Off |
| `--quiet` | Suppress all stderr output | Off |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success -- analysis completed, at least one primary metric has data |
| `1` | Error -- invalid path, missing data, profile not found, PyYAML not installed |
| `2` | Partial -- no benchmark measurement data found but report was still generated |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CRUCIBLE_HOME` | Crucible installation directory | `/opt/crucible` |

---

## Profile Resolution Order

1. `--profiles-dir /absolute/path` (user-defined directory)
2. `--profile NAME` (explicit override within profiles directory)
3. Auto-detection via run tags + tool presence
4. Fallback: `_base.yaml` only

---

## Examples by Benchmark

### trafficgen -- ASTF + OVS-DPDK

Auto-detects from tag `trafficgen_backend=trex-astf` and `ovs` in tools. Uses profile `trafficgen/astf-ovsdpdk`.

```
/crucible-analysis:analyze-run latest
```

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/trafficgen--2026-06-05_06:37:33_UTC--8ab97461-... --format markdown
```

### trafficgen -- ASTF + SR-IOV

Auto-detects from tag `trafficgen_backend=trex-astf` and absence of `ovs`. Uses profile `trafficgen/astf-sriov`.

```
/crucible-analysis:analyze-run latest --profile trafficgen/astf-sriov
```

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest --profile trafficgen/astf-sriov
```

### trafficgen -- STL (trex-txrx-profile) + OVS-DPDK

Auto-detects from tag `trafficgen_backend=trex-txrx-profile` and `ovs` in tools. Uses profile `trafficgen/stl-ovsdpdk` with profiler correlations enabled.

```
/crucible-analysis:analyze-run 8ab97461
```

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/trafficgen--2026-06-05_12:00:00_UTC--... --format markdown
```

### trafficgen -- STL (trex-txrx) + SR-IOV

Auto-detects from tag `trafficgen_backend=trex-txrx` and absence of `ovs`. Uses profile `trafficgen/stl-sriov` without profiler time-series (profiler only exists in trex-txrx-profile mode).

```
/crucible-analysis:analyze-run latest
```

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest --format markdown
```

### fio -- Random I/O (Future)

Will auto-detect from benchmark name `fio` and run tags indicating random I/O workload.

```
/crucible-analysis:analyze-run latest --profile fio/random-io
```

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/fio--2026-07-01_10:00:00_UTC--... --profile fio/random-io
```

### iperf -- TCP Throughput (Future)

Will auto-detect from benchmark name `iperf` and TCP protocol tags.

```
/crucible-analysis:analyze-run latest --profile iperf/tcp-throughput
```

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/iperf--2026-07-01_10:00:00_UTC--... --profile iperf/tcp-throughput
```

### uperf -- Latency/Throughput (Future)

Will auto-detect from benchmark name `uperf` and workload profile tags.

```
/crucible-analysis:analyze-run latest --profile uperf/latency-throughput
```

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/uperf--2026-07-01_10:00:00_UTC--... --profile uperf/latency-throughput
```

### cyclictest -- Real-Time Latency (Future)

Will auto-detect from benchmark name `cyclictest`.

```
/crucible-analysis:analyze-run latest --profile cyclictest/realtime-latency
```

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/cyclictest--2026-07-01_10:00:00_UTC--... --profile cyclictest/realtime-latency
```

### ilab -- Training Throughput (Future)

Will auto-detect from benchmark name `ilab` with nvidia GPU tool data.

```
/crucible-analysis:analyze-run latest --profile ilab/training-throughput
```

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/ilab--2026-07-01_10:00:00_UTC--... --profile ilab/training-throughput
```

### pytorch -- Inference Latency (Future)

Will auto-detect from benchmark name `pytorch`.

```
/crucible-analysis:analyze-run latest --profile pytorch/inference-latency
```

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/pytorch--2026-07-01_10:00:00_UTC--... --profile pytorch/inference-latency
```

---

## Comparison Examples

### Compare two trafficgen runs

```
/crucible-analysis:analyze-run latest --compare 079069ba
```

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest \
    --compare /var/lib/crucible/run/trafficgen--2026-06-04_10:00:00_UTC--079069ba-...
```

### Compare with section filtering

```
/crucible-analysis:analyze-run latest --compare 079069ba --section overview,metrics
```

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest \
    --compare /var/lib/crucible/run/trafficgen--2026-06-04_10:00:00_UTC--079069ba-... \
    --section overview,metrics
```

---

## Output Format Specifications

### Markdown Format (default)

Sections produced (omitted when empty):

| Section | Content |
|---------|---------|
| **Run Overview** | Benchmark, profile, timestamp, scenario, DUT, tools, mode, duration |
| **Primary Metrics** | Table: Metric, Value, Status (OK/WARN/CRITICAL) |
| **Alerts** | Threshold violations grouped by severity and tool |
| **Detected Patterns** | Cross-tool anomaly patterns with severity and recommendations |
| **Tool Summary** | Per-tool metric tables (top N instances) |
| **Comparison** | Side-by-side delta table (when --compare used) |
| **Recommendations** | Prioritized actionable items from patterns + critical alerts |

### JSON Format

```json
{
  "run_info": {
    "benchmark": "trafficgen",
    "uuid": "8ab97461-...",
    "timestamp": "2026-06-05_06:37:33_UTC",
    "tags": {},
    "tools": ["sysstat", "procstat", "ovs", "dpdk"],
    "mode": "astf",
    "duration_ms": 76751
  },
  "profile_name": "astf-ovsdpdk",
  "primary_metrics": [
    {"label": "Connections/sec", "value": 847706.8, "status": "OK", "source": "trafficgen", "type": "connections-per-second"}
  ],
  "alerts": [
    {"severity": "CRITICAL", "tool": "dpdk", "label": "DPDK RX Missed/sec", "group": "device=0000.3b.00.0", "value": 19511174, "detail": "..."}
  ],
  "detected_patterns": [
    {"name": "High Retransmission Rate", "severity": "warning", "description": "...", "recommendation": "..."}
  ],
  "tool_correlation_results": [],
  "recommendations": [
    {"priority": "HIGH", "action": "..."}
  ],
  "comparison": null
}
```

### Summary Format

Single line for scripting:

```
STATUS: benchmark (run-id-short) primary-metric=value [delta%]
```

Where STATUS is `OK`, `WARN`, or `CRITICAL`.

Example:
```
OK: trafficgen (8ab97461) Connections/sec=847,706.8 Retransmit %=0.0133
```

---

## User-Defined Profiles

Create custom profiles for site-specific thresholds or new benchmarks:

```
/crucible-analysis:analyze-run latest --profile /home/user/my-profiles/custom-astf.yaml
```

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest \
    --profiles-dir /home/user/my-profiles
```

The engine searches the user directory first, falling back to bundled profiles if no match is found.

# crucible-run-analysis

Profile-driven benchmark run analysis for the [crucible](https://github.com/perftool-incubator/crucible) performance testing framework. Provides a Claude plugin that analyzes benchmark results, detects anomalies, and correlates tool metrics with benchmark performance.

## Installation

This project is a crucible subproject managed by `crucible update`. Once registered in `config/repos.json`, it is automatically cloned to `subprojects/core/crucible-run-analysis`.

Register the Claude plugin marketplace and install the plugin:

```bash
claude plugin marketplace add ${CRUCIBLE_HOME}/subprojects/core/crucible-run-analysis
claude plugin install crucible-analysis@crucible-run-analysis
```

## Usage

### Claude Skill Invocation

```
/crucible-analysis:analyze-run latest
/crucible-analysis:analyze-run 8ab97461
/crucible-analysis:analyze-run /var/lib/crucible/run/trafficgen--2026-06-05_06:37:33_UTC--8ab97461-...
/crucible-analysis:analyze-run latest --compare /var/lib/crucible/run/trafficgen--2026-06-04_...
/crucible-analysis:analyze-run latest --profile trafficgen/stl-sriov
/crucible-analysis:analyze-run latest --section overview,metrics,alerts
```

### Direct Engine Invocation

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest --format markdown
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest --format json
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest --format summary --quiet
```

## Supported Benchmarks

### Current (v1)

| Benchmark | Profiles | Test Modes | Datapaths |
|-----------|----------|------------|-----------|
| **trafficgen** | `astf-ovsdpdk`, `astf-sriov`, `stl-ovsdpdk`, `stl-sriov` | trex-txrx, trex-txrx-profile, trex-astf | OVS-DPDK, SR-IOV |

### Planned (Future)

| Benchmark | Planned Profiles | Primary Metrics |
|-----------|-----------------|-----------------|
| **fio** | `random-io`, `sequential-io` | IOPS, bandwidth (MB/s), latency (usec) |
| **iperf** | `tcp-throughput`, `udp-loss` | bits-per-second, jitter, lost datagrams |
| **uperf** | `tcp-stream`, `tcp-rr`, `udp-stream` | transactions/s, bytes/s, latency |
| **cyclictest** | `realtime-latency` | max-latency (usec), avg-latency, histogram P99 |
| **oslat** | `os-jitter` | max-latency (nsec), P99 latency |
| **hwnoise** | `platform-noise` | max-noise (nsec), noise-frequency |
| **ilab** | `training-throughput` | samples/s, tokens/s, loss |
| **pytorch** | `inference-latency` | latency (ms), throughput (inferences/s) |
| **flexran** | `l1-acceleration` | uplink/downlink throughput, L1 latency |
| **timerlat** | `timer-latency` | max-latency (usec), P99 latency |
| **hwlatdetect** | `hw-latency` | max-latency (usec), count above threshold |

## Tool Coverage

### Current Tool Support (v1 -- trafficgen profiles)

| Tool | Source(s) | Key Metrics | Used In |
|------|-----------|-------------|---------|
| **sysstat** | mpstat, iostat, sar-mem, sar-net, sar-scheduler, sar-tasks | CPU utilization, disk I/O, memory pressure, network throughput, context switches | All profiles (via `_base.yaml`) |
| **procstat** | procstat | interrupts/sec, softnet processed/sec | All profiles (via `_base.yaml`) |
| **dpdk** | dpdk | rx-missed-sec, rx/tx-pps, rx/tx-Gbps, mempool-used-pct, queue-pps, xstats | trafficgen (all datapaths) |
| **ovs** | ovs-pmd, ovs-dpctl, ovs-ofctl, ovs-appctl | pmd-busy, kpps, lookups-sec, flows-count, upcall-flow, errors-sec, Gbps | trafficgen (OVS-DPDK only) |
| **ethtool** | ethtool | packets-sec, bytes-sec, errors-sec, dropped-sec (+ dynamic NIC counters) | trafficgen (all datapaths) |
| **ebpf-dpdk** | ebpf-dpdk-ovs, ebpf-dpdk-testpmd, etc. | top-function-pct, top1..top5-function-pct, perf-samples, perf-samples-active | trafficgen (all datapaths) |

### Future Tool Support (Planned)

| Tool | Planned Benchmarks | Key Metrics |
|------|-------------------|-------------|
| **nvidia** | ilab, pytorch | GPU utilization, GPU memory, power draw, SM clock |
| **kernel** | fio, cyclictest, oslat | scheduler stats, preemption counts, softirq stats |
| **ftrace** | cyclictest, oslat, timerlat | latency tracing, preemption events, wakeup paths |
| **forkstat** | fio, uperf | process creation rate, fork overhead |
| **power** | hwnoise, oslat | C-state transitions, frequency scaling events |

### Tool Coverage Matrix

| Tool | trafficgen | fio | iperf | uperf | cyclictest | oslat | ilab | pytorch |
|------|:----------:|:---:|:-----:|:-----:|:----------:|:-----:|:----:|:-------:|
| sysstat (mpstat) | v1 | planned | planned | planned | planned | planned | planned | planned |
| sysstat (iostat) | v1 | planned | -- | -- | -- | -- | -- | -- |
| sysstat (sar-mem) | v1 | planned | -- | -- | planned | planned | planned | planned |
| sysstat (sar-net) | v1 | -- | planned | planned | -- | -- | -- | -- |
| sysstat (sar-scheduler) | v1 | -- | -- | -- | planned | planned | -- | -- |
| procstat | v1 | planned | planned | planned | planned | planned | -- | -- |
| dpdk | v1 | -- | -- | -- | -- | -- | -- | -- |
| ovs | v1 | -- | -- | -- | -- | -- | -- | -- |
| ethtool | v1 | -- | planned | planned | -- | -- | -- | -- |
| ebpf-dpdk | v1 | -- | -- | -- | -- | -- | -- | -- |
| nvidia | -- | -- | -- | -- | -- | -- | planned | planned |
| kernel | -- | planned | -- | -- | planned | planned | -- | -- |
| ftrace | -- | -- | -- | -- | planned | planned | -- | -- |

`v1` = shipped. `planned` = on roadmap. `--` = not applicable.

## Example Reports

- [Single-run STL + OVS-DPDK](examples/single-run-stl-ovsdpdk.md) -- Full analysis with per-instance ebpf-dpdk profiling (OVS + testpmd), DPDK NIC telemetry, OVS datapath stats, and pattern detection
- [Comparison ASTF + OVS-DPDK](examples/comparison-astf-ovsdpdk.md) -- Two-run comparison showing delta computation, regression/improvement flagging, and cross-tool alerts

## Documentation

- [Architecture](docs/architecture.md) -- End-to-end technical design and future roadmap
- [CLI Reference](docs/cli-reference.md) -- Complete command-line guide with examples

## Dependencies

- Python 3.6+
- PyYAML (`dnf install python3-pyyaml` or `pip3 install pyyaml`)

## License

Apache-2.0

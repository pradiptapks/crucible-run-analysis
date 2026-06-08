# crucible-run-analysis

Profile-driven benchmark run analysis for the [crucible](https://github.com/perftool-incubator/crucible) performance testing framework. Provides a Claude plugin that analyzes benchmark results, detects anomalies, and correlates tool metrics with benchmark performance.

## Installation

This project is a crucible subproject managed by `crucible update`. Once registered in `config/repos.json`, it is automatically cloned to `subprojects/core/crucible-run-analysis`.

Register the Claude plugin:

```bash
claude plugin marketplace add ${CRUCIBLE_HOME}/subprojects/core/crucible-run-analysis
```

## Usage

Invoke via the Claude skill:

```
/crucible-analysis:analyze-run latest
/crucible-analysis:analyze-run 8ab97461
/crucible-analysis:analyze-run /var/lib/crucible/run/trafficgen--2026-06-05_06:37:33_UTC--8ab97461-...
```

Or run the engine directly:

```bash
python3 bin/analyze-run.py --run-dir /var/lib/crucible/run/latest --format markdown
```

## Supported Benchmarks

- **trafficgen** (v1): Full coverage for trex-txrx, trex-txrx-profile, and trex-astf modes across OVS-DPDK and SR-IOV datapaths

## Tool Coverage

Analysis profiles correlate benchmark metrics with data from:

- **sysstat** (mpstat, iostat, sar-mem, sar-net, sar-scheduler, sar-tasks)
- **procstat** (interrupts, softnet)
- **dpdk** (port stats, queue stats, mempool, xstats)
- **ovs** (PMD performance, datapath stats, port counters, upcalls, conntrack)
- **ethtool** (NIC driver counters)
- **ebpf-dpdk** (PMD function profiling)

## Documentation

- [Architecture](docs/architecture.md) — End-to-end technical design
- [CLI Reference](docs/cli-reference.md) — Complete command-line guide

## Dependencies

- Python 3.6+
- PyYAML (`dnf install python3-pyyaml` or `pip3 install pyyaml`)

## License

Apache-2.0

# Run Analysis: trafficgen (8955f0a7)

**Profile**: stl-ovsdpdk
**Timestamp**: 2026-06-09_09:50:00_UTC
**Scenario**: ovs-dpdk
**Tools**: sysstat, procstat, ovs, dpdk, ebpf-dpdk, ebpf-dpdk
**Mode**: stl (trex-txrx)
**Duration**: 30.1s

## Primary Metrics

| Metric | Value | Status |
|--------|-------|--------|
| RX Packets/sec | 1.01 Mpps | OK |
| TX Packets/sec | 1.86 Mpps | OK |
| L2 RX Throughput (bps) | 484.95 Mbps | OK |
| L2 TX Throughput (bps) | 894.20 Mbps | OK |
| L1 RX Throughput (bps) | 678.93 Mbps | OK |
| L1 TX Throughput (bps) | 1.25 Gbps | OK |
| Lost RX Packets/sec | 852.60 Kpps | CRITICAL |
| Max Round-Trip (usec) | 559.2 | WARN |
| Mean Round-Trip (usec) | 513.4 | WARN |

## Alerts (5)

**WARN** sysstat / Pages Out KB/sec [_all]: 2,750.8 (2750.809262295082 >= 1000)
**CRITICAL** dpdk / DPDK RX Missed/sec [device=0000.4b.00.0]: 203,444,570 (203444570.26761332 >= 1000)
**CRITICAL** dpdk / DPDK RX Missed/sec [device=0000.4b.00.1]: 204,969,542 (204969542.08651015 >= 1000)
**WARN** ovs / OVS Port Errors/sec [bridge=br-provider1, interface=dpdk2, direction=rx]: 39,614,142 (39614142.06382474 >= 100)
**WARN** ovs / OVS Port Errors/sec [bridge=br-provider2, interface=dpdk3, direction=rx]: 39,910,671 (39910671.238529526 >= 100)

## Detected Patterns

### info PMD Hot Function
A single function is consuming more than 50% of PMD CPU cycles, which may indicate an optimization opportunity.

**Action**: Review the hot function for optimization opportunities. If it is a lookup function, consider enabling hardware offloads.


## Tool Summary

### dpdk

**rx-Gbps**:

| Group | Value | Status |
|-------|-------|--------|
| device=0000.4b.00.0 | 1.81 Gbps | OK |
| device=0000.4b.00.1 | 1.80 Gbps | OK |
| device=0000.04.00.0 | 1.77 Gbps | OK |
| device=0000.05.00.0 | 1.76 Gbps | OK |
| device=0000.5e.00.1 | 0.42 Gbps | OK |
| device=0000.86.00.1 | 0.42 Gbps | OK |
| device=0000.5e.00.0 | 0.41 Gbps | OK |
| device=0000.af.00.1 | 0.41 Gbps | OK |
| device=0000.86.00.0 | 0.41 Gbps | OK |
| device=0000.3b.00.0 | 0.41 Gbps | OK |
| ... (3 more) | | |

**rx-missed-sec**:

| Group | Value | Status |
|-------|-------|--------|
| device=0000.4b.00.1 | 204,969,542 | CRITICAL |
| device=0000.4b.00.0 | 203,444,570 | CRITICAL |

**rx-pps**:

| Group | Value | Status |
|-------|-------|--------|
| device=0000.04.00.0 | 3.69 Mpps | OK |
| device=0000.05.00.0 | 3.67 Mpps | OK |
| device=0000.4b.00.0 | 3.32 Mpps | OK |
| device=0000.4b.00.1 | 3.30 Mpps | OK |
| device=0000.5e.00.1 | 874.55 Kpps | OK |
| device=0000.86.00.1 | 872.36 Kpps | OK |
| device=0000.5e.00.0 | 855.96 Kpps | OK |
| device=0000.af.00.1 | 854.28 Kpps | OK |
| device=0000.86.00.0 | 848.70 Kpps | OK |
| device=0000.3b.00.0 | 847.91 Kpps | OK |
| ... (3 more) | | |

**tx-Gbps**:

| Group | Value | Status |
|-------|-------|--------|
| device=0000.4b.00.1 | 1.88 Gbps | OK |
| device=0000.4b.00.0 | 1.87 Gbps | OK |
| device=0000.05.00.0 | 1.77 Gbps | OK |
| device=0000.04.00.0 | 1.76 Gbps | OK |
| device=0000.86.00.1 | 0.74 Gbps | OK |
| device=0000.86.00.0 | 0.74 Gbps | OK |
| device=0000.5e.00.1 | 0.74 Gbps | OK |
| device=0000.5e.00.0 | 0.74 Gbps | OK |
| device=0000.3b.00.1 | 0.74 Gbps | OK |
| device=0000.3b.00.0 | 0.74 Gbps | OK |
| ... (3 more) | | |

**tx-pps**:

| Group | Value | Status |
|-------|-------|--------|
| device=0000.05.00.0 | 3.69 Mpps | OK |
| device=0000.4b.00.1 | 3.67 Mpps | OK |
| device=0000.04.00.0 | 3.67 Mpps | OK |
| device=0000.4b.00.0 | 3.65 Mpps | OK |
| device=0000.86.00.1 | 1.55 Mpps | OK |
| device=0000.86.00.0 | 1.55 Mpps | OK |
| device=0000.5e.00.1 | 1.55 Mpps | OK |
| device=0000.5e.00.0 | 1.55 Mpps | OK |
| device=0000.3b.00.1 | 1.55 Mpps | OK |
| device=0000.3b.00.0 | 1.55 Mpps | OK |
| ... (3 more) | | |


### ebpf-dpdk-ovs

- **perf-samples** [_all]: 25,231.0 (OK)
- **top-function-pct** [function=rte_vhost_dequeue_burst]: 19.92 (OK)
- **top1-function-pct** [function=rte_vhost_dequeue_burst]: 19.92 (OK)
- **top2-function-pct** [function=dp_netdev_process_rxq_port]: 15.74 (OK)
- **top3-function-pct** [function=rxq_cq_process_v]: 13.44 (OK)

### ebpf-dpdk-testpmd

- **perf-samples** [_all]: 2.00 (OK)
- **top-function-pct** [function=exit_to_user_mode_loop]: 50.00 (OK)
- **top1-function-pct** [function=exit_to_user_mode_loop]: 50.00 (OK)
- **top2-function-pct** [function=_raw_spin_unlock_irq]: 50.00 (OK)

### ovs

**Gbps**:

| Group | Value | Status |
|-------|-------|--------|
| bridge=br-provider2, interface=dpdk3, direction=tx | 1.61 Gbps | OK |
| bridge=br-provider1, interface=dpdk2, direction=tx | 1.60 Gbps | OK |
| bridge=br-int, interface=8, direction=tx | 1.51 Gbps | OK |
| bridge=br-provider2, interface=patch-provnet-a, direction=rx | 1.51 Gbps | OK |
| bridge=br-int, interface=61, direction=tx | 1.50 Gbps | OK |
| bridge=br-provider1, interface=patch-provnet-6, direction=rx | 1.50 Gbps | OK |
| bridge=br-provider1, interface=dpdk2, direction=rx | 1.43 Gbps | OK |
| bridge=br-provider2, interface=dpdk3, direction=rx | 1.42 Gbps | OK |
| bridge=br-int, interface=61, direction=rx | 1.27 Gbps | OK |
| bridge=br-provider1, interface=patch-provnet-6, direction=tx | 1.27 Gbps | OK |
| ... (17 more) | | |

**datapath-hits-sec**:

| Group | Value | Status |
|-------|-------|--------|
| dp=EMC | 53,560.7 | OK |
| dp=Megaflow | 10,838.3 | OK |
| dp=Upcalls | 0.0379 | OK |
| dp=Lost-upcalls | 0.0277 | OK |

**errors-sec**:

| Group | Value | Status |
|-------|-------|--------|
| bridge=br-provider2, interface=dpdk3, direction=rx | 39,910,671 | WARN |
| bridge=br-provider1, interface=dpdk2, direction=rx | 39,614,142 | WARN |
| bridge=br-provider1, interface=LOCAL, direction=tx | 12.38 | OK |
| bridge=br-int, interface=vhu83c842df-70, direction=tx | 0.0074 | OK |
| bridge=br-int, interface=vhu8c42343b-25, direction=tx | 0.0074 | OK |

- **flows-count** [interface=netdev@ovs-netdev]: 13.58 (OK)
**kpps**:

| Group | Value | Status |
|-------|-------|--------|
| core=14, direction=Rx, id=0-14 | 102.12 pps | OK |
| core=14, direction=Tx, id=0-14 | 102.12 pps | OK |
| core=18, direction=Rx, id=0-18 | 102.12 pps | OK |
| core=18, direction=Tx, id=0-18 | 102.12 pps | OK |
| core=10, direction=Rx, id=0-10 | 101.31 pps | OK |
| core=10, direction=Tx, id=0-10 | 101.31 pps | OK |
| core=16, direction=Rx, id=0-16 | 101.31 pps | OK |
| core=16, direction=Tx, id=0-16 | 101.31 pps | OK |
| core=11, direction=Rx, id=1-11 | 0.00 pps | OK |
| core=11, direction=Tx, id=1-11 | 0.00 pps | OK |
| ... (2 more) | | |

**lookups-sec**:

| Group | Value | Status |
|-------|-------|--------|
| action=hit | 3,938,620 | OK |
| action=miss | 0.5405 | OK |
| action=lost | 0.0000 | OK |

**mem-show**:

| Group | Value | Status |
|-------|-------|--------|
| source=idl-cells-Open_vSwitch | 1,269.0 | OK |
| source=rules | 565.0 | OK |
| source=ports | 20.00 | OK |
| source=udpif-keys | 13.58 | OK |
| source=ofconns | 4.00 | OK |
| source=revalidators | 3.00 | OK |

**packets-sec**:

| Group | Value | Status |
|-------|-------|--------|
| bridge=br-int, interface=8, direction=tx | 3,147,047 | OK |
| bridge=br-provider2, interface=patch-provnet-a, direction=rx | 3,146,972 | OK |
| bridge=br-provider2, interface=dpdk3, direction=tx | 3,146,970 | OK |
| bridge=br-int, interface=61, direction=tx | 3,127,251 | OK |
| bridge=br-provider1, interface=patch-provnet-6, direction=rx | 3,127,207 | OK |
| bridge=br-provider1, interface=dpdk2, direction=tx | 3,127,207 | OK |
| bridge=br-provider1, interface=dpdk2, direction=rx | 2,622,502 | OK |
| bridge=br-provider2, interface=dpdk3, direction=rx | 2,605,979 | OK |
| bridge=br-int, interface=61, direction=rx | 2,484,511 | OK |
| bridge=br-provider1, interface=patch-provnet-6, direction=tx | 2,484,477 | OK |
| ... (17 more) | | |

**pmd-busy**:

| Group | Value | Status |
|-------|-------|--------|
| core=10, id=0-10 | 0.0250 | OK |
| core=14, id=0-14 | 0.0250 | OK |
| core=16, id=0-16 | 0.0220 | OK |
| core=18, id=0-18 | 0.0220 | OK |

- **upcall-flow** [interface=netdev@ovs-netdev]: 14.15 (OK)

### procstat

- **interrupts-sec** [_all]: 475,310.6 (OK)
- **processed-sec** [_all]: 6,837.2 (OK)

### sysstat

**Busy-CPU**:

| Group | Value | Status |
|-------|-------|--------|
| num=8 | 1.00 | OK |
| num=16 | 1.00 | OK |
| num=24 | 1.00 | OK |
| num=32 | 1.00 | OK |
| num=9 | 1.00 | OK |
| num=17 | 1.00 | OK |
| num=25 | 1.00 | OK |
| num=2 | 1.00 | OK |
| num=10 | 1.00 | OK |
| num=18 | 1.00 | OK |
| ... (80 more) | | |

- **Context-switches-sec** [_all]: 13,272.7 (OK)
- **KB-Paged-out-sec** [_all]: 2,750.8 (WARN)
**L2-Gbps**:

| Group | Value | Status |
|-------|-------|--------|
| dev=eno3, direction=tx | 0.00 Gbps | OK |
| dev=eno8303, direction=tx | 0.00 Gbps | OK |
| dev=eth0, direction=tx | 0.00 Gbps | OK |
| dev=eno3, direction=rx | 0.00 Gbps | OK |
| dev=eno8303, direction=rx | 0.00 Gbps | OK |
| dev=lo, direction=rx | 0.00 Gbps | OK |
| dev=lo, direction=tx | 0.00 Gbps | OK |
| dev=eth0, direction=rx | 0.00 Gbps | OK |
| dev=ens2f1, direction=tx | 0.00 Gbps | OK |
| dev=bond_api, direction=tx | 0.00 Gbps | OK |
| ... (10 more) | | |

- **Load-Average-01m** [_all]: 9.28 (OK)
- **Memory-Used-Percent** [_all]: 48.16 (OK)
- **Run-Queue-Length** [_all]: 7.86 (OK)
**percent-utilization**:

| Group | Value | Status |
|-------|-------|--------|
| dev=sdb | 7.23 | OK |
| dev=dm-1 | 7.00 | OK |
| dev=dm-2 | 7.00 | OK |
| dev=dm-6 | 6.93 | OK |
| dev=sdb6 | 6.20 | OK |
| dev=dm-3 | 6.13 | OK |
| dev=sda | 6.07 | OK |
| dev=sda2 | 6.07 | OK |
| dev=sdb4 | 5.53 | OK |
| dev=dm-0 | 4.20 | OK |
| ... (4 more) | | |


## Recommendations

1. **[HIGH]** Investigate DPDK RX Missed/sec [device=0000.4b.00.0]: 203,444,570 exceeds critical threshold
2. **[info]** Review the hot function for optimization opportunities. If it is a lookup function, consider enabling hardware offloads.



# Run Analysis: trafficgen (8ab97461)

**Profile**: astf-ovsdpdk
**Timestamp**: 2026-06-05_06:37:33_UTC
**Scenario**: ovsdpdk-astf-short-lived-tcp-no-conntrack
**DUT**: ovs-dpdk-vm-testpmd-io | **Tools**: sysstat, procstat, ovs, dpdk
**Mode**: astf (trex-astf)
**Duration**: 1.3m

## Primary Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Connections/sec | 847,706.8 | OK |
| Active Flows | 428,105.0 | OK |
| Established Flows | 427,815.0 | OK |
| Retransmit % | 0.0133 | OK |
| Connection Error % | N/A | NO_DATA |
| TCP RTT Avg (usec) | 31.25 | OK |
| L7 TX Throughput (bps) | 135.76 Mbps | OK |
| L7 RX Throughput (bps) | 135.76 Mbps | OK |
| Latency Avg (usec) | N/A | NO_DATA |
| Latency Max (usec) | N/A | NO_DATA |
| TCP SYN-ACK Latency (usec) | N/A | NO_DATA |
| TCP Req-Resp Latency (usec) | N/A | NO_DATA |
| Connections Dropped/sec | N/A | NO_DATA |
| Out-of-Order % | N/A | NO_DATA |
| Server Drops | N/A | NO_DATA |
| TCP Connection Drops | N/A | NO_DATA |

## Alerts (10)

**WARN** sysstat / Pages Out KB/sec [_all]: 1,195.5 (1195.4646063281832 >= 1000)
**WARN** sysstat / Run Queue Length [_all]: 15.64 (15.64404609475032 >= 10)
**CRITICAL** dpdk / DPDK RX Missed/sec [device=0000.3b.00.0]: 19,511,174 (19511173.58438901 >= 1000)
**CRITICAL** dpdk / DPDK RX Missed/sec [device=0000.af.00.1]: 1,173,641 (1173640.5180855168 >= 1000)
**CRITICAL** dpdk / DPDK RX Missed/sec [device=0000.4b.00.0]: 62,805.4 (62805.43327870943 >= 1000)
**CRITICAL** dpdk / DPDK RX Missed/sec [device=0000.4b.00.1]: 79,288.5 (79288.54791007914 >= 1000)
**WARN** ovs / OVS Port Errors/sec [bridge=br-int, interface=vhu8c42343b-25, direction=tx]: 346,255.7 (346255.7070417553 >= 100)
**WARN** ovs / OVS Port Errors/sec [bridge=br-int, interface=vhu83c842df-70, direction=tx]: 778.7 (778.6993831872824 >= 100)
**WARN** ovs / OVS Port Errors/sec [bridge=br-provider1, interface=dpdk2, direction=rx]: 6,230.8 (6230.78743978097 >= 100)
**WARN** ovs / OVS Port Errors/sec [bridge=br-provider2, interface=dpdk3, direction=rx]: 7,866.0 (7866.040648221331 >= 100)

## Detected Patterns

### warning High Retransmission Rate
TCP retransmission rate exceeds acceptable threshold, indicating packet loss in the network path.

**Action**: Check for packet drops at OVS or DPDK level, verify MTU settings, and check for buffer overflows.


## Tool Summary

### dpdk

**queue-pps**:

| Group | Value | Status |
|-------|-------|--------|
| device=0000.04.00.0, direction=rx, queue=2 | 1.65 Mpps | OK |
| device=0000.4b.00.1, direction=tx, queue=4 | 1.65 Mpps | OK |
| device=0000.4b.00.1, direction=tx, queue=5 | 1.63 Mpps | OK |
| device=0000.05.00.0, direction=tx, queue=2 | 1.63 Mpps | OK |
| device=0000.05.00.0, direction=rx, queue=2 | 1.10 Mpps | OK |
| device=0000.05.00.0, direction=rx, queue=0 | 1.05 Mpps | OK |
| device=0000.04.00.0, direction=tx, queue=0 | 1.05 Mpps | OK |
| device=0000.4b.00.0, direction=tx, queue=6 | 1.05 Mpps | OK |
| device=0000.04.00.0, direction=tx, queue=2 | 1.04 Mpps | OK |
| device=0000.4b.00.0, direction=tx, queue=2 | 1.04 Mpps | OK |
| ... (12 more) | | |

**rx-Gbps**:

| Group | Value | Status |
|-------|-------|--------|
| device=0000.4b.00.0 | 1.82 Gbps | OK |
| device=0000.04.00.0 | 1.63 Gbps | OK |
| device=0000.af.00.1 | 1.61 Gbps | OK |
| device=0000.4b.00.1 | 1.21 Gbps | OK |
| device=0000.05.00.0 | 1.09 Gbps | OK |
| device=0000.3b.00.0 | 0.31 Gbps | OK |
| device=0000.86.00.0 | 0.29 Gbps | OK |
| device=0000.5e.00.0 | 0.29 Gbps | OK |
| device=0000.af.00.0 | 0.23 Gbps | OK |
| device=0000.5e.00.1 | 0.00 Gbps | OK |
| ... (3 more) | | |

**rx-missed-sec**:

| Group | Value | Status |
|-------|-------|--------|
| device=0000.3b.00.0 | 19,511,174 | CRITICAL |
| device=0000.af.00.1 | 1,173,641 | CRITICAL |
| device=0000.4b.00.1 | 79,288.5 | CRITICAL |
| device=0000.4b.00.0 | 62,805.4 | CRITICAL |

**rx-pps**:

| Group | Value | Status |
|-------|-------|--------|
| device=0000.04.00.0 | 3.22 Mpps | OK |
| device=0000.4b.00.0 | 3.20 Mpps | OK |
| device=0000.af.00.1 | 3.18 Mpps | OK |
| device=0000.05.00.0 | 2.10 Mpps | OK |
| device=0000.4b.00.1 | 2.08 Mpps | OK |
| device=0000.3b.00.0 | 585.41 Kpps | OK |
| device=0000.86.00.0 | 556.14 Kpps | OK |
| device=0000.5e.00.0 | 554.65 Kpps | OK |
| device=0000.af.00.0 | 445.69 Kpps | OK |
| device=0000.5e.00.1 | 2.78 Kpps | OK |
| ... (3 more) | | |

**tx-Gbps**:

| Group | Value | Status |
|-------|-------|--------|
| device=0000.4b.00.1 | 1.72 Gbps | OK |
| device=0000.05.00.0 | 1.61 Gbps | OK |
| device=0000.4b.00.0 | 1.12 Gbps | OK |
| device=0000.af.00.1 | 1.08 Gbps | OK |
| device=0000.04.00.0 | 1.06 Gbps | OK |
| device=0000.3b.00.0 | 0.46 Gbps | OK |
| device=0000.86.00.0 | 0.45 Gbps | OK |
| device=0000.5e.00.0 | 0.45 Gbps | OK |
| device=0000.af.00.0 | 0.33 Gbps | OK |
| device=0000.b1.00.1 | 0.00 Gbps | OK |
| ... (3 more) | | |

**tx-pps**:

| Group | Value | Status |
|-------|-------|--------|
| device=0000.4b.00.1 | 3.20 Mpps | OK |
| device=0000.05.00.0 | 3.20 Mpps | OK |
| device=0000.af.00.1 | 2.09 Mpps | OK |
| device=0000.04.00.0 | 2.04 Mpps | OK |
| device=0000.4b.00.0 | 2.04 Mpps | OK |
| device=0000.3b.00.0 | 916.01 Kpps | OK |
| device=0000.86.00.0 | 893.06 Kpps | OK |
| device=0000.5e.00.0 | 889.41 Kpps | OK |
| device=0000.af.00.0 | 657.25 Kpps | OK |
| device=0000.3b.00.1 | 927.26 pps | OK |
| ... (3 more) | | |


### ovs

**Gbps**:

| Group | Value | Status |
|-------|-------|--------|
| bridge=br-provider1, interface=dpdk2, direction=rx | 1.48 Gbps | OK |
| bridge=br-provider2, interface=dpdk3, direction=tx | 1.44 Gbps | OK |
| bridge=br-int, interface=61, direction=rx | 1.40 Gbps | OK |
| bridge=br-provider1, interface=patch-provnet-6, direction=tx | 1.40 Gbps | OK |
| bridge=br-int, interface=62, direction=tx | 1.36 Gbps | OK |
| bridge=br-provider2, interface=patch-provnet-a, direction=rx | 1.36 Gbps | OK |
| bridge=br-provider2, interface=dpdk3, direction=rx | 0.99 Gbps | OK |
| bridge=br-provider1, interface=dpdk2, direction=tx | 0.94 Gbps | OK |
| bridge=br-int, interface=62, direction=rx | 0.93 Gbps | OK |
| bridge=br-provider2, interface=patch-provnet-a, direction=tx | 0.93 Gbps | OK |
| ... (18 more) | | |

**datapath-hits-sec**:

| Group | Value | Status |
|-------|-------|--------|
| dp=Megaflow | 1,255,687 | OK |
| dp=EMC | 973.8 | OK |
| dp=Upcalls | 0.9499 | OK |

**errors-sec**:

| Group | Value | Status |
|-------|-------|--------|
| bridge=br-int, interface=vhu8c42343b-25, direction=tx | 346,255.7 | WARN |
| bridge=br-provider2, interface=dpdk3, direction=rx | 7,866.0 | WARN |
| bridge=br-provider1, interface=dpdk2, direction=rx | 6,230.8 | WARN |
| bridge=br-int, interface=vhu83c842df-70, direction=tx | 778.7 | WARN |

- **flows-count** [interface=netdev@ovs-netdev]: 38.50 (OK)
**kpps**:

| Group | Value | Status |
|-------|-------|--------|
| core=14, direction=Rx, id=0-14 | 1.95 Kpps | OK |
| core=14, direction=Tx, id=0-14 | 1.94 Kpps | OK |
| core=10, direction=Rx, id=0-10 | 1.94 Kpps | OK |
| core=10, direction=Tx, id=0-10 | 1.93 Kpps | OK |
| core=12, direction=Rx, id=0-12 | 1.71 Kpps | OK |
| core=12, direction=Tx, id=0-12 | 1.71 Kpps | OK |
| core=16, direction=Rx, id=0-16 | 1.61 Kpps | OK |
| core=16, direction=Tx, id=0-16 | 1.61 Kpps | OK |
| core=18, direction=Tx, id=0-18 | 765.10 pps | OK |
| core=18, direction=Rx, id=0-18 | 764.04 pps | OK |
| ... (2 more) | | |

**lookups-sec**:

| Group | Value | Status |
|-------|-------|--------|
| action=miss | -0.0136 | OK |
| action=hit | -3,251.0 | OK |

**mem-show**:

| Group | Value | Status |
|-------|-------|--------|
| source=idl-cells-Open_vSwitch | 1,269.0 | OK |
| source=rules | 566.3 | OK |
| source=udpif-keys | 38.50 | OK |
| source=ports | 20.00 | OK |
| source=ofconns | 4.00 | OK |
| source=revalidators | 3.00 | OK |

**packets-sec**:

| Group | Value | Status |
|-------|-------|--------|
| bridge=br-int, interface=62, direction=tx | 2,687,481 | OK |
| bridge=br-provider2, interface=dpdk3, direction=tx | 2,687,428 | OK |
| bridge=br-provider2, interface=patch-provnet-a, direction=rx | 2,687,424 | OK |
| bridge=br-int, interface=61, direction=rx | 2,612,616 | OK |
| bridge=br-provider1, interface=dpdk2, direction=rx | 2,612,607 | OK |
| bridge=br-provider1, interface=patch-provnet-6, direction=tx | 2,612,600 | OK |
| bridge=br-int, interface=61, direction=tx | 1,714,995 | OK |
| bridge=br-provider1, interface=dpdk2, direction=tx | 1,714,978 | OK |
| bridge=br-provider1, interface=patch-provnet-6, direction=rx | 1,714,973 | OK |
| bridge=br-int, interface=62, direction=rx | 1,701,394 | OK |
| ... (18 more) | | |

**pmd-busy**:

| Group | Value | Status |
|-------|-------|--------|
| core=12, id=0-12 | 0.6639 | OK |
| core=14, id=0-14 | 0.6591 | OK |
| core=10, id=0-10 | 0.5985 | OK |
| core=16, id=0-16 | 0.4584 | OK |
| core=18, id=0-18 | 0.3527 | OK |
| core=11, id=1-11 | 0.0014 | OK |

- **ufid-expired-flows-sec** [_all]: 0.7481 (OK)
- **ufid-new-flows-sec** [_all]: 0.7433 (OK)
- **upcall-flow** [interface=netdev@ovs-netdev]: 38.68 (OK)
- **upcall-flow-avg** [interface=netdev@ovs-netdev]: 37.47 (OK)

### procstat

- **interrupts-sec** [_all]: 3,612,901 (OK)
- **processed-sec** [_all]: 554,355.7 (OK)

### sysstat

**Busy-CPU**:

| Group | Value | Status |
|-------|-------|--------|
| num=56 | 1.00 | OK |
| num=50 | 1.00 | OK |
| num=62 | 1.00 | OK |
| num=8 | 1.00 | OK |
| num=16 | 1.00 | OK |
| num=24 | 1.00 | OK |
| num=32 | 1.00 | OK |
| num=9 | 1.00 | OK |
| num=17 | 1.00 | OK |
| num=25 | 1.00 | OK |
| ... (80 more) | | |

- **Context-switches-sec** [_all]: 25,047.1 (OK)
- **KB-Paged-out-sec** [_all]: 1,195.5 (WARN)
**L2-Gbps**:

| Group | Value | Status |
|-------|-------|--------|
| dev=eno3, direction=tx | 0.00 Gbps | OK |
| dev=eno8303, direction=tx | 0.00 Gbps | OK |
| dev=eth0, direction=tx | 0.00 Gbps | OK |
| dev=eno3, direction=rx | 0.00 Gbps | OK |
| dev=eno8303, direction=rx | 0.00 Gbps | OK |
| dev=br-provider1, direction=rx | 0.00 Gbps | OK |
| dev=br-provider2, direction=rx | 0.00 Gbps | OK |
| dev=eth0, direction=rx | 0.00 Gbps | OK |
| dev=lo, direction=rx | 0.00 Gbps | OK |
| dev=lo, direction=tx | 0.00 Gbps | OK |
| ... (11 more) | | |

- **Load-Average-01m** [_all]: 14.26 (OK)
- **Memory-Used-Percent** [_all]: 49.08 (OK)
- **Run-Queue-Length** [_all]: 15.64 (WARN)
**percent-utilization**:

| Group | Value | Status |
|-------|-------|--------|
| dev=sda | 10.23 | OK |
| dev=sda2 | 10.23 | OK |
| dev=dm-1 | 10.23 | OK |
| dev=dm-2 | 10.23 | OK |
| dev=dm-3 | 10.23 | OK |
| dev=sdb | 5.27 | OK |
| dev=sdb6 | 5.27 | OK |
| dev=dm-6 | 5.23 | OK |
| dev=dm-0 | 3.67 | OK |
| dev=sdb4 | 3.33 | OK |
| ... (4 more) | | |


## Comparison

Baseline: trafficgen (079069ba)

| Metric | Current | Baseline | Delta | Status |
|--------|---------|----------|-------|--------|
| Connections/sec | 847,706.8 | 806,656.2 | +5.1% | IMPROVEMENT |
| Active Flows | 428,105.0 | 622,827.0 | -31.3% | REGRESSION |
| Established Flows | 427,815.0 | 580,683.0 | -26.3% | REGRESSION |
| Retransmit % | 0.0133 | 9.85 | -99.9% | REGRESSION |
| Connection Error % | N/A | 0.1705 | N/A | NO_DATA |
| TCP RTT Avg (usec) | 31.25 | 31.25 | +0.0% | OK |
| L7 TX Throughput (bps) | 135.76 Mbps | 129.10 Mbps | +5.2% | IMPROVEMENT |
| L7 RX Throughput (bps) | 135.76 Mbps | 129.09 Mbps | +5.2% | IMPROVEMENT |
| Latency Avg (usec) | N/A | N/A | N/A | NO_DATA |
| Latency Max (usec) | N/A | N/A | N/A | NO_DATA |
| TCP SYN-ACK Latency (usec) | N/A | N/A | N/A | NO_DATA |
| TCP Req-Resp Latency (usec) | N/A | N/A | N/A | NO_DATA |
| Connections Dropped/sec | N/A | 84,295.0 | N/A | NO_DATA |
| Out-of-Order % | N/A | N/A | N/A | NO_DATA |
| Server Drops | N/A | 84.31 Kops | N/A | NO_DATA |
| TCP Connection Drops | N/A | 340.00 ops | N/A | NO_DATA |

## Recommendations

1. **[HIGH]** Investigate DPDK RX Missed/sec [device=0000.3b.00.0]: 19,511,174 exceeds critical threshold
2. **[warning]** Check for packet drops at OVS or DPDK level, verify MTU settings, and check for buffer overflows.



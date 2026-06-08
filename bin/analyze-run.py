#!/usr/bin/env python3
# -*- mode: python; indent-tabs-mode: nil; python-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

"""
Crucible Run Analysis Engine

Analyzes benchmark run results using profile-driven metric evaluation,
pattern detection, and tool correlation. Produces structured reports in
markdown, JSON, or summary format.
"""

import argparse
import csv
import fnmatch
import glob
import io
import json
import lzma
import os
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    print(json.dumps({
        "error": "PyYAML is required but not installed",
        "detail": "Install with: pip install PyYAML"
    }))
    sys.exit(1)


EXIT_OK = 0
EXIT_ERROR = 1
EXIT_PARTIAL = 2

STATUS_OK = "OK"
STATUS_WARN = "WARN"
STATUS_CRITICAL = "CRITICAL"
STATUS_NO_DATA = "no_data"

REGRESSION_THRESHOLD_PCT = 5.0

THROUGHPUT_TYPES = frozenset([
    "Gbps", "Mpps", "transactions-sec", "ops-sec", "frames-sec",
    "bits-per-sec", "packets-per-sec", "requests-per-sec",
])

LATENCY_TYPES = frozenset([
    "usec", "msec", "nsec", "latency-usec", "latency-msec",
    "mean-latency", "max-latency", "p50-latency", "p90-latency",
    "p95-latency", "p99-latency", "round-trip-time",
])

ERROR_TYPES = frozenset([
    "errors", "drops", "drop-rate", "loss-rate", "retries",
    "rx-lost-packets", "tx-errors", "rx-errors",
])

UNIT_SCALES = {
    "bps": [(1e12, "Tbps"), (1e9, "Gbps"), (1e6, "Mbps"), (1e3, "Kbps")],
    "pps": [(1e9, "Gpps"), (1e6, "Mpps"), (1e3, "Kpps")],
    "ops": [(1e6, "Mops"), (1e3, "Kops")],
    "bytes": [(1e12, "TB"), (1e9, "GB"), (1e6, "MB"), (1e3, "KB")],
}

_csv_cache = {}
_verbose = False
_quiet = False


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def log_verbose(msg):
    if _verbose and not _quiet:
        print(f"[analyze] {msg}", file=sys.stderr)


def log_warn(msg):
    if not _quiet:
        print(f"[warn] {msg}", file=sys.stderr)


def safe_mean(values):
    if not values:
        return None
    return sum(values) / len(values)


def safe_max(values):
    if not values:
        return None
    return max(values)


def _detect_unit_category(metric_type):
    metric_lower = metric_type.lower() if metric_type else ""
    if metric_lower.endswith("-gbps") or metric_lower == "gbps":
        return "pre_scaled_Gbps"
    if metric_lower.endswith("-mbps") or metric_lower == "mbps":
        return "pre_scaled_Mbps"
    if "bps" in metric_lower or "bits-per-sec" in metric_lower:
        return "bps"
    if "pps" in metric_lower or "packets-per-sec" in metric_lower:
        return "pps"
    if "ops" in metric_lower or "operations-per-sec" in metric_lower:
        return "ops"
    if metric_lower in ("bytes", "rx-bytes", "tx-bytes"):
        return "bytes"
    return None


def _scale_value(value, unit_category):
    scales = UNIT_SCALES.get(unit_category)
    if not scales:
        return None, None
    for threshold, suffix in scales:
        if abs(value) >= threshold:
            return value / threshold, suffix
    return None, None


def format_value(value, metric_type=""):
    if value is None:
        return "N/A"

    unit_cat = _detect_unit_category(metric_type)
    if unit_cat:
        if unit_cat.startswith("pre_scaled_"):
            suffix = unit_cat.replace("pre_scaled_", "")
            return f"{value:.2f} {suffix}"
        scaled, suffix = _scale_value(value, unit_cat)
        if scaled is not None:
            return f"{scaled:.2f} {suffix}"
        base_unit = {"bps": "bps", "pps": "pps", "ops": "ops",
                     "bytes": "B"}.get(unit_cat, "")
        return f"{value:.2f} {base_unit}".strip()

    abs_val = abs(value)
    if abs_val >= 1_000_000:
        return f"{value:,.0f}"
    elif abs_val >= 100:
        return f"{value:,.1f}"
    elif abs_val >= 1:
        return f"{value:.2f}"
    elif abs_val > 0:
        return f"{value:.4f}"
    else:
        return "0"


def format_duration_ms(ms_value):
    if ms_value is None:
        return "N/A"
    if ms_value >= 3_600_000:
        return f"{ms_value / 3_600_000:.1f}h"
    elif ms_value >= 60_000:
        return f"{ms_value / 60_000:.1f}m"
    elif ms_value >= 1000:
        return f"{ms_value / 1000:.1f}s"
    return f"{ms_value:.0f}ms"


def format_pct(value):
    if value is None:
        return "N/A"
    return f"{value:.1f}%"


def is_lower_better(metric_type):
    if not metric_type:
        return False
    mt = metric_type.lower()
    if mt in LATENCY_TYPES or any(lt in mt for lt in ("latency", "usec", "msec")):
        return True
    if mt in ERROR_TYPES or any(et in mt for et in ("error", "drop", "loss", "retry")):
        return True
    return False


def evaluate_threshold(value, thresholds):
    if value is None:
        return {"status": STATUS_NO_DATA, "detail": "no data available"}

    if not thresholds:
        return {"status": STATUS_OK, "detail": ""}

    critical_above = thresholds.get("critical_above", thresholds.get("critical"))
    warn_above = thresholds.get("warn_above", thresholds.get("warn"))
    critical_below = thresholds.get("critical_below")
    warn_below = thresholds.get("warn_below")

    if critical_above is not None and value >= critical_above:
        return {"status": STATUS_CRITICAL, "detail": f"{value} >= {critical_above}"}
    if warn_above is not None and value >= warn_above:
        return {"status": STATUS_WARN, "detail": f"{value} >= {warn_above}"}
    if critical_below is not None and value <= critical_below:
        return {"status": STATUS_CRITICAL, "detail": f"{value} <= {critical_below}"}
    if warn_below is not None and value <= warn_below:
        return {"status": STATUS_WARN, "detail": f"{value} <= {warn_below}"}

    return {"status": STATUS_OK, "detail": ""}


def compute_aggregate(values, aggregation):
    if not values:
        return None

    agg = aggregation if aggregation else "mean"
    if agg == "mean":
        return safe_mean(values)
    elif agg == "max":
        return safe_max(values)
    elif agg == "sum":
        return sum(values)
    elif agg == "per_instance":
        return values
    return safe_mean(values)


def match_profile(profile, tags, tools):
    match_section = profile.get("match", {})
    if not match_section:
        return 0

    score = 0

    match_tags = match_section.get("tags", {})
    for key, expected in match_tags.items():
        actual = tags.get(key, "")
        if isinstance(expected, list):
            if actual in expected:
                score += 10
            else:
                return -1
        else:
            if actual == expected:
                score += 10
            elif expected == "*" and actual:
                score += 5
            else:
                return -1

    tools_present = match_section.get("tools_present", [])
    for tool in tools_present:
        if tool in tools:
            score += 3
        else:
            return -1

    tools_absent = match_section.get("tools_absent", [])
    for tool in tools_absent:
        if tool in tools:
            return -1
        score += 1

    return score


def find_descriptors(all_descs, source, metric_type, names_match=None):
    results = []
    for desc in all_descs:
        d = desc.get("desc", {})
        if source and d.get("source") != source:
            continue
        if metric_type:
            if "*" in metric_type or "?" in metric_type:
                if not fnmatch.fnmatch(d.get("type", ""), metric_type):
                    continue
            else:
                if d.get("type") != metric_type:
                    continue
        if names_match:
            names = desc.get("names", {})
            matched = True
            for k, v in names_match.items():
                if isinstance(v, list):
                    if names.get(k) not in v:
                        matched = False
                        break
                elif v == "*":
                    if k not in names:
                        matched = False
                        break
                else:
                    if names.get(k) != v:
                        matched = False
                        break
            if not matched:
                continue
        results.append(desc)
    return results


def group_by_names(descs, names_keys):
    groups = defaultdict(list)
    if not names_keys:
        groups["_all"] = descs
        return dict(groups)

    for desc in descs:
        names = desc.get("names", {})
        key_parts = []
        for k in names_keys:
            key_parts.append(f"{k}={names.get(k, '?')}")
        group_key = ", ".join(key_parts)
        groups[group_key].append(desc)
    return dict(groups)


# ---------------------------------------------------------------------------
# Phase 1 - Discovery
# ---------------------------------------------------------------------------

def parse_run_directory(run_dir):
    basename = os.path.basename(run_dir.rstrip("/"))
    parts = basename.split("--")

    info = {
        "benchmark": parts[0] if len(parts) >= 1 else "unknown",
        "timestamp": parts[1] if len(parts) >= 2 else "",
        "uuid": parts[2] if len(parts) >= 3 else "",
        "run_id_short": "",
    }

    if info["uuid"]:
        info["run_id_short"] = info["uuid"][:8]
    elif info["timestamp"]:
        info["run_id_short"] = info["timestamp"][:8]
    else:
        info["run_id_short"] = basename[:12]

    return info


def load_json_auto(path):
    p = Path(path)
    if p.exists():
        with open(p, "r") as f:
            return json.load(f)
    xz_path = Path(str(path) + ".xz")
    if xz_path.exists():
        with lzma.open(xz_path, "rt") as f:
            return json.load(f)
    return None


def load_run_config(run_dir):
    config_path = os.path.join(run_dir, "config", "run-file.json")
    data = load_json_auto(config_path)
    if data is None:
        return {}
    return data


def extract_tags(run_config):
    tags = {}
    tag_list = run_config.get("tags", {})
    if isinstance(tag_list, dict):
        tags = tag_list
    elif isinstance(tag_list, list):
        for item in tag_list:
            if isinstance(item, dict):
                tags.update(item)
            elif isinstance(item, str) and ":" in item:
                k, v = item.split(":", 1)
                tags[k] = v
    return tags


def load_tool_params(run_dir):
    tp_path = os.path.join(run_dir, "config", "tool-params.json")
    data = load_json_auto(tp_path)
    if data is None:
        return []
    if isinstance(data, list):
        return [t.get("name", t.get("tool", "")) for t in data if isinstance(t, dict)]
    if isinstance(data, dict):
        return list(data.keys())
    return []


def detect_trafficgen_mode(tags):
    backend = tags.get("trafficgen_backend", "")
    if backend == "trex-astf":
        return "astf"
    elif backend in ("trex-txrx", "trex-txrx-profile"):
        return "stl"
    return None


# ---------------------------------------------------------------------------
# Phase 2 - Profile Resolution
# ---------------------------------------------------------------------------

def resolve_profiles_dir(script_dir, profiles_dir_arg):
    if profiles_dir_arg:
        return profiles_dir_arg
    return os.path.join(script_dir, "..", "profiles")


def load_yaml_file(path):
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError) as e:
        log_warn(f"Failed to load YAML {path}: {e}")
        return {}


def find_matching_profile(profiles_dir, benchmark, tags, tools):
    bench_dir = os.path.join(profiles_dir, benchmark)
    if not os.path.isdir(bench_dir):
        return None, None

    best_score = -1
    best_profile = None
    best_name = None

    for fname in sorted(os.listdir(bench_dir)):
        if fname.startswith("_") or not fname.endswith((".yaml", ".yml")):
            continue
        fpath = os.path.join(bench_dir, fname)
        profile = load_yaml_file(fpath)
        if not profile:
            continue
        score = match_profile(profile, tags, tools)
        if score > best_score:
            best_score = score
            best_profile = profile
            best_name = fname.rsplit(".", 1)[0]

    return best_profile, best_name


def load_base_profile(profiles_dir, benchmark):
    base_path = os.path.join(profiles_dir, benchmark, "_base.yaml")
    if os.path.exists(base_path):
        return load_yaml_file(base_path)

    base_path = os.path.join(profiles_dir, "_base.yaml")
    if os.path.exists(base_path):
        return load_yaml_file(base_path)

    return {}


def merge_profiles(base, overlay):
    merged = dict(base)

    if "primary_metrics" in overlay:
        merged["primary_metrics"] = overlay["primary_metrics"]

    if "tool_correlations" in overlay:
        base_tc = merged.get("tool_correlations", [])
        merged["tool_correlations"] = base_tc + overlay["tool_correlations"]

    if "profiler_correlations" in overlay:
        base_pc = merged.get("profiler_correlations", [])
        merged["profiler_correlations"] = base_pc + overlay["profiler_correlations"]

    if "patterns" in overlay:
        base_p = merged.get("patterns", [])
        merged["patterns"] = base_p + overlay["patterns"]

    for key in overlay:
        if key not in ("primary_metrics", "tool_correlations",
                       "profiler_correlations", "patterns", "match"):
            merged[key] = overlay[key]

    return merged


def resolve_profile(profiles_dir, benchmark, tags, tools, profile_name=None):
    if profile_name:
        explicit_path = os.path.join(profiles_dir, profile_name)
        if not os.path.exists(explicit_path):
            explicit_path = os.path.join(profiles_dir, benchmark, profile_name)
        if not os.path.exists(explicit_path):
            for ext in (".yaml", ".yml"):
                p = os.path.join(profiles_dir, benchmark, profile_name + ext)
                if os.path.exists(p):
                    explicit_path = p
                    break

        if os.path.exists(explicit_path):
            overlay = load_yaml_file(explicit_path)
            base = load_base_profile(profiles_dir, benchmark)
            return merge_profiles(base, overlay), profile_name
        else:
            log_warn(f"Specified profile '{profile_name}' not found")
            return load_base_profile(profiles_dir, benchmark), "_base"

    matched, match_name = find_matching_profile(profiles_dir, benchmark, tags, tools)
    base = load_base_profile(profiles_dir, benchmark)

    if matched:
        log_verbose(f"Matched profile: {match_name}")
        return merge_profiles(base, matched), match_name
    elif base:
        log_verbose("Using base profile only")
        return base, "_base"
    else:
        log_warn(f"No profiles found for benchmark '{benchmark}'")
        return {}, None


# ---------------------------------------------------------------------------
# Phase 3 - Metric Loading
# ---------------------------------------------------------------------------

def load_benchmark_results(run_dir):
    descriptors = []
    pattern = os.path.join(run_dir, "run", "iterations", "iteration-*", "sample-*",
                           "client", "*", "metric-data-measurement.*")
    for path in sorted(glob.glob(pattern)):
        if path.endswith(".json"):
            data = load_json_auto(path)
            if data and isinstance(data, list):
                csv_path = path.replace(".json", ".csv.xz")
                if not os.path.exists(csv_path):
                    csv_path = path.replace(".json", ".csv")
                for entry in data:
                    entry["_csv_path"] = csv_path
                    entry["_source_path"] = path
                descriptors.extend(data)
            elif data and isinstance(data, dict):
                csv_path = path.replace(".json", ".csv.xz")
                if not os.path.exists(csv_path):
                    csv_path = path.replace(".json", ".csv")
                data["_csv_path"] = csv_path
                data["_source_path"] = path
                descriptors.append(data)

    server_pattern = os.path.join(run_dir, "run", "iterations", "iteration-*", "sample-*",
                                  "server", "*", "metric-data-measurement.*")
    for path in sorted(glob.glob(server_pattern)):
        if path.endswith(".json"):
            data = load_json_auto(path)
            if data and isinstance(data, list):
                csv_path = path.replace(".json", ".csv.xz")
                if not os.path.exists(csv_path):
                    csv_path = path.replace(".json", ".csv")
                for entry in data:
                    entry["_csv_path"] = csv_path
                    entry["_source_path"] = path
                descriptors.extend(data)
            elif data and isinstance(data, dict):
                csv_path = path.replace(".json", ".csv.xz")
                if not os.path.exists(csv_path):
                    csv_path = path.replace(".json", ".csv")
                data["_csv_path"] = csv_path
                data["_source_path"] = path
                descriptors.append(data)

    return descriptors


def load_profiler_data(run_dir):
    descriptors = []
    pattern = os.path.join(run_dir, "run", "iterations", "iteration-*", "sample-*",
                           "*", "*", "metric-data-*.*")
    for path in sorted(glob.glob(pattern)):
        if not path.endswith(".json"):
            continue
        if "metric-data-measurement" in path:
            continue
        data = load_json_auto(path)
        if not data:
            continue
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            source = entry.get("desc", {}).get("source", "")
            if "profiler" in source.lower() or "trex-profiler" in source:
                csv_path = path.replace(".json", ".csv.xz")
                if not os.path.exists(csv_path):
                    csv_path = path.replace(".json", ".csv")
                entry["_csv_path"] = csv_path
                entry["_source_path"] = path
                descriptors.append(entry)

    return descriptors


def discover_tool_instances(run_dir, tool_name):
    instances = []
    pattern = os.path.join(run_dir, "run", "tool-data", "*",
                           f"*-{tool_name}-*", tool_name, "")
    for path in sorted(glob.glob(pattern)):
        if os.path.isdir(path):
            instances.append(path)

    if not instances:
        alt_pattern = os.path.join(run_dir, "iterations", "iteration-*",
                                   "sample-*", "*", "*", "tool-data",
                                   f"*{tool_name}*", "")
        for path in sorted(glob.glob(alt_pattern)):
            if os.path.isdir(path):
                instances.append(path)

    return instances


def load_metric_descriptors(instance_path):
    descriptors = []
    pattern = os.path.join(instance_path, "metric-data-*.json")
    for path in sorted(glob.glob(pattern)):
        data = load_json_auto(path)
        if not data:
            continue
        csv_path = path.replace(".json", ".csv.xz")
        if not os.path.exists(csv_path):
            csv_path = path.replace(".json", ".csv")
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            entry["_csv_path"] = csv_path
            entry["_source_path"] = path
        descriptors.extend(entries)
    return descriptors


def load_metric_values(csv_path, idx_set=None):
    global _csv_cache

    cache_key = csv_path
    if cache_key in _csv_cache:
        cached = _csv_cache[cache_key]
        if idx_set is None:
            return cached
        return {idx: vals for idx, vals in cached.items() if idx in idx_set}

    all_values = defaultdict(list)

    if not os.path.exists(csv_path):
        return {}

    try:
        if csv_path.endswith(".xz"):
            fh = lzma.open(csv_path, "rt")
        else:
            fh = open(csv_path, "r")

        row_count = 0
        error_count = 0
        with fh:
            reader = csv.reader(fh)
            for row in reader:
                row_count += 1
                if len(row) < 4:
                    error_count += 1
                    continue
                try:
                    idx = int(row[0])
                    value = float(row[3])
                    all_values[idx].append(value)
                except (ValueError, IndexError):
                    error_count += 1
                    continue

        if error_count > 0 and row_count > 0:
            error_pct = (error_count / row_count) * 100
            if error_pct > 50:
                log_warn(f"High error rate ({error_pct:.0f}%) in {csv_path}")

    except (OSError, lzma.LZMAError) as e:
        log_warn(f"Error reading {csv_path}: {e}")
        return {}

    _csv_cache[cache_key] = dict(all_values)

    if idx_set is None:
        return dict(all_values)
    return {idx: vals for idx, vals in all_values.items() if idx in idx_set}


def compute_stats(values):
    if not values:
        return {"count": 0, "mean": None, "min": None, "max": None,
                "stddev": None, "p50": None, "p95": None, "p99": None}

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mean = sum(sorted_vals) / n

    variance = sum((v - mean) ** 2 for v in sorted_vals) / n if n > 1 else 0
    stddev = variance ** 0.5

    def percentile(pct):
        k = (n - 1) * (pct / 100.0)
        f = int(k)
        c = f + 1 if f + 1 < n else f
        d = k - f
        return sorted_vals[f] + d * (sorted_vals[c] - sorted_vals[f])

    return {
        "count": n,
        "mean": mean,
        "min": sorted_vals[0],
        "max": sorted_vals[-1],
        "stddev": stddev,
        "p50": percentile(50),
        "p95": percentile(95),
        "p99": percentile(99),
    }


def get_time_range(csv_path, idx_set=None):
    if not os.path.exists(csv_path):
        return None, None

    min_begin = None
    max_end = None

    try:
        if csv_path.endswith(".xz"):
            fh = lzma.open(csv_path, "rt")
        else:
            fh = open(csv_path, "r")

        with fh:
            reader = csv.reader(fh)
            for row in reader:
                if len(row) < 4:
                    continue
                try:
                    idx = int(row[0])
                    if idx_set is not None and idx not in idx_set:
                        continue
                    begin = float(row[1])
                    end = float(row[2])
                    if min_begin is None or begin < min_begin:
                        min_begin = begin
                    if max_end is None or end > max_end:
                        max_end = end
                except (ValueError, IndexError):
                    continue

    except (OSError, lzma.LZMAError):
        pass

    return min_begin, max_end


# ---------------------------------------------------------------------------
# Phase 4 - Analysis
# ---------------------------------------------------------------------------

def analyze_primary_metrics(profile, bench_descs, profiler_descs):
    primary_metrics = profile.get("primary_metrics", [])
    if not primary_metrics:
        return []

    results = []
    all_descs = bench_descs + profiler_descs

    for pm in primary_metrics:
        source = pm.get("source", "")
        metric_type = pm.get("type", "")
        label = pm.get("label", metric_type)
        aggregation = pm.get("aggregation", "mean")
        thresholds = pm.get("thresholds", {})
        names_filter = pm.get("names", None)

        matching = find_descriptors(all_descs, source, metric_type, names_filter)

        if not matching:
            results.append({
                "label": label,
                "source": source,
                "type": metric_type,
                "value": None,
                "formatted": "N/A",
                "status": STATUS_NO_DATA,
                "detail": "no matching descriptors found",
            })
            continue

        all_values = []
        for desc in matching:
            csv_path = desc.get("_csv_path", "")
            idx = desc.get("idx")
            if csv_path and idx is not None:
                vals = load_metric_values(csv_path, {idx})
                if idx in vals:
                    all_values.extend(vals[idx])

        if not all_values:
            results.append({
                "label": label,
                "source": source,
                "type": metric_type,
                "value": None,
                "formatted": "N/A",
                "status": STATUS_NO_DATA,
                "detail": "no values loaded",
            })
            continue

        agg_value = compute_aggregate(all_values, aggregation)
        if isinstance(agg_value, list):
            agg_value = safe_mean(agg_value)

        threshold_result = evaluate_threshold(agg_value, thresholds)
        results.append({
            "label": label,
            "source": source,
            "type": metric_type,
            "value": agg_value,
            "formatted": format_value(agg_value, metric_type),
            "status": threshold_result["status"],
            "detail": threshold_result["detail"],
        })

    return results


def analyze_tool_correlations(profile, run_dir, tools, all_tool_descs=None):
    correlations = profile.get("tool_correlations", [])
    if not correlations:
        return [], []

    results = []
    alerts = []

    for corr in correlations:
        tool_name = corr.get("tool", "")
        condition = corr.get("condition", "")
        group_source = corr.get("source", tool_name)

        if condition == "tool_present" and tool_name not in tools:
            continue
        if isinstance(condition, dict) and condition.get("tool_present") and condition["tool_present"] not in tools:
            continue
        if not condition and tool_name and tool_name not in tools:
            continue

        instances = discover_tool_instances(run_dir, tool_name)
        if not instances:
            if all_tool_descs and all_tool_descs.get(tool_name):
                instance_descs = all_tool_descs[tool_name]
            else:
                continue
        else:
            instance_descs = []
            for inst_path in instances:
                instance_descs.extend(load_metric_descriptors(inst_path))

        metrics_list = corr.get("metrics", [])
        if not metrics_list:
            source = group_source
            metric_type = corr.get("type", "")
            label = corr.get("label", f"{tool_name}/{metric_type}")
            aggregation = corr.get("aggregation", "mean")
            thresholds = corr.get("thresholds", {})
            names_keys = corr.get("filter", {}).get("names", [])
            dynamic = corr.get("dynamic", False)
            metrics_list = [{
                "type": metric_type, "label": label, "aggregation": aggregation,
                "thresholds": thresholds, "filter": {"names": names_keys},
                "dynamic": dynamic, "source": source,
            }]

        for metric_def in metrics_list:
            source = metric_def.get("source", group_source)
            metric_type = metric_def.get("type", "")
            label = metric_def.get("label", f"{tool_name}/{metric_type}")
            aggregation = metric_def.get("aggregation", "mean")
            thresholds = metric_def.get("thresholds", {})
            names_keys = metric_def.get("filter", {}).get("names", [])
            dynamic = metric_def.get("dynamic", False)

            if dynamic:
                type_patterns = [metric_type] if metric_type else ["*"]
                discovered_types = set()
                for desc in instance_descs:
                    dt = desc.get("desc", {}).get("type", "")
                    for pat in type_patterns:
                        if fnmatch.fnmatch(dt, pat):
                            discovered_types.add(dt)
                for disc_type in sorted(discovered_types):
                    disc_label = label.replace("{type}", disc_type) if "{type}" in label else f"{label}/{disc_type}"
                    _process_correlation(
                        instance_descs, source, disc_type, disc_label,
                        aggregation, thresholds, names_keys, tool_name,
                        results, alerts
                    )
            else:
                _process_correlation(
                    instance_descs, source, metric_type, label,
                    aggregation, thresholds, names_keys, tool_name,
                    results, alerts
                )

    return results, alerts


def _process_correlation(descs, source, metric_type, label, aggregation,
                         thresholds, names_keys, tool_name, results, alerts):
    matching = find_descriptors(descs, source, metric_type)
    if not matching:
        return

    groups = group_by_names(matching, names_keys)

    for group_key, group_descs in groups.items():
        all_values = []
        for desc in group_descs:
            csv_path = desc.get("_csv_path", "")
            idx = desc.get("idx")
            if csv_path and idx is not None:
                vals = load_metric_values(csv_path, {idx})
                if idx in vals:
                    all_values.extend(vals[idx])

        if not all_values:
            continue

        agg_value = compute_aggregate(all_values, aggregation)
        if isinstance(agg_value, list):
            agg_value = safe_mean(agg_value)

        threshold_result = evaluate_threshold(agg_value, thresholds)

        entry = {
            "tool": tool_name,
            "label": label,
            "group": group_key,
            "type": metric_type,
            "value": agg_value,
            "formatted": format_value(agg_value, metric_type),
            "status": threshold_result["status"],
            "detail": threshold_result["detail"],
        }
        results.append(entry)

        if threshold_result["status"] in (STATUS_WARN, STATUS_CRITICAL):
            alerts.append(entry)


def analyze_profiler_correlations(profile, profiler_descs, bench_descs):
    correlations = profile.get("profiler_correlations", [])
    if not correlations:
        return [], []

    results = []
    alerts = []
    all_descs = profiler_descs + bench_descs

    available_sources = set()
    for d in all_descs:
        available_sources.add(d.get("desc", {}).get("source", ""))

    for corr in correlations:
        condition = corr.get("condition", "")
        group_source = corr.get("source", "")

        if condition == "source_present" and group_source not in available_sources:
            continue
        if isinstance(condition, dict) and condition.get("source_present"):
            if condition["source_present"] not in available_sources:
                continue

        metrics_list = corr.get("metrics", [])
        if not metrics_list:
            metrics_list = [{
                "source": group_source,
                "type": corr.get("type", ""),
                "label": corr.get("label", ""),
                "aggregation": corr.get("aggregation", "mean"),
                "thresholds": corr.get("thresholds", {}),
                "filter": corr.get("filter", {}),
                "dynamic": corr.get("dynamic", False),
            }]

        for metric_def in metrics_list:
            source = metric_def.get("source", group_source)
            metric_type = metric_def.get("type", "")
            label = metric_def.get("label", f"{source}/{metric_type}")
            aggregation = metric_def.get("aggregation", "mean")
            thresholds = metric_def.get("thresholds", {})
            names_keys = metric_def.get("filter", {}).get("names", [])
            dynamic = metric_def.get("dynamic", False)

            if dynamic:
                discovered_types = set()
                for desc in all_descs:
                    d = desc.get("desc", {})
                    if d.get("source") == source:
                        dt = d.get("type", "")
                        if fnmatch.fnmatch(dt, metric_type if metric_type else "*"):
                            discovered_types.add(dt)
                for disc_type in sorted(discovered_types):
                    disc_label = label.replace("{type}", disc_type) if "{type}" in label else f"{label}/{disc_type}"
                    _process_correlation(
                        all_descs, source, disc_type, disc_label,
                        aggregation, thresholds, names_keys, source,
                        results, alerts
                    )
            else:
                _process_correlation(
                    all_descs, source, metric_type, label,
                    aggregation, thresholds, names_keys, source,
                    results, alerts
                )

    return results, alerts


def detect_patterns(profile, bench_descs, profiler_descs, tool_corr_results):
    patterns = profile.get("patterns", [])
    if not patterns:
        return []

    detected = []
    all_descs = bench_descs + profiler_descs

    all_metric_data = {}
    for desc in all_descs:
        source = desc.get("desc", {}).get("source", "")
        mtype = desc.get("desc", {}).get("type", "")
        key = f"{source}/{mtype}"
        if key not in all_metric_data:
            all_metric_data[key] = []
        csv_path = desc.get("_csv_path", "")
        idx = desc.get("idx")
        if csv_path and idx is not None:
            vals = load_metric_values(csv_path, {idx})
            if idx in vals:
                all_metric_data[key].extend(vals[idx])

    for tc in tool_corr_results:
        key = f"{tc.get('tool', '')}/{tc.get('type', '')}"
        if key not in all_metric_data:
            all_metric_data[key] = []
        if tc.get("value") is not None:
            all_metric_data[key].append(tc["value"])

    for pattern in patterns:
        name = pattern.get("name", "unnamed")
        severity = pattern.get("severity", "INFO")
        description = pattern.get("description", "")
        recommendation = pattern.get("recommendation", "")
        conditions = pattern.get("conditions", [])

        if not conditions:
            continue

        all_met = True
        for cond in conditions:
            source = cond.get("source", "")
            mtype = cond.get("type", "")
            check = cond.get("check", "")
            threshold = cond.get("threshold", 0)

            key = f"{source}/{mtype}"
            values = all_metric_data.get(key, [])

            if not values:
                all_met = False
                break

            if not _evaluate_condition(values, check, threshold):
                all_met = False
                break

        if all_met:
            detected.append({
                "name": name,
                "severity": severity,
                "description": description,
                "recommendation": recommendation,
            })

    return detected


def _evaluate_condition(values, check, threshold):
    if not values:
        return False

    if check == "any_above":
        return any(v > threshold for v in values)
    elif check == "mean_above":
        return safe_mean(values) > threshold
    elif check == "sum_above":
        return sum(values) > threshold
    elif check == "any_below":
        return any(v < threshold for v in values)
    elif check == "mean_below":
        return safe_mean(values) < threshold
    elif check == "value_above":
        return safe_mean(values) > threshold
    return False


def generate_recommendations(detected_patterns, alerts):
    recommendations = []

    for pattern in detected_patterns:
        if pattern.get("recommendation"):
            sev = pattern.get("severity", "MEDIUM")
            recommendations.append({
                "priority": sev,
                "text": pattern["recommendation"],
                "source": f"pattern:{pattern['name']}",
            })

    critical_tools = set()
    for alert in alerts:
        if alert["status"] == STATUS_CRITICAL:
            tool = alert.get("tool", "")
            label = alert.get("label", "")
            key = f"{tool}/{label}"
            if key not in critical_tools:
                critical_tools.add(key)
                recommendations.append({
                    "priority": "HIGH",
                    "text": f"Investigate {label} [{alert.get('group', '')}]: "
                            f"{alert.get('formatted', '')} exceeds critical threshold",
                    "source": f"alert:{key}",
                })

    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    recommendations.sort(key=lambda r: priority_order.get(r["priority"], 5))

    return recommendations


# ---------------------------------------------------------------------------
# Phase 5 - Compare
# ---------------------------------------------------------------------------

def run_comparison(current_results, baseline_dir, profiles_dir, profile_name):
    baseline_analysis = run_full_analysis(baseline_dir, profiles_dir, profile_name)
    if not baseline_analysis:
        return None

    current_primary = current_results.get("primary_metrics", [])
    baseline_primary = baseline_analysis.get("primary_metrics", [])

    comparison = []
    baseline_map = {m["label"]: m for m in baseline_primary}

    for metric in current_primary:
        label = metric["label"]
        baseline_metric = baseline_map.get(label)

        entry = {
            "label": label,
            "type": metric.get("type", ""),
            "current_value": metric.get("value"),
            "current_formatted": metric.get("formatted", "N/A"),
            "baseline_value": None,
            "baseline_formatted": "N/A",
            "delta_pct": None,
            "status": STATUS_NO_DATA,
        }

        if baseline_metric and baseline_metric.get("value") is not None:
            entry["baseline_value"] = baseline_metric["value"]
            entry["baseline_formatted"] = baseline_metric["formatted"]

            if metric.get("value") is not None and baseline_metric["value"] != 0:
                delta = ((metric["value"] - baseline_metric["value"])
                         / abs(baseline_metric["value"])) * 100
                entry["delta_pct"] = delta

                lower_better = is_lower_better(metric.get("type", ""))

                if lower_better:
                    if delta > REGRESSION_THRESHOLD_PCT:
                        entry["status"] = "REGRESSION"
                    elif delta < -REGRESSION_THRESHOLD_PCT:
                        entry["status"] = "IMPROVEMENT"
                    else:
                        entry["status"] = STATUS_OK
                else:
                    if delta < -REGRESSION_THRESHOLD_PCT:
                        entry["status"] = "REGRESSION"
                    elif delta > REGRESSION_THRESHOLD_PCT:
                        entry["status"] = "IMPROVEMENT"
                    else:
                        entry["status"] = STATUS_OK

        comparison.append(entry)

    return {
        "baseline_dir": baseline_dir,
        "baseline_info": baseline_analysis.get("run_info", {}),
        "metrics": comparison,
    }


# ---------------------------------------------------------------------------
# Phase 6 - Output Formatting
# ---------------------------------------------------------------------------

def format_markdown(analysis, top_n, no_color, sections):
    lines = []
    run_info = analysis.get("run_info", {})
    profile_name = analysis.get("profile_name", "")

    show_all = "all" in sections
    show_section = lambda s: show_all or s in sections

    benchmark = run_info.get("benchmark", "unknown")
    run_id_short = run_info.get("run_id_short", "")
    lines.append(f"# Run Analysis: {benchmark} ({run_id_short})")
    lines.append("")

    if show_section("overview"):
        lines.append(f"**Profile**: {profile_name or 'none'}")
        lines.append(f"**Timestamp**: {run_info.get('timestamp', 'N/A')}")

        tags = analysis.get("tags", {})
        if tags.get("scenario"):
            lines.append(f"**Scenario**: {tags['scenario']}")

        dut_line_parts = []
        if tags.get("dut"):
            dut_line_parts.append(f"**DUT**: {tags['dut']}")
        tools = analysis.get("tools", [])
        if tools:
            tool_str = ", ".join(tools)
            dut_line_parts.append(f"**Tools**: {tool_str}")
        if dut_line_parts:
            lines.append(" | ".join(dut_line_parts))

        mode = analysis.get("mode")
        if mode:
            backend = tags.get("trafficgen_backend", "")
            lines.append(f"**Mode**: {mode} ({backend})")

        duration = analysis.get("duration_ms")
        if duration is not None:
            lines.append(f"**Duration**: {format_duration_ms(duration)}")

        num_iterations = analysis.get("num_iterations", 0)
        num_samples = analysis.get("num_samples", 0)
        if num_iterations > 0:
            lines.append(f"**Iterations**: {num_iterations} | "
                         f"**Samples**: {num_samples}")

        lines.append("")

    if show_section("metrics"):
        primary = analysis.get("primary_metrics", [])
        if primary:
            lines.append("## Primary Metrics")
            lines.append("")
            lines.append("| Metric | Value | Status |")
            lines.append("|--------|-------|--------|")
            for m in primary:
                status = _format_status(m["status"], no_color)
                lines.append(f"| {m['label']} | {m['formatted']} | {status} |")
            lines.append("")

    if show_section("alerts"):
        alerts = analysis.get("alerts", [])
        if alerts:
            lines.append(f"## Alerts ({len(alerts)})")
            lines.append("")
            for alert in alerts:
                severity = f"**{alert['status']}**"
                tool = alert.get("tool", "")
                label = alert.get("label", "")
                group = alert.get("group", "")
                formatted = alert.get("formatted", "")
                detail = alert.get("detail", "")
                lines.append(f"{severity} {tool} / {label} [{group}]: "
                             f"{formatted} ({detail})")
            lines.append("")

    if show_section("patterns"):
        patterns = analysis.get("detected_patterns", [])
        if patterns:
            lines.append("## Detected Patterns")
            lines.append("")
            for p in patterns:
                lines.append(f"### {p['severity']} {p['name']}")
                if p.get("description"):
                    lines.append(p["description"])
                if p.get("recommendation"):
                    lines.append(f"**Action**: {p['recommendation']}")
                lines.append("")

    if show_section("tools"):
        tool_results = analysis.get("tool_correlation_results", [])
        if tool_results:
            lines.append("## Tool Summary")
            lines.append("")
            _format_tool_summary(lines, tool_results, top_n)

    if show_section("metrics"):
        comparison = analysis.get("comparison")
        if comparison:
            lines.append("## Comparison")
            lines.append("")
            baseline_info = comparison.get("baseline_info", {})
            lines.append(f"Baseline: {baseline_info.get('benchmark', '?')} "
                         f"({baseline_info.get('run_id_short', '?')})")
            lines.append("")
            lines.append("| Metric | Current | Baseline | Delta | Status |")
            lines.append("|--------|---------|----------|-------|--------|")
            for m in comparison.get("metrics", []):
                delta_str = f"{m['delta_pct']:+.1f}%" if m["delta_pct"] is not None else "N/A"
                status = _format_status(m["status"], no_color)
                lines.append(f"| {m['label']} | {m['current_formatted']} | "
                             f"{m['baseline_formatted']} | {delta_str} | {status} |")
            lines.append("")

    if show_section("recommendations"):
        recs = analysis.get("recommendations", [])
        if recs:
            lines.append("## Recommendations")
            lines.append("")
            for i, rec in enumerate(recs, 1):
                lines.append(f"{i}. **[{rec['priority']}]** {rec['text']}")
            lines.append("")

    return "\n".join(lines)


def _format_status(status, no_color):
    if no_color:
        return status
    indicators = {
        STATUS_OK: "OK",
        STATUS_WARN: "WARN",
        STATUS_CRITICAL: "CRITICAL",
        STATUS_NO_DATA: "NO_DATA",
        "REGRESSION": "REGRESSION",
        "IMPROVEMENT": "IMPROVEMENT",
    }
    return indicators.get(status, status)


def _format_tool_summary(lines, tool_results, top_n):
    by_tool = defaultdict(list)
    for r in tool_results:
        by_tool[r.get("tool", "unknown")].append(r)

    for tool_name, entries in sorted(by_tool.items()):
        lines.append(f"### {tool_name}")
        lines.append("")

        if not entries:
            continue

        type_groups = defaultdict(list)
        for e in entries:
            type_groups[e.get("type", "")].append(e)

        for mtype, type_entries in sorted(type_groups.items()):
            if len(type_entries) > 1:
                lines.append(f"**{mtype}**:")
                lines.append("")
                lines.append("| Group | Value | Status |")
                lines.append("|-------|-------|--------|")
                sorted_entries = sorted(type_entries,
                                        key=lambda x: x.get("value") or 0,
                                        reverse=True)
                for e in sorted_entries[:top_n]:
                    lines.append(f"| {e.get('group', '')} | "
                                 f"{e.get('formatted', '')} | "
                                 f"{e.get('status', '')} |")
                if len(sorted_entries) > top_n:
                    lines.append(f"| ... ({len(sorted_entries) - top_n} more) "
                                 f"| | |")
                lines.append("")
            else:
                e = type_entries[0]
                lines.append(f"- **{mtype}** [{e.get('group', '')}]: "
                             f"{e.get('formatted', '')} ({e.get('status', '')})")

        lines.append("")


def format_json_output(analysis):
    clean = _clean_for_json(analysis)
    return json.dumps(clean, indent=2, default=str)


def _clean_for_json(obj):
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items()
                if not k.startswith("_")}
    elif isinstance(obj, list):
        return [_clean_for_json(item) for item in obj]
    return obj


def format_summary(analysis):
    run_info = analysis.get("run_info", {})
    benchmark = run_info.get("benchmark", "unknown")
    run_id_short = run_info.get("run_id_short", "")

    primary = analysis.get("primary_metrics", [])
    worst_status = STATUS_OK
    metric_parts = []

    for m in primary:
        if m["status"] == STATUS_CRITICAL:
            worst_status = STATUS_CRITICAL
        elif m["status"] == STATUS_WARN and worst_status != STATUS_CRITICAL:
            worst_status = STATUS_WARN
        metric_parts.append(f"{m['label']}={m['formatted']}")

    metrics_str = " ".join(metric_parts) if metric_parts else "no_metrics"
    return f"{worst_status}: {benchmark} ({run_id_short}) {metrics_str}"


# ---------------------------------------------------------------------------
# Main Analysis Pipeline
# ---------------------------------------------------------------------------

def run_full_analysis(run_dir, profiles_dir, profile_name=None):
    global _csv_cache
    _csv_cache = {}

    if not os.path.isdir(run_dir):
        return None

    log_verbose(f"Analyzing run: {run_dir}")

    # Phase 1: Discovery
    run_info = parse_run_directory(run_dir)
    log_verbose(f"Benchmark: {run_info['benchmark']}, UUID: {run_info['uuid']}")

    run_config = load_run_config(run_dir)
    tags = extract_tags(run_config)
    tools = load_tool_params(run_dir)
    mode = detect_trafficgen_mode(tags)

    log_verbose(f"Tags: {len(tags)}, Tools: {tools}, Mode: {mode}")

    # Phase 2: Profile Resolution
    profile, resolved_profile_name = resolve_profile(
        profiles_dir, run_info["benchmark"], tags, tools, profile_name
    )

    # Phase 3: Metric Loading
    log_verbose("Loading benchmark results...")
    bench_descs = load_benchmark_results(run_dir)
    log_verbose(f"Loaded {len(bench_descs)} benchmark descriptors")

    log_verbose("Loading profiler data...")
    profiler_descs = load_profiler_data(run_dir)
    log_verbose(f"Loaded {len(profiler_descs)} profiler descriptors")

    if mode is None and bench_descs:
        for desc in bench_descs:
            source = desc.get("desc", {}).get("source", "")
            if "trex" in source.lower():
                if "astf" in source.lower():
                    mode = "astf"
                else:
                    mode = "stl"
                break

    iteration_dirs = sorted(glob.glob(
        os.path.join(run_dir, "iterations", "iteration-*")))
    num_iterations = len(iteration_dirs)
    num_samples = 0
    for it_dir in iteration_dirs:
        num_samples += len(glob.glob(os.path.join(it_dir, "sample-*")))

    run_duration_ms = None
    if bench_descs:
        first_csv = bench_descs[0].get("_csv_path", "")
        first_idx = bench_descs[0].get("idx")
        if first_csv and first_idx is not None:
            all_idx = set()
            for d in bench_descs:
                if d.get("_csv_path") == first_csv and d.get("idx") is not None:
                    all_idx.add(d["idx"])
            min_begin, max_end = get_time_range(first_csv, all_idx)
            if min_begin is not None and max_end is not None:
                run_duration_ms = max_end - min_begin

    # Phase 4: Analysis
    log_verbose("Analyzing primary metrics...")
    primary_metrics = analyze_primary_metrics(profile, bench_descs, profiler_descs)

    log_verbose("Analyzing tool correlations...")
    tool_corr_results, tool_alerts = analyze_tool_correlations(
        profile, run_dir, tools
    )

    log_verbose("Analyzing profiler correlations...")
    prof_corr_results, prof_alerts = analyze_profiler_correlations(
        profile, profiler_descs, bench_descs
    )

    all_alerts = tool_alerts + prof_alerts

    log_verbose("Detecting patterns...")
    detected_patterns = detect_patterns(
        profile, bench_descs, profiler_descs, tool_corr_results
    )

    recommendations = generate_recommendations(detected_patterns, all_alerts)

    return {
        "run_info": run_info,
        "profile_name": resolved_profile_name,
        "tags": tags,
        "tools": tools,
        "mode": mode,
        "num_iterations": num_iterations,
        "num_samples": num_samples,
        "duration_ms": run_duration_ms,
        "primary_metrics": primary_metrics,
        "tool_correlation_results": tool_corr_results + prof_corr_results,
        "alerts": all_alerts,
        "detected_patterns": detected_patterns,
        "recommendations": recommendations,
    }


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        description="Crucible Run Analysis Engine - "
                    "Profile-driven benchmark result analysis"
    )
    parser.add_argument(
        "--run-dir", required=True,
        help="Path to the run directory to analyze"
    )
    parser.add_argument(
        "--profiles-dir",
        help="Absolute path to user profiles directory"
    )
    parser.add_argument(
        "--profile",
        help="Override profile selection (name or filename)"
    )
    parser.add_argument(
        "--format", choices=["markdown", "json", "summary"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    parser.add_argument(
        "--section", default="all",
        help="Comma-separated sections: "
             "overview,metrics,alerts,patterns,tools,recommendations,all "
             "(default: all)"
    )
    parser.add_argument(
        "--compare",
        help="Path to baseline run directory for comparison"
    )
    parser.add_argument(
        "--top", type=int, default=10,
        help="Limit per-instance tables to N rows (default: 10)"
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable status indicators"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print progress messages to stderr"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress all stderr output"
    )
    return parser


def main():
    global _verbose, _quiet

    parser = build_parser()
    args = parser.parse_args()

    _verbose = args.verbose
    _quiet = args.quiet

    run_dir = os.path.abspath(args.run_dir)
    if not os.path.isdir(run_dir):
        print(json.dumps({"error": f"Run directory not found: {run_dir}"}))
        sys.exit(EXIT_ERROR)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    profiles_dir = resolve_profiles_dir(script_dir, args.profiles_dir)
    profiles_dir = os.path.abspath(profiles_dir)

    if not os.path.isdir(profiles_dir):
        log_warn(f"Profiles directory not found: {profiles_dir}")

    sections = set(s.strip() for s in args.section.split(","))

    had_partial_failure = False

    analysis = run_full_analysis(run_dir, profiles_dir, args.profile)
    if analysis is None:
        print(json.dumps({"error": f"Analysis failed for: {run_dir}"}))
        sys.exit(EXIT_ERROR)

    if args.compare:
        compare_dir = os.path.abspath(args.compare)
        if not os.path.isdir(compare_dir):
            log_warn(f"Comparison directory not found: {compare_dir}")
            had_partial_failure = True
        else:
            comparison = run_comparison(analysis, compare_dir, profiles_dir,
                                        args.profile)
            if comparison:
                analysis["comparison"] = comparison
            else:
                log_warn("Comparison analysis returned no results")
                had_partial_failure = True

    has_any_data = any(
        m["status"] != STATUS_NO_DATA
        for m in analysis.get("primary_metrics", [])
    )
    if not has_any_data and analysis.get("primary_metrics"):
        had_partial_failure = True

    if args.format == "markdown":
        output = format_markdown(analysis, args.top, args.no_color, sections)
    elif args.format == "json":
        output = format_json_output(analysis)
    elif args.format == "summary":
        output = format_summary(analysis)
    else:
        output = format_markdown(analysis, args.top, args.no_color, sections)

    print(output)

    if had_partial_failure:
        sys.exit(EXIT_PARTIAL)
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()

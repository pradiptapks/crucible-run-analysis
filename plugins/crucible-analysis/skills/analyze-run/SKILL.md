---
description: Analyze a crucible benchmark run — summarize results, detect anomalies, correlate tool metrics
---

Analyze a crucible benchmark run using profile-driven analysis. Extracts primary benchmark metrics, evaluates tool correlations, and detects cross-tool anomaly patterns.

Arguments: $ARGUMENTS

## Instructions

1. Parse the arguments to determine the run directory and any options:
   - If the argument is a full path (e.g., `/var/lib/crucible/run/trafficgen--2026-06-05_...`), use it directly
   - If the argument is `latest` or no argument is given, resolve it: `readlink -f /var/lib/crucible/run/latest`
   - If the argument is a partial UUID (e.g., `8ab97461`), find the matching directory: `ls -d /var/lib/crucible/run/*--${partial}*`
   - Extract optional flags from arguments:
     - `--profile <name>` or `--profile /absolute/path`: pass through to engine
     - `--compare <path-or-partial-uuid>`: resolve the comparison path the same way as the main run
     - `--section <sections>`: pass through to engine

2. Run the analysis engine:
   ```
   python3 ${CRUCIBLE_HOME}/subprojects/core/crucible-run-analysis/bin/analyze-run.py \
     --run-dir <resolved-run-dir> \
     --format markdown \
     --quiet \
     [--profile <name>] \
     [--compare <resolved-compare-dir>] \
     [--section <sections>]
   ```
   If the user provided an absolute path for --profile that looks like a directory, pass it as `--profiles-dir` instead.

3. Display the stdout output verbatim as the response. The engine produces pre-formatted markdown — do not parse, reformat, or add additional structure. Exit codes:
   - **Exit 0**: Success — display output as-is
   - **Exit 2**: Partial — no benchmark measurement data found, but report was still generated. Display the output and note that measurement data may not yet be available for this run.
   - **Exit 1**: Error — display the error message and suggest:
     - Check that the run directory exists and contains valid data
     - Run `crucible ls` to see available runs
     - Check that PyYAML is installed (`dnf install python3-pyyaml`)

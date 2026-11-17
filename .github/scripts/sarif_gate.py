"""Fail the job when a SARIF file has a result with security-severity >= threshold.

CodeQL uploads every finding to the Security tab, but by default the job stays
green. This gate turns high/critical findings into a red build.
"""
import glob
import json
import sys

folder = sys.argv[1] if len(sys.argv) > 1 else "sarif-results"
threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 7.0
blocking = []
total = 0

for path in glob.glob(f"{folder}/*.sarif"):
    with open(path, encoding="utf-8") as fh:
        sarif = json.load(fh)
    for run in sarif.get("runs", []):
        rules = {}
        tool = run.get("tool", {})
        for component in [tool.get("driver", {})] + tool.get("extensions", []):
            for rule in component.get("rules", []):
                rules[rule["id"]] = rule
        for result in run.get("results", []):
            total += 1
            rule_id = result.get("ruleId") or result.get("rule", {}).get("id", "?")
            props = rules.get(rule_id, {}).get("properties", {})
            severity = float(props.get("security-severity") or 0)
            loc = result["locations"][0]["physicalLocation"]
            uri = loc["artifactLocation"]["uri"]
            line = loc.get("region", {}).get("startLine", 1)
            print(f"{rule_id} severity={severity} {uri}:{line}")
            if severity >= threshold:
                msg = result.get("message", {}).get("text", "").splitlines()[0]
                blocking.append((rule_id, severity, uri, line, msg))

print(f"{total} finding(s), {len(blocking)} at or above {threshold}")
for rule_id, severity, uri, line, msg in blocking:
    print(f"::error file={uri},line={line},title=CodeQL {rule_id} ({severity})::{msg}")
sys.exit(1 if blocking else 0)

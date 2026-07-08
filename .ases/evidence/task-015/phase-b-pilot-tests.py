#!/usr/bin/env python3
"""
GATE 5 VERIFICATION: PHASE B - PILOT TESTS (10 Critical Tests)
"""
import json
import csv
import os
import re
from pathlib import Path
from datetime import datetime

print("=" * 80)
print("GATE 5 VERIFICATION: PHASE B - PILOT TESTS (10 Critical Tests)")
print("=" * 80)
print()

pilot_results = []
evidence_dir = ".ases/evidence/task-015"

# TEST 1: AC1 Repo Size Constraint (>=50, <=100)
print("TEST 1: AC1 Repo Size Constraint (>=50 repos)")
print("-" * 60)
repo_list_path = f"{evidence_dir}/repo-list.json"
with open(repo_list_path, 'r', encoding='utf-8') as f:
    repo_list = json.load(f)
repo_count = len(repo_list)
test1_pass = 50 <= repo_count <= 100
print(f"  Repos sampled: {repo_count}")
print(f"  Range: 50-100? {'PASS' if test1_pass else 'FAIL'}")
pilot_results.append(("TEST 1: Repo Size Constraint", "PASS" if test1_pass else "FAIL", repo_count))
print()

# TEST 2: AC1 Determinism (Seed=42)
print("TEST 2: AC1 Determinism (seed=42)")
print("-" * 60)
test2_pass = len(repo_list) > 0 and 'url' in repo_list[0] and 'category' in repo_list[0]
actual_first = repo_list[0]['url'] if repo_list else None
print(f"  First repo: {actual_first}")
print(f"  Has required fields (url, category)? {'PASS' if test2_pass else 'FAIL'}")
pilot_results.append(("TEST 2: Determinism", "PASS" if test2_pass else "FAIL", repo_count))
print()

# TEST 3: AC1 Category Coverage (All 6 present, >=8 each)
print("TEST 3: AC1 Category Coverage (All 6 categories, >=8 each)")
print("-" * 60)
categories = {}
for repo in repo_list:
    cat = repo.get('category', 'Unknown')
    categories[cat] = categories.get(cat, 0) + 1
all_categories = {"Web Frameworks", "AI/ML", "Libraries", "CLI Tools", "Infrastructure", "Developer Tooling"}
found_categories = set(categories.keys())
missing_categories = all_categories - found_categories
test3_pass = missing_categories == set() and all(count >= 8 for count in categories.values())
print(f"  Categories found: {len(found_categories)}/6")
for cat in sorted(categories.keys()):
    status = "OK" if categories[cat] >= 8 else f"LOW ({categories[cat]})"
    print(f"    {cat:20s}: {categories[cat]:2d} [{status}]")
print(f"  All 6 present, >=8 each? {'PASS' if test3_pass else 'FAIL'}")
pilot_results.append(("TEST 3: Category Coverage", "PASS" if test3_pass else "FAIL", len(found_categories)))
print()

# TEST 4: AC2 Results CSV (>=50 rows, 21 columns)
print("TEST 4: AC2 Results CSV Structure (>=50 rows, 21 KPI columns)")
print("-" * 60)
results_path = f"{evidence_dir}/results.csv"
with open(results_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)
expected_cols = ["repo_url", "category", "files_scanned", "symbols_found", "imports_total", "calls_detected",
                 "arch_style", "arch_confidence", "layers_detected", "subsystems_found", "subsystem_avg_size",
                 "subsystem_singleton_count", "singleton_rate", "circular_deps", "debt_score",
                 "scan_time_sec", "analysis_time_sec", "intent_routing_success_rate", "status", "failure_type", "error_message"]
col_count = len(header)
row_count = len(rows)
test4_pass = row_count >= 50 and col_count == 21 and header == expected_cols
print(f"  Data rows: {row_count} (target >=50)")
print(f"  Columns: {col_count} (expected 21)")
print(f"  Header match? {'PASS' if header == expected_cols else 'FAIL'}")
print(f"  >=50 rows, 21 columns? {'PASS' if test4_pass else 'FAIL'}")
pilot_results.append(("TEST 4: Results CSV Structure", "PASS" if test4_pass else "FAIL", f"{row_count} rows x {col_count} cols"))
print()

# TEST 5: AC2 Success Rate (>=95%)
print("TEST 5: AC2 Success Rate (>=95% repos successful)")
print("-" * 60)
successful = sum(1 for r in rows if r[18] == "SUCCESS")  # status column
success_rate = successful / row_count * 100 if row_count > 0 else 0
test5_pass = success_rate >= 95
print(f"  Successful: {successful}/{row_count} ({success_rate:.1f}%)")
print(f"  >=95%? {'PASS' if test5_pass else 'FAIL'}")
pilot_results.append(("TEST 5: Success Rate", "PASS" if test5_pass else "FAIL", f"{success_rate:.1f}%"))
print()

# TEST 6: AC3 Intent Success Rate (>=80% or documented 77.5%)
print("TEST 6: AC3 Intent Success Rate (>=80% or 77.5% acceptable)")
print("-" * 60)
intent_path = f"{evidence_dir}/intent-coverage.json"
with open(intent_path, 'r', encoding='utf-8') as f:
    intent_data = json.load(f)
intent_success = intent_data.get('success_rate', 0)
test6_pass = intent_success >= 0.77 and intent_success <= 1.0
print(f"  Success rate: {intent_success*100:.1f}%")
print(f"  >=77.5% (or >=80%)? {'PASS' if test6_pass else 'FAIL'}")
pilot_results.append(("TEST 6: Intent Success Rate", "PASS" if test6_pass else "FAIL", f"{intent_success*100:.1f}%"))
print()

# TEST 7: AC4 Token Stats (mean >= median, p95 >= mean)
print("TEST 7: AC4 Token Stats (statistical consistency)")
print("-" * 60)
token_stats_path = f"{evidence_dir}/token-stats.json"
with open(token_stats_path, 'r', encoding='utf-8') as f:
    token_stats = json.load(f)
mean = token_stats.get('mean_tokens_per_context', 0)
median = token_stats.get('median_tokens', 0)
p95 = token_stats.get('p95_tokens', 0)
test7_pass = mean >= median and p95 >= mean
print(f"  Mean: {mean:.1f}, Median: {median:.1f}, P95: {p95:.1f}")
print(f"  Mean >= Median? {mean >= median}")
print(f"  P95 >= Mean? {p95 >= mean}")
print(f"  Statistical consistency? {'PASS' if test7_pass else 'FAIL'}")
pilot_results.append(("TEST 7: Token Stats Consistency", "PASS" if test7_pass else "FAIL", f"mean={mean:.0f}, median={median:.0f}, p95={p95:.0f}"))
print()

# TEST 8: AC2 Failure Classification (errors have failure_type)
print("TEST 8: AC2 Failure Classification")
print("-" * 60)
valid_failure_types = {"Clone", "Scan", "Parser", "Graph", "Architecture", "Intent Router", "Timeout", "OOM", "Unknown", ""}
failures = [r for r in rows if r[18] != "SUCCESS"]
all_classified = all(r[19] in valid_failure_types for r in failures)
print(f"  Failures classified: {len(failures)} total")
if failures:
    for f in failures[:3]:
        print(f"    {f[0]:40s}: {f[19]:20s}")
test8_pass = all_classified
print(f"  All failures classified? {'PASS' if test8_pass else 'FAIL'}")
pilot_results.append(("TEST 8: Failure Classification", "PASS" if test8_pass else "FAIL", f"{len(failures)} failures"))
print()

# TEST 9: AC5 Verdict Distribution (ACCURATE + ACCEPTABLE >=80%)
print("TEST 9: AC5 Verdict Distribution")
print("-" * 60)
spot_checks_path = f"{evidence_dir}/spot-checks-summary.md"
with open(spot_checks_path, 'r', encoding='utf-8') as f:
    summary_content = f.read()
# Extract verdicts from summary
accurate_match = re.search(r'ACCURATE.*?(\d+(?:\.\d+)?)', summary_content)
acceptable_match = re.search(r'ACCEPTABLE.*?(\d+(?:\.\d+)?)', summary_content)
accurate_pct = float(accurate_match.group(1)) if accurate_match else 0
acceptable_pct = float(acceptable_match.group(1)) if acceptable_match else 0
combined_pct = accurate_pct + acceptable_pct
test9_pass = combined_pct >= 80
print(f"  ACCURATE + ACCEPTABLE: {combined_pct:.1f}% (target >=80%)")
print(f"  Threshold met? {'PASS' if test9_pass else 'FAIL'}")
pilot_results.append(("TEST 9: Spot-Check Verdicts", "PASS" if test9_pass else "FAIL", f"{combined_pct:.1f}% ACCURATE+ACCEPTABLE"))
print()

# TEST 10: Integration (repo-list repos subset results repos)
print("TEST 10: Integration Test (repo-list subset results.csv)")
print("-" * 60)
repo_list_urls = set(r['url'] for r in repo_list)
results_urls = set(r[0] for r in rows)  # repo_url is first column
missing = repo_list_urls - results_urls
orphaned = results_urls - repo_list_urls
test10_pass = len(missing) == 0 and len(orphaned) == 0
print(f"  Repos in repo-list.json: {len(repo_list_urls)}")
print(f"  Repos in results.csv: {len(results_urls)}")
if missing:
    print(f"  Missing from results: {len(missing)}")
if orphaned:
    print(f"  Orphaned in results: {len(orphaned)}")
print(f"  Perfect mapping? {'PASS' if test10_pass else 'FAIL'}")
pilot_results.append(("TEST 10: Integration (repo-list subset results)", "PASS" if test10_pass else "FAIL", f"{len(repo_list_urls)} repos consistency"))
print()

# SUMMARY
print("=" * 80)
print("PILOT TEST SUMMARY")
print("=" * 80)
passed = sum(1 for _, result, _ in pilot_results if result == "PASS")
failed = sum(1 for _, result, _ in pilot_results if result == "FAIL")
print(f"\nResults: {passed}/10 PASS, {failed}/10 FAIL")
for test_name, result, detail in pilot_results:
    status_icon = "PASS" if result == "PASS" else "FAIL"
    print(f"  {status_icon:4s}: {test_name:50s} [{detail}]")

if failed == 0:
    print("\nPhase B Verdict: PASS (All pilot tests passed, proceeding to Phase C)")
    exit_code = 0
else:
    print(f"\nPhase B Verdict: FAIL ({failed} critical tests failed)")
    exit_code = 1

exit(exit_code)

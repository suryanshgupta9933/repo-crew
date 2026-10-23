#!/usr/bin/env python3
"""Drift check for repo-crew knowledge files.

Usage:
  check_drift.py [repo]                      report stale knowledge + uncovered paths
  check_drift.py [repo] --json               machine-readable report
  check_drift.py [repo] --stamp FILE         set FILE's verified_at to current HEAD

Knowledge files live in docs/crew/*.md (and docs/crew/shared/*.md) and carry
frontmatter with `covers:` (glob list) and `verified_at:` (git sha).
Only the standard library and git are needed.
"""
import argparse
import collections
import fnmatch
import glob
import json
import os
import re
import subprocess
import sys

IGNORE_UNCOVERED = (
    "docs/", ".github/", ".claude/", ".gitignore", "LICENSE", "README", "CHANGELOG",
)
IGNORE_SUFFIX = (".lock", ".md", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".gif", ".woff", ".woff2")


def git(root, *a):
    r = subprocess.run(["git", "-C", root, *a], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    fm, key = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^\s*-\s+", line) and key:
            fm.setdefault(key, []).append(re.sub(r"^\s*-\s+", "", line).strip().strip("'\""))
            continue
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                fm[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            elif val == "":
                fm[key] = []
            else:
                fm[key] = val.strip("'\"")
    return fm


def glob_to_regex(g):
    g = g.strip().lstrip("./")
    if g.endswith("/"):
        g += "**"
    out, i = "", 0
    while i < len(g):
        c = g[i]
        if g[i:i + 3] == "**/":
            out += "(?:.*/)?"
            i += 3
        elif g[i:i + 2] == "**":
            out += ".*"
            i += 2
        elif c == "*":
            out += "[^/]*"
            i += 1
        elif c == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(c)
            i += 1
    return re.compile("^" + out + "$")


def matches(path, regexes):
    return any(r.match(path) for r in regexes)


def knowledge_files(root):
    paths = sorted(glob.glob(os.path.join(root, "docs/crew/*.md")) +
                   glob.glob(os.path.join(root, "docs/crew/shared/*.md")))
    out = []
    for p in paths:
        base = os.path.basename(p)
        if base in ("DECISIONS.md", "ROSTER.md", "routing-evals.md"):
            continue
        with open(p, encoding="utf-8") as fh:
            fm = parse_frontmatter(fh.read())
        if fm.get("covers") is not None or fm.get("verified_at"):
            out.append((os.path.relpath(p, root), fm))
    return out


def stamp(root, file):
    head = (git(root, "rev-parse", "--short", "HEAD") or "").strip()
    if not head:
        sys.exit("cannot read HEAD (not a git repo or no commits)")
    path = file if os.path.isabs(file) else os.path.join(root, file)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if re.search(r"^verified_at:.*$", text, re.M):
        text = re.sub(r"^verified_at:.*$", f"verified_at: {head}", text, count=1, flags=re.M)
    elif re.match(r"^---\n", text):
        text = re.sub(r"^---\n", f"---\nverified_at: {head}\n", text, count=1)
    else:
        sys.exit(f"{file} has no frontmatter block to stamp")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"stamped {file} verified_at={head}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--stamp", metavar="FILE")
    args = ap.parse_args()
    root = os.path.abspath(args.repo)

    if git(root, "rev-parse", "--git-dir") is None:
        sys.exit("not a git repository")
    if args.stamp:
        return stamp(root, args.stamp)

    kfiles = knowledge_files(root)
    if not kfiles:
        sys.exit("no knowledge files with frontmatter found in docs/crew/")

    tracked = [f for f in (git(root, "ls-files") or "").splitlines() if f]
    all_regexes = []
    report = []
    for rel, fm in kfiles:
        covers = fm.get("covers") or []
        if isinstance(covers, str):
            covers = [covers]
        regs = [glob_to_regex(c) for c in covers]
        all_regexes += regs
        sha = fm.get("verified_at", "")
        entry = {"file": rel, "covers": covers, "verified_at": sha or None}
        if not covers:
            entry["status"] = "no-covers"
        elif not sha:
            entry["status"] = "unverified"
        elif git(root, "cat-file", "-t", sha) is None:
            entry["status"] = "unknown-sha"
        else:
            changed = (git(root, "diff", "--name-only", sha, "HEAD") or "").splitlines()
            hit = sorted(f for f in changed if matches(f, regs))
            commits = 0
            if hit:
                log = git(root, "log", "--oneline", f"{sha}..HEAD", "--", *hit) or ""
                commits = len([l for l in log.splitlines() if l])
            entry.update(changed_files=hit, commits=commits,
                         status="stale" if hit else "fresh")
        report.append(entry)

    uncovered = collections.Counter()
    for f in tracked:
        if f.startswith(IGNORE_UNCOVERED) or f.endswith(IGNORE_SUFFIX) or "/" not in f:
            continue
        if not matches(f, all_regexes):
            parts = f.split("/")
            uncovered["/".join(parts[:2]) if len(parts) > 2 else parts[0]] += 1

    result = {"knowledge": report, "uncovered": uncovered.most_common(15)}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("# Drift report\n")
        for e in report:
            line = f"- {e['file']}: {e['status']}"
            if e["status"] == "stale":
                line += f" ({len(e['changed_files'])} files / {e['commits']} commits since {e['verified_at']})"
            print(line)
            for f in e.get("changed_files", [])[:8]:
                print(f"    {f}")
            if len(e.get("changed_files", [])) > 8:
                print(f"    ... +{len(e['changed_files']) - 8} more")
        print("\n## Paths not covered by any knowledge file")
        for d, n in uncovered.most_common(15):
            print(f"- {d}: {n} files")
        if not uncovered:
            print("- none")
    stale = any(e["status"] not in ("fresh", "no-covers") for e in report)
    sys.exit(1 if stale or uncovered else 0)


if __name__ == "__main__":
    main()

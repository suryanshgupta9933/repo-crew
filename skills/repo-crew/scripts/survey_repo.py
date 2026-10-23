#!/usr/bin/env python3
"""Deterministic repo survey for repo-crew.

Usage: survey_repo.py [repo_path] [--days N] [--json] [--max-commits N]

Reports languages, manifests, CI/ship signals, existing agent config,
"units" (container-aware directories) with size and churn, co-change pairs,
entry-point-like files and the largest files. Uses only the standard library;
git history sections are skipped gracefully when the path is not a git repo.
"""
import argparse
import collections
import itertools
import json
import os
import re
import subprocess
import sys

SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", "out", "target", "vendor", ".venv",
    "venv", "__pycache__", ".next", ".nuxt", ".cache", "coverage", ".idea",
    ".vscode", ".mypy_cache", ".pytest_cache", ".tox", "site-packages",
}
SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "uv.lock",
    "Cargo.lock", "go.sum", "Gemfile.lock", "composer.lock", "bun.lockb",
}
CONTAINERS = {
    "src", "packages", "apps", "services", "libs", "lib", "crates", "modules",
    "extensions", "internal", "cmd", "pkg", "plugins", "projects", "components",
}
LANGS = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".cjs": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".go": "Go",
    ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".swift": "Swift",
    ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".c": "C", ".h": "C/C++ header",
    ".cpp": "C++", ".cc": "C++", ".scala": "Scala", ".sh": "Shell", ".sql": "SQL",
    ".html": "HTML", ".css": "CSS", ".scss": "CSS", ".vue": "Vue", ".svelte": "Svelte",
    ".dart": "Dart", ".lua": "Lua", ".ex": "Elixir", ".exs": "Elixir", ".tf": "Terraform",
    ".md": "Markdown", ".yml": "YAML", ".yaml": "YAML", ".json": "JSON", ".toml": "TOML",
}
CODE_LANGS = {v for v in LANGS.values()} - {"Markdown", "YAML", "JSON", "TOML"}
MANIFEST_NAMES = {
    "package.json", "pyproject.toml", "setup.py", "requirements.txt", "Pipfile",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "build.gradle.kts",
    "Gemfile", "composer.json", "mix.exs", "pubspec.yaml", "Package.swift",
    "manifest.json", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "tsconfig.json", "vite.config.ts", "vite.config.js", "webpack.config.js",
    "next.config.js", "terraform.tf", "serverless.yml",
}
AGENT_CONFIG_DIRS = (
    ".claude/agents/", ".claude/skills/", ".claude/rules/", "docs/crew/",
)
CI_FILES = {
    ".gitlab-ci.yml", "Makefile", "makefile", "justfile", "Jenkinsfile",
    "azure-pipelines.yml", "bitbucket-pipelines.yml", ".pre-commit-config.yaml",
    "tox.ini", "noxfile.py", "Taskfile.yml", ".travis.yml",
}
ENTRY_NAMES = {    "main.py", "__main__.py", "app.py", "server.py", "wsgi.py", "asgi.py", "cli.py",
    "index.js", "index.ts", "index.tsx", "main.ts", "main.js", "main.tsx", "app.ts",
    "app.tsx", "server.ts", "server.js", "background.js", "background.ts",
    "service-worker.js", "service_worker.js", "content.js", "content.ts", "popup.js",
    "sidepanel.js", "sidepanel.tsx", "main.go", "main.rs", "lib.rs", "Program.cs",
    "manage.py", "manifest.json",
}


def run_git(root, *args):
    try:
        out = subprocess.run(
            ["git", "-C", root, *args], capture_output=True, text=True, timeout=60
        )
        return out.stdout if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def list_files(root):
    out = run_git(root, "ls-files")
    if out is not None and out.strip():
        files = [f for f in out.splitlines() if f]
        files = [f for f in files if not set(f.split("/")[:-1]) & SKIP_DIRS]
        return files, True
    files = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            files.append(os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, "/"))
    return files, False


def find_agent_config(root):
    """Find agent and crew config in the working tree.

    These paths are commonly gitignored (`.claude/` usually is), so `git ls-files`
    alone would report no existing crew for a repo that already has one.
    """
    found = set()
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        rel_dir = os.path.relpath(dp, root).replace(os.sep, "/")
        rel_dir = "" if rel_dir == "." else rel_dir
        for fn in fns:
            rel = f"{rel_dir}/{fn}" if rel_dir else fn
            if rel in ("CLAUDE.md", "AGENTS.md") or rel.endswith("/CLAUDE.md"):
                found.add(rel)
            elif rel.startswith(AGENT_CONFIG_DIRS):
                found.add(rel)
    return found


def count_loc(path):
    try:
        if os.path.getsize(path) > 1_500_000:
            return 0
        with open(path, "rb") as fh:
            data = fh.read()
        if b"\0" in data[:4096]:
            return 0
        return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
    except OSError:
        return 0


def build_children(files):
    children = collections.defaultdict(set)
    for f in files:
        parts = f.split("/")
        for i in range(len(parts) - 1):
            children[tuple(parts[:i])].add(parts[i])
    return children


def unit_of(path, children):
    parts = path.split("/")
    if len(parts) == 1:
        return "(root)"
    i = 1
    while i < len(parts) - 1:
        prefix = tuple(parts[:i])
        name = parts[i - 1]
        only_child = len(children.get(prefix, ())) == 1
        if name in CONTAINERS or only_child:
            i += 1
        else:
            break
    return "/".join(parts[:i])


def package_scripts(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8") as fh:
            data = json.load(fh)
        return sorted((data.get("scripts") or {}).keys())
    except (OSError, ValueError):
        return []


def make_targets(root, rel):
    targets = []
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                m = re.match(r"^([A-Za-z0-9_.-]+)\s*:(?!=)", line)
                if m and not m.group(1).startswith("."):
                    targets.append(m.group(1))
    except OSError:
        pass
    return targets[:25]


def churn(root, units_of, days, max_commits):
    out = run_git(
        root, "log", f"--since={days}.days", "--no-merges", f"-n{max_commits}",
        "--name-only", "--pretty=format:@@%H",
    )
    if out is None:
        return None, None, 0
    unit_commits = collections.Counter()
    pairs = collections.Counter()
    n = 0
    for block in out.split("@@")[1:]:
        lines = [l for l in block.splitlines()[1:] if l.strip()]
        us = {units_of[l] for l in lines if l in units_of}
        if not us:
            continue
        n += 1
        for u in us:
            unit_commits[u] += 1
        if len(us) <= 6:  # ignore sweeping commits that touch everything
            for a, b in itertools.combinations(sorted(us), 2):
                pairs[(a, b)] += 1
    return unit_commits, pairs, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--days", type=int, default=180)
    ap.add_argument("--max-commits", type=int, default=1500)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(args.path)
    if not os.path.isdir(root):
        sys.exit(f"not a directory: {root}")

    files, is_git = list_files(root)
    files = [f for f in files if os.path.basename(f) not in SKIP_FILES]
    children = build_children(files)
    units_of = {f: unit_of(f, children) for f in files}

    lang_loc = collections.Counter()
    unit_stats = collections.defaultdict(lambda: {"files": 0, "loc": 0, "langs": collections.Counter()})
    file_loc = []
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        lang = LANGS.get(ext)
        loc = count_loc(os.path.join(root, f)) if lang else 0
        if lang:
            lang_loc[lang] += loc
        u = unit_stats[units_of[f]]
        u["files"] += 1
        u["loc"] += loc
        if lang in CODE_LANGS:
            u["langs"][lang] += loc
        if lang in CODE_LANGS and loc:
            file_loc.append((loc, f))

    manifests = sorted(f for f in files if os.path.basename(f) in MANIFEST_NAMES)
    ci = sorted(
        f for f in files
        if f.startswith(".github/workflows/") or f.startswith(".circleci/")
        or os.path.basename(f) in CI_FILES
    )
    scripts = {}
    for m in manifests:
        if os.path.basename(m) == "package.json":
            s = package_scripts(root, m)
            if s:
                scripts[m] = s
    targets = {f: make_targets(root, f) for f in ci if os.path.basename(f) in ("Makefile", "makefile", "justfile")}

    agent_cfg = sorted(
        set(f for f in files
            if f in ("CLAUDE.md", "AGENTS.md") or f.endswith("/CLAUDE.md")
            or f.startswith(AGENT_CONFIG_DIRS))
        | find_agent_config(root)
    )
    docs = sorted(
        f for f in files
        if re.search(r"(^|/)(adr|adrs|decisions)(/|$)", f, re.I)
        or os.path.basename(f).lower() in ("readme.md", "contributing.md", "architecture.md")
    )
    tests = sorted({
        units_of[f] for f in files
        if re.search(r"(^|/)(tests?|__tests__|spec|e2e)(/|$)|\.(test|spec)\.[a-z]+$|_test\.(py|go)$", f)
    })
    entries = sorted(f for f in files if os.path.basename(f) in ENTRY_NAMES)[:40]

    unit_commits = pairs = None
    n_commits = 0
    if is_git:
        unit_commits, pairs, n_commits = churn(root, units_of, args.days, args.max_commits)

    units = []
    for name, s in unit_stats.items():
        units.append({
            "unit": name, "files": s["files"], "loc": s["loc"],
            "main_langs": [l for l, _ in s["langs"].most_common(2)],
            "commits": (unit_commits or {}).get(name),
        })
    units.sort(key=lambda u: (-(u["commits"] or 0), -u["loc"]))

    pair_list = []
    if pairs:
        for (a, b), c in pairs.most_common(12):
            base = min(unit_commits[a], unit_commits[b]) or 1
            pair_list.append({"a": a, "b": b, "together": c, "share_of_smaller": round(c / base, 2)})

    result = {
        "root": root, "git": is_git, "files": len(files),
        "commits_analyzed": n_commits, "days": args.days,
        "languages": lang_loc.most_common(10),
        "manifests": manifests, "ci_files": ci, "package_scripts": scripts,
        "make_targets": targets, "agent_config": agent_cfg, "docs": docs,
        "units_with_tests": tests, "entry_points": entries, "units": units,
        "co_change": pair_list,
        "largest_files": sorted(file_loc, reverse=True)[:10],
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return

    p = print
    p(f"# Repo survey: {root}")
    p(f"\nFiles: {len(files)} | git: {'yes' if is_git else 'no (history sections skipped)'}"
      f" | commits analyzed (last {args.days}d): {n_commits}")
    p("\n## Languages (LOC)")
    for l, c in lang_loc.most_common(10):
        p(f"- {l}: {c}")
    p("\n## Manifests")
    p("\n".join(f"- {m}" for m in manifests) or "- none found")
    p("\n## CI / ship signals")
    p("\n".join(f"- {c}" for c in ci) or "- none found")
    for m, s in scripts.items():
        p(f"- {m} scripts: {', '.join(s)}")
    for f, t in targets.items():
        if t:
            p(f"- {f} targets: {', '.join(t)}")
    p("\n## Existing agent config / docs")
    p("\n".join(f"- {c}" for c in agent_cfg + docs) or "- none found")
    p("\n## Units (sorted by recent churn, then LOC)")
    p("| unit | files | LOC | main langs | commits |")
    p("|---|---|---|---|---|")
    for u in units[:40]:
        p(f"| {u['unit']} | {u['files']} | {u['loc']} | {', '.join(u['main_langs']) or '-'} | "
          f"{u['commits'] if u['commits'] is not None else '-'} |")
    if len(units) > 40:
        p(f"\n(+{len(units) - 40} smaller units omitted; use --json for all)")
    p("\n## Units containing tests")
    p("\n".join(f"- {t}" for t in tests) or "- none detected")
    p("\n## Co-change pairs (same commits)")
    if pair_list:
        for x in pair_list:
            p(f"- {x['a']} + {x['b']}: {x['together']} commits ({int(x['share_of_smaller']*100)}% of the smaller unit's)")
    else:
        p("- not available")
    p("\n## Entry-point-like files")
    p("\n".join(f"- {e}" for e in entries) or "- none detected")
    p("\n## Largest source files")
    for loc, f in result["largest_files"]:
        p(f"- {f}: {loc}")


if __name__ == "__main__":
    main()

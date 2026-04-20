#!/usr/bin/env python3
"""
BMAD Full Cycle Installer

Install BMAD skills into any AI IDE project.

Supported IDEs:
    trae        .trae/skills/{name}/SKILL.md        (native directory structure)
    cursor      .cursor/rules/{name}.mdc            (frontmatter: description/globs/alwaysApply)
    windsurf    .windsurf/rules/{name}.md            (workspace rules)
    claude-code CLAUDE.md + .claude/commands/{name}.md (project instructions + slash commands)

Usage:
    python install.py /path/to/project                    # auto-detect IDE or default trae
    python install.py /path/to/project --ide cursor       # specify IDE
    python install.py /path/to/project --ide claude-code  # Claude Code
    python install.py /path/to/project --list             # list available skills
    python install.py /path/to/project --select           # interactive group selection
"""

import argparse
import json
import os
import re
import shutil
import sys
import textwrap

# ── IDE Configs ───────────────────────────────────────────────────────────

IDE_CONFIGS = {
    "trae": {
        "name": "Trae",
        "rules_dir": ".trae/skills",
        "format": "trae",
        "chat_shortcut": "Cmd+L (macOS) / Ctrl+L (Windows)",
        "description": "Trae IDE by ByteDance — native skill directories",
    },
    "cursor": {
        "name": "Cursor",
        "rules_dir": ".cursor/rules",
        "format": "mdc",
        "chat_shortcut": "Cmd+L (macOS) / Ctrl+L (Windows)",
        "description": "Cursor AI IDE — .mdc rule files with frontmatter",
    },
    "windsurf": {
        "name": "Windsurf",
        "rules_dir": ".windsurf/rules",
        "format": "windsurf",
        "chat_shortcut": "Cmd+L (macOS) / Ctrl+L (Windows)",
        "description": "Windsurf (Cascade) — workspace rule files",
    },
    "claude-code": {
        "name": "Claude Code",
        "rules_dir": ".claude/commands",
        "format": "claude",
        "chat_shortcut": "claude (CLI)",
        "description": "Anthropic Claude Code — CLAUDE.md + slash commands",
    },
}

# ── Skill Groups ──────────────────────────────────────────────────────────

SKILL_GROUPS = {
    "core": {
        "name": "Core (required)",
        "name_zh": "核心 (必装)",
        "description": "BMAD infrastructure and project initialization",
        "skills": [
            "bmad-init",
            "bmad-help",
            "bmad-router",
            "bmad-index-docs",
        ],
    },
    "planning": {
        "name": "Planning",
        "name_zh": "规划阶段",
        "description": "Requirements, architecture, epic/story breakdown",
        "skills": [
            "bmad-create-prd",
            "bmad-edit-prd",
            "bmad-validate-prd",
            "bmad-create-architecture",
            "bmad-create-epics-and-stories",
            "bmad-check-implementation-readiness",
            "bmad-sprint-planning",
            "bmad-sprint-status",
        ],
    },
    "development": {
        "name": "Development",
        "name_zh": "开发阶段",
        "description": "Story creation, coding, code review, code standards",
        "skills": [
            "bmad-create-story",
            "bmad-dev-story",
            "bmad-code-review",
            "bmad-correct-course",
            "bmad-java-code-standards",
        ],
    },
    "automation": {
        "name": "Automation",
        "name_zh": "自动化编排",
        "description": "Fully automated execution loops",
        "skills": [
            "bmad-full-cycle",
            "bmad-autopilot",
            "bmad-migration-autopilot",
            "bmad-quick-dev",
        ],
    },
    "agents": {
        "name": "AI Agents",
        "name_zh": "AI 角色代理",
        "description": "Role-based AI agents (PM, Architect, Dev, QA, etc.)",
        "skills": [
            "bmad-agent-analyst",
            "bmad-agent-architect",
            "bmad-agent-dev",
            "bmad-agent-pm",
            "bmad-agent-qa",
            "bmad-agent-sm",
            "bmad-agent-tech-writer",
            "bmad-agent-ux-designer",
            "bmad-agent-quick-flow-solo-dev",
        ],
    },
    "research": {
        "name": "Research",
        "name_zh": "研究与分析",
        "description": "Domain, market, and technical research",
        "skills": [
            "bmad-domain-research",
            "bmad-market-research",
            "bmad-technical-research",
            "bmad-product-brief",
            "bmad-advanced-elicitation",
        ],
    },
    "review": {
        "name": "Review & QA",
        "name_zh": "审查与质量",
        "description": "Document review, adversarial testing, edge cases",
        "skills": [
            "bmad-document-reviewer",
            "bmad-editorial-review-prose",
            "bmad-editorial-review-structure",
            "bmad-review-adversarial-general",
            "bmad-review-edge-case-hunter",
            "bmad-qa-generate-e2e-tests",
            "bmad-retrospective",
        ],
    },
    "docs": {
        "name": "Documentation",
        "name_zh": "文档工具",
        "description": "Project docs, context generation, knowledge distillation, enterprise doc standards",
        "skills": [
            "bmad-documentation",
            "bmad-document-project",
            "bmad-generate-project-context",
            "bmad-shard-doc",
            "bmad-distillator",
        ],
    },
    "creative": {
        "name": "Creative",
        "name_zh": "创意与设计",
        "description": "Brainstorming, UX design, multi-agent discussion",
        "skills": [
            "bmad-brainstorming",
            "bmad-create-ux-design",
            "bmad-party-mode",
        ],
    },
}

# ── Terminal Colors ───────────────────────────────────────────────────────

def _supports_color():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

if _supports_color():
    GREEN = "\033[32m"; YELLOW = "\033[33m"; CYAN = "\033[36m"
    RED = "\033[31m"; BOLD = "\033[1m"; DIM = "\033[2m"; RESET = "\033[0m"
else:
    GREEN = YELLOW = CYAN = RED = BOLD = DIM = RESET = ""

def print_header(text):
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}\n")

def print_success(text): print(f"  {GREEN}✓{RESET} {text}")
def print_warn(text):    print(f"  {YELLOW}⚠{RESET} {text}")
def print_error(text):   print(f"  {RED}✗{RESET} {text}")
def print_info(text):    print(f"  {DIM}→{RESET} {text}")


# ── Skill Parsing Helpers ─────────────────────────────────────────────────

def parse_skill_md(skill_md_path):
    """Parse a SKILL.md file, extract frontmatter and body."""
    with open(skill_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter = {}
    body = content

    # YAML frontmatter between ---
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        body = content[fm_match.end():]
        for line in fm_text.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                frontmatter[key.strip()] = val.strip().strip('"').strip("'")

    # Fallback: extract description from first heading or description field
    if "description" not in frontmatter:
        for line in body.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                frontmatter["description"] = line[2:].strip()
                break

    return frontmatter, body


def collect_supporting_files(skill_dir):
    """List all non-SKILL.md files in a skill directory (relative paths)."""
    files = []
    for root, dirs, filenames in os.walk(skill_dir):
        for fname in filenames:
            if fname == "SKILL.md":
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, skill_dir)
            files.append(rel_path)
    return files


def rewrite_body_paths(body, skill_name, support_files, target_base="_bmad/skills"):
    """Rewrite relative path references in skill body to target IDE path structure.

    Handles common patterns:
      - ./filename.ext          → _bmad/skills/{name}/filename.ext
      - ./subdir/filename.ext   → _bmad/skills/{name}/subdir/filename.ext
      - (filename.ext)          → (_bmad/skills/{name}/filename.ext)  (markdown links)
      - "filename.ext"          → "_bmad/skills/{name}/filename.ext"  (quoted refs)
    Only rewrites references to files that actually exist in the skill directory.
    """
    if not support_files:
        return body

    target_prefix = f"{target_base}/{skill_name}"
    support_set = set(support_files)

    # Pattern 1: Explicit relative paths  ./path/to/file
    body = re.sub(
        r'\./([^\s\)\"\'>\]]+)',
        lambda m: f"{target_prefix}/{m.group(1)}" if m.group(1) in support_set else m.group(0),
        body
    )

    # Pattern 2: Markdown link targets  [text](filename.ext) or [text](subdir/file)
    def rewrite_md_link(m):
        path = m.group(1)
        if path in support_set:
            return f"]({target_prefix}/{path})"
        return m.group(0)
    body = re.sub(r'\]\(([^):/\s][^):]*?\.(md|yaml|yml|json|txt|sh|py|j2|tmpl))\)', rewrite_md_link, body)

    return body


def build_supporting_files_section(skill_name, support_files, target_base="_bmad/skills"):
    """Build an explicit markdown section for supporting file references.

    Uses a clear instruction block instead of HTML comments, so AI agents
    will actually read and use the file paths.
    """
    if not support_files:
        return ""

    target_prefix = f"{target_base}/{skill_name}"
    lines = [
        f"**Supporting files** for this skill are located in `{target_prefix}/`:",
        "",
    ]
    for f in sorted(support_files):
        lines.append(f"- `{target_prefix}/{f}`")
    lines.append("")
    return "\n".join(lines)


# ── IDE-specific Installers ───────────────────────────────────────────────

def install_trae(skills_dir, target_project, skill_names):
    """Trae: copy skill directories as-is to .trae/skills/"""
    target_dir = os.path.join(target_project, ".trae", "skills")
    os.makedirs(target_dir, exist_ok=True)

    stats = {"installed": 0, "updated": 0}
    for name in skill_names:
        src = os.path.join(skills_dir, name)
        dst = os.path.join(target_dir, name)
        if os.path.exists(dst):
            shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print_success(f"{name} {DIM}(updated){RESET}")
            stats["updated"] += 1
        else:
            shutil.copytree(src, dst)
            print_success(name)
            stats["installed"] += 1

    return stats


def install_cursor(skills_dir, target_project, skill_names):
    """Cursor: convert SKILL.md to .mdc files in .cursor/rules/"""
    rules_dir = os.path.join(target_project, ".cursor", "rules")
    support_dir = os.path.join(target_project, "_bmad", "skills")
    os.makedirs(rules_dir, exist_ok=True)

    stats = {"installed": 0, "updated": 0}
    for name in skill_names:
        src_dir = os.path.join(skills_dir, name)
        skill_md_path = os.path.join(src_dir, "SKILL.md")
        if not os.path.isfile(skill_md_path):
            continue

        fm, body = parse_skill_md(skill_md_path)
        desc = fm.get("description", name)

        # Build .mdc content
        mdc_lines = ["---"]
        mdc_lines.append(f'description: "{desc}"')
        mdc_lines.append("alwaysApply: false")
        mdc_lines.append("---")
        mdc_lines.append("")

        # Add explicit supporting file references (replaces HTML comment)
        support_files = collect_supporting_files(src_dir)
        if support_files:
            mdc_lines.append(build_supporting_files_section(name, support_files))

        # Rewrite relative paths in body to point to _bmad/skills/{name}/
        rewritten_body = rewrite_body_paths(body, name, support_files)
        mdc_lines.append(rewritten_body)

        # Write .mdc file
        mdc_path = os.path.join(rules_dir, f"{name}.mdc")
        is_update = os.path.exists(mdc_path)
        with open(mdc_path, "w", encoding="utf-8") as f:
            f.write("\n".join(mdc_lines))

        # Copy supporting files
        if support_files:
            dst_support = os.path.join(support_dir, name)
            if os.path.exists(dst_support):
                shutil.rmtree(dst_support)
            os.makedirs(dst_support, exist_ok=True)
            for rel in support_files:
                src_file = os.path.join(src_dir, rel)
                dst_file = os.path.join(dst_support, rel)
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                shutil.copy2(src_file, dst_file)

        if is_update:
            print_success(f"{name}.mdc {DIM}(updated){RESET}")
            stats["updated"] += 1
        else:
            print_success(f"{name}.mdc")
            stats["installed"] += 1

    return stats


def install_windsurf(skills_dir, target_project, skill_names):
    """Windsurf: convert SKILL.md to .md rules in .windsurf/rules/"""
    rules_dir = os.path.join(target_project, ".windsurf", "rules")
    support_dir = os.path.join(target_project, "_bmad", "skills")
    os.makedirs(rules_dir, exist_ok=True)

    stats = {"installed": 0, "updated": 0}
    for name in skill_names:
        src_dir = os.path.join(skills_dir, name)
        skill_md_path = os.path.join(src_dir, "SKILL.md")
        if not os.path.isfile(skill_md_path):
            continue

        fm, body = parse_skill_md(skill_md_path)
        desc = fm.get("description", name)

        # Build rule content with Windsurf-compatible header
        rule_lines = []
        rule_lines.append(f"# {name}")
        rule_lines.append("")
        rule_lines.append(f"> {desc}")
        rule_lines.append("")

        support_files = collect_supporting_files(src_dir)
        if support_files:
            rule_lines.append(build_supporting_files_section(name, support_files))

        # Rewrite relative paths in body
        rewritten_body = rewrite_body_paths(body, name, support_files)
        rule_lines.append(rewritten_body)

        # Write rule file
        rule_path = os.path.join(rules_dir, f"{name}.md")
        is_update = os.path.exists(rule_path)
        with open(rule_path, "w", encoding="utf-8") as f:
            f.write("\n".join(rule_lines))

        # Copy supporting files
        if support_files:
            dst_support = os.path.join(support_dir, name)
            if os.path.exists(dst_support):
                shutil.rmtree(dst_support)
            os.makedirs(dst_support, exist_ok=True)
            for rel in support_files:
                src_file = os.path.join(src_dir, rel)
                dst_file = os.path.join(dst_support, rel)
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                shutil.copy2(src_file, dst_file)

        if is_update:
            print_success(f"{name}.md {DIM}(updated){RESET}")
            stats["updated"] += 1
        else:
            print_success(f"{name}.md")
            stats["installed"] += 1

    return stats


def install_claude_code(skills_dir, target_project, skill_names):
    """Claude Code: create CLAUDE.md + .claude/commands/{name}.md"""
    commands_dir = os.path.join(target_project, ".claude", "commands")
    support_dir = os.path.join(target_project, "_bmad", "skills")
    os.makedirs(commands_dir, exist_ok=True)

    # Collect skill descriptions for CLAUDE.md
    skill_entries = []
    stats = {"installed": 0, "updated": 0}

    for name in skill_names:
        src_dir = os.path.join(skills_dir, name)
        skill_md_path = os.path.join(src_dir, "SKILL.md")
        if not os.path.isfile(skill_md_path):
            continue

        fm, body = parse_skill_md(skill_md_path)
        desc = fm.get("description", name)
        trigger = fm.get("argument-hint", "")
        skill_entries.append((name, desc, trigger))

        # Create slash command file
        # Add supporting file references and rewrite paths
        support_files = collect_supporting_files(src_dir)
        cmd_content = ""
        if support_files:
            cmd_content = build_supporting_files_section(name, support_files) + "\n"
        cmd_content += rewrite_body_paths(body, name, support_files)

        cmd_path = os.path.join(commands_dir, f"{name}.md")
        is_update = os.path.exists(cmd_path)
        with open(cmd_path, "w", encoding="utf-8") as f:
            f.write(cmd_content)

        # Copy supporting files
        if support_files:
            dst_support = os.path.join(support_dir, name)
            if os.path.exists(dst_support):
                shutil.rmtree(dst_support)
            os.makedirs(dst_support, exist_ok=True)
            for rel in support_files:
                src_file = os.path.join(src_dir, rel)
                dst_file = os.path.join(dst_support, rel)
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                shutil.copy2(src_file, dst_file)

        if is_update:
            print_success(f"/{name} {DIM}(updated){RESET}")
            stats["updated"] += 1
        else:
            print_success(f"/{name}")
            stats["installed"] += 1

    # Generate/update CLAUDE.md
    claude_md_path = os.path.join(target_project, "CLAUDE.md")
    bmad_section = _build_claude_md_section(skill_entries)

    if os.path.isfile(claude_md_path):
        with open(claude_md_path, "r", encoding="utf-8") as f:
            existing = f.read()

        # Replace existing BMAD section or append
        marker_start = "<!-- BMAD-START -->"
        marker_end = "<!-- BMAD-END -->"
        if marker_start in existing:
            pattern = re.compile(
                re.escape(marker_start) + r".*?" + re.escape(marker_end),
                re.DOTALL
            )
            new_content = pattern.sub(bmad_section, existing)
        else:
            new_content = existing.rstrip() + "\n\n" + bmad_section + "\n"

        with open(claude_md_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print_success(f"CLAUDE.md {DIM}(BMAD section updated){RESET}")
    else:
        with open(claude_md_path, "w", encoding="utf-8") as f:
            f.write(bmad_section + "\n")
        print_success("CLAUDE.md")

    return stats


def _build_claude_md_section(skill_entries):
    """Build the BMAD section for CLAUDE.md."""
    lines = ["<!-- BMAD-START -->"]
    lines.append("## BMAD Skills")
    lines.append("")
    lines.append("This project uses BMAD (Business Model-Aligned Development) skills.")
    lines.append("Available as slash commands:")
    lines.append("")

    for name, desc, trigger in skill_entries:
        lines.append(f"- `/{name}` — {desc}")

    lines.append("")
    lines.append("Key workflows:")
    lines.append("- Full cycle (requirements → code → docs): `/{} [feature description]`".format("bmad-full-cycle"))
    lines.append("- Auto dev loop: `/{}`".format("bmad-autopilot"))
    lines.append("- Migration autopilot: `/{}`".format("bmad-migration-autopilot"))
    lines.append("")
    lines.append("Supporting files are in `_bmad/skills/`.")
    lines.append("Project config: `_bmad/bmm/config.yaml`.")
    lines.append("<!-- BMAD-END -->")
    return "\n".join(lines)


# ── Auto-detect IDE ───────────────────────────────────────────────────────

def detect_ide(project_path):
    """Try to detect which IDE is used based on existing directories."""
    checks = [
        (".trae", "trae"),
        (".cursor", "cursor"),
        (".windsurf", "windsurf"),
        (".claude", "claude-code"),
    ]
    for dirname, ide in checks:
        if os.path.isdir(os.path.join(project_path, dirname)):
            return ide
    return None


# ── Common Logic ──────────────────────────────────────────────────────────

def get_repo_skills_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skills_dir = os.path.join(script_dir, "skills")
    if not os.path.isdir(skills_dir):
        print_error(f"skills/ directory not found: {skills_dir}")
        print_info("Make sure you're running from the bmad-full-cycle repository")
        sys.exit(1)
    return skills_dir


def discover_available_skills(skills_dir):
    skills = []
    for name in sorted(os.listdir(skills_dir)):
        skill_path = os.path.join(skills_dir, name)
        if os.path.isdir(skill_path) and name.startswith("bmad-"):
            skills.append(name)
    return skills


def list_skills(skills_dir):
    available = set(discover_available_skills(skills_dir))

    print_header("Available BMAD Skills")

    total = 0
    for group_id, group in SKILL_GROUPS.items():
        group_skills = [s for s in group["skills"] if s in available]
        if not group_skills:
            continue

        print(f"  {BOLD}{group['name']}{RESET} {DIM}— {group['description']}{RESET}")
        for skill_name in group_skills:
            skill_md = os.path.join(skills_dir, skill_name, "SKILL.md")
            desc = ""
            if os.path.isfile(skill_md):
                fm, _ = parse_skill_md(skill_md)
                desc = fm.get("description", "")
            desc_short = (desc[:60] + "...") if len(desc) > 63 else desc
            print(f"    {GREEN}•{RESET} {skill_name}  {DIM}{desc_short}{RESET}")
            total += 1
        print()

    grouped = set()
    for group in SKILL_GROUPS.values():
        grouped.update(group["skills"])
    ungrouped = [s for s in available if s not in grouped]
    if ungrouped:
        print(f"  {BOLD}Other{RESET}")
        for skill_name in ungrouped:
            print(f"    {GREEN}•{RESET} {skill_name}")
            total += 1
        print()

    print(f"  {BOLD}Total: {total} skills{RESET}\n")


def select_skills_interactive(skills_dir):
    available = set(discover_available_skills(skills_dir))

    print_header("Select Skill Groups to Install")
    print("  Enter group numbers (comma-separated), or press Enter for all:\n")

    group_list = []
    for i, (group_id, group) in enumerate(SKILL_GROUPS.items(), 1):
        count = len([s for s in group["skills"] if s in available])
        if count == 0:
            continue
        marker = f"{YELLOW}*{RESET}" if group_id in ("core", "planning", "development", "automation") else " "
        print(f"  {marker} [{i}] {group['name']}  {DIM}({count} skills) — {group['description']}{RESET}")
        group_list.append((group_id, group))

    print(f"\n  {DIM}* = required for full-cycle workflow{RESET}\n")

    try:
        answer = input("  Select (Enter=all): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)

    selected = set()
    if not answer:
        for s in available:
            selected.add(s)
    else:
        for idx_str in answer.split(","):
            try:
                idx = int(idx_str.strip()) - 1
                if 0 <= idx < len(group_list):
                    _, group = group_list[idx]
                    for s in group["skills"]:
                        if s in available:
                            selected.add(s)
            except ValueError:
                print_warn(f"Ignoring invalid input: {idx_str}")

    # Always include core
    for s in SKILL_GROUPS["core"]["skills"]:
        if s in available:
            selected.add(s)

    return sorted(selected)


def install_skills(skills_dir, target_project, ide, skill_names=None):
    available = discover_available_skills(skills_dir)
    if skill_names is None:
        skill_names = available
    else:
        skill_names = [s for s in skill_names if s in available]

    ide_config = IDE_CONFIGS[ide]

    print_header(f"Installing BMAD Skills → {ide_config['name']}")
    print_info(f"Target:  {target_project}")
    print_info(f"IDE:     {ide_config['name']} ({ide_config['description']})")
    print_info(f"Format:  {ide_config['format']}")
    print_info(f"Skills:  {len(skill_names)}")
    print()

    # Dispatch to IDE-specific installer
    installer = {
        "trae": install_trae,
        "cursor": install_cursor,
        "windsurf": install_windsurf,
        "claude-code": install_claude_code,
    }[ide]

    stats = installer(skills_dir, target_project, skill_names)

    print()
    print(f"  {BOLD}Done!{RESET}")
    print_info(f"Installed: {stats['installed']}")
    if stats.get("updated"):
        print_info(f"Updated:   {stats['updated']}")

    return stats["installed"] + stats.get("updated", 0)


def install_harness(target_project):
    """Install BMAD Harness infrastructure files into the target project.

    Copies harness files (state management, gatekeeper, config) so that
    bmad-full-cycle and autopilot skills can persist phase state across
    sessions and enforce gatekeeper validation on phase transitions.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_harness = os.path.join(script_dir, "harness")
    dst_harness = os.path.join(target_project, "harness")

    if not os.path.isdir(src_harness):
        print_warn("harness/ directory not found in repo, skipping harness install")
        return

    print_header("Installing BMAD Harness Infrastructure")

    # Files to copy (relative to harness/)
    harness_files = [
        "bmad_harness.py",
        "bmad-gatekeeper.sh",
        "bmad-harness-config.json",
    ]

    os.makedirs(dst_harness, exist_ok=True)
    os.makedirs(os.path.join(dst_harness, "memory"), exist_ok=True)

    for fname in harness_files:
        src = os.path.join(src_harness, fname)
        dst = os.path.join(dst_harness, fname)
        if os.path.isfile(src):
            is_update = os.path.isfile(dst)
            shutil.copy2(src, dst)
            label = f"{DIM}(updated){RESET}" if is_update else ""
            print_success(f"harness/{fname} {label}")

    # Ensure memory/bmad-state.json exists (don't overwrite if already has state)
    state_file = os.path.join(dst_harness, "memory", "bmad-state.json")
    if not os.path.isfile(state_file):
        src_state = os.path.join(src_harness, "memory", "bmad-state.json")
        if os.path.isfile(src_state):
            shutil.copy2(src_state, state_file)
            print_success("harness/memory/bmad-state.json")
        else:
            # Create a default empty state
            default_state = {
                "project": os.path.basename(os.path.normpath(target_project)),
                "currentPhase": None,
                "phases": {},
                "retryCounters": {},
            }
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(default_state, f, indent=2, ensure_ascii=False)
            print_success("harness/memory/bmad-state.json (default)")
    else:
        print_info("harness/memory/bmad-state.json already exists, preserving state")

    # Make scripts executable
    for script in ["bmad_harness.py", "bmad-gatekeeper.sh"]:
        path = os.path.join(dst_harness, script)
        if os.path.isfile(path):
            os.chmod(path, 0o755)

    print()
    print_info("Harness installed → phase state persists across sessions")
    print_info("Skills will auto-load harness/memory/bmad-state.json on startup")


def init_bmad(target_project, ide):
    bmad_dir = os.path.join(target_project, "_bmad", "bmm")
    config_file = os.path.join(bmad_dir, "config.yaml")

    if os.path.isfile(config_file):
        print_info("_bmad/bmm/config.yaml already exists, skipping init")
        return

    print_header("Initializing BMAD Project Config")

    os.makedirs(bmad_dir, exist_ok=True)
    project_name = os.path.basename(os.path.normpath(target_project))
    ide_name = IDE_CONFIGS[ide]["name"]

    config_content = textwrap.dedent(f"""\
        # BMAD Project Configuration
        # Auto-generated by install.py — edit as needed
        #
        # For full interactive setup, type in {ide_name} AI chat:
        #   bmad-init
        # or (in Chinese):
        #   初始化 bmad 项目

        project:
          name: {project_name}
          root: .

        paths:
          planning_artifacts: _bmad-output/planning-artifacts
          implementation_artifacts: _bmad-output/implementation-artifacts
    """)

    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config_content)

    os.makedirs(os.path.join(target_project, "_bmad-output", "planning-artifacts"), exist_ok=True)
    os.makedirs(os.path.join(target_project, "_bmad-output", "implementation-artifacts"), exist_ok=True)

    print_success("_bmad/bmm/config.yaml")
    print_success("_bmad-output/ directories")
    print_info(f"For full setup, type in {ide_name}: bmad-init")


def print_next_steps(target_project, ide):
    ide_config = IDE_CONFIGS[ide]
    name = ide_config["name"]

    print_header("Next Steps")

    # Step 1: open project
    if ide == "claude-code":
        print(f"  {BOLD}1. Enter your project directory{RESET}")
        print(f"     cd {target_project}\n")
    else:
        print(f"  {BOLD}1. Open project in {name}{RESET}")
        print(f"     File → Open Folder → {target_project}\n")

    # Step 2: open AI chat
    print(f"  {BOLD}2. Open AI chat{RESET}")
    if ide == "claude-code":
        print(f"     Run: claude\n")
    else:
        print(f"     {ide_config['chat_shortcut']}\n")

    # Step 3: start using
    print(f"  {BOLD}3. Start using BMAD{RESET}")
    if ide == "claude-code":
        print(f"     {CYAN}/bmad-full-cycle I want to build: user management module{RESET}")
        print(f"     {CYAN}/bmad-autopilot{RESET}       ← auto-execute existing sprint")
        print(f"     {CYAN}/bmad-help{RESET}             ← list all commands")
    else:
        print(f"     Type in chat:\n")
        print(f"     {CYAN}I want to build: user management module{RESET}  ← full cycle")
        print(f"     {CYAN}start autopilot{RESET}                          ← auto-execute sprint")
        print(f"     {CYAN}bmad-help{RESET}                                ← list all commands")
    print()

    # IDE-specific notes
    if ide == "cursor":
        print(f"  {DIM}Note: Cursor rules are loaded from .cursor/rules/*.mdc{RESET}")
        print(f"  {DIM}Type @ in chat to reference a specific rule (e.g. @bmad-full-cycle){RESET}\n")
    elif ide == "windsurf":
        print(f"  {DIM}Note: Windsurf rules are loaded from .windsurf/rules/*.md{RESET}")
        print(f"  {DIM}Cascade will automatically apply matching rules{RESET}\n")
    elif ide == "claude-code":
        print(f"  {DIM}Note: Skills are available as /{'{'}command{'}'} slash commands{RESET}")
        print(f"  {DIM}CLAUDE.md provides project context automatically{RESET}\n")


# ── Uninstall ─────────────────────────────────────────────────────────────

def get_installed_skills(target_project, ide):
    """Discover which BMAD skills are currently installed in the target project."""
    installed = []
    ide_config = IDE_CONFIGS[ide]

    if ide == "trae":
        skills_dir = os.path.join(target_project, ".trae", "skills")
        if os.path.isdir(skills_dir):
            for name in sorted(os.listdir(skills_dir)):
                if name.startswith("bmad-") and os.path.isdir(os.path.join(skills_dir, name)):
                    installed.append(name)
    elif ide == "cursor":
        rules_dir = os.path.join(target_project, ".cursor", "rules")
        if os.path.isdir(rules_dir):
            for fname in sorted(os.listdir(rules_dir)):
                if fname.startswith("bmad-") and fname.endswith(".mdc"):
                    installed.append(fname[:-4])  # strip .mdc
    elif ide == "windsurf":
        rules_dir = os.path.join(target_project, ".windsurf", "rules")
        if os.path.isdir(rules_dir):
            for fname in sorted(os.listdir(rules_dir)):
                if fname.startswith("bmad-") and fname.endswith(".md"):
                    installed.append(fname[:-3])  # strip .md
    elif ide == "claude-code":
        commands_dir = os.path.join(target_project, ".claude", "commands")
        if os.path.isdir(commands_dir):
            for fname in sorted(os.listdir(commands_dir)):
                if fname.startswith("bmad-") and fname.endswith(".md"):
                    installed.append(fname[:-3])

    return installed


def uninstall_skills(target_project, ide, skill_names=None):
    """Remove installed BMAD skills from the target project.

    Args:
        target_project: Project root path
        ide: IDE identifier
        skill_names: List of skill names to remove, or None for all BMAD skills
    """
    installed = get_installed_skills(target_project, ide)
    if skill_names:
        to_remove = [s for s in skill_names if s in installed]
    else:
        to_remove = installed

    if not to_remove:
        print_warn("No BMAD skills found to uninstall")
        return 0

    print_header(f"Uninstalling BMAD Skills from {IDE_CONFIGS[ide]['name']}")
    print_info(f"Target: {target_project}")
    print_info(f"Skills to remove: {len(to_remove)}")
    print()

    removed = 0

    for name in to_remove:
        if ide == "trae":
            skill_dir = os.path.join(target_project, ".trae", "skills", name)
            if os.path.isdir(skill_dir):
                shutil.rmtree(skill_dir)
                print_success(f"Removed {name}/")
                removed += 1
        elif ide == "cursor":
            mdc_path = os.path.join(target_project, ".cursor", "rules", f"{name}.mdc")
            if os.path.isfile(mdc_path):
                os.remove(mdc_path)
                print_success(f"Removed {name}.mdc")
                removed += 1
        elif ide == "windsurf":
            rule_path = os.path.join(target_project, ".windsurf", "rules", f"{name}.md")
            if os.path.isfile(rule_path):
                os.remove(rule_path)
                print_success(f"Removed {name}.md")
                removed += 1
        elif ide == "claude-code":
            cmd_path = os.path.join(target_project, ".claude", "commands", f"{name}.md")
            if os.path.isfile(cmd_path):
                os.remove(cmd_path)
                print_success(f"Removed /{name}")
                removed += 1

        # Remove supporting files for non-trae IDEs
        if ide != "trae":
            support_dir = os.path.join(target_project, "_bmad", "skills", name)
            if os.path.isdir(support_dir):
                shutil.rmtree(support_dir)
                print_info(f"  Removed _bmad/skills/{name}/")

    # Claude Code: clean BMAD section from CLAUDE.md
    if ide == "claude-code" and not skill_names:
        claude_md_path = os.path.join(target_project, "CLAUDE.md")
        if os.path.isfile(claude_md_path):
            with open(claude_md_path, "r", encoding="utf-8") as f:
                content = f.read()
            marker_start = "<!-- BMAD-START -->"
            marker_end = "<!-- BMAD-END -->"
            if marker_start in content:
                pattern = re.compile(
                    r'\n?' + re.escape(marker_start) + r'.*?' + re.escape(marker_end) + r'\n?',
                    re.DOTALL
                )
                new_content = pattern.sub('', content).strip()
                if new_content:
                    with open(claude_md_path, "w", encoding="utf-8") as f:
                        f.write(new_content + "\n")
                    print_success("Cleaned BMAD section from CLAUDE.md")
                else:
                    os.remove(claude_md_path)
                    print_success("Removed CLAUDE.md (was BMAD-only)")

    # Clean up empty _bmad/skills/ directory
    bmad_skills_dir = os.path.join(target_project, "_bmad", "skills")
    if os.path.isdir(bmad_skills_dir) and not os.listdir(bmad_skills_dir):
        os.rmdir(bmad_skills_dir)
        bmad_dir = os.path.join(target_project, "_bmad")
        if os.path.isdir(bmad_dir) and not os.listdir(bmad_dir):
            os.rmdir(bmad_dir)

    print()
    print(f"  {BOLD}Done!{RESET} Removed {removed} skill(s)")
    return removed


# ── Upgrade ───────────────────────────────────────────────────────────────

def upgrade_skills(skills_dir, target_project, ide, skill_names=None):
    """Upgrade installed BMAD skills: show changes, then reinstall.

    Only upgrades skills that are already installed. New skills are skipped
    unless explicitly listed in skill_names.
    """
    installed = get_installed_skills(target_project, ide)
    available = discover_available_skills(skills_dir)

    if skill_names:
        to_upgrade = [s for s in skill_names if s in available]
    else:
        to_upgrade = [s for s in installed if s in available]

    if not to_upgrade:
        print_warn("No BMAD skills to upgrade")
        return 0

    print_header(f"Upgrading BMAD Skills — {IDE_CONFIGS[ide]['name']}")
    print_info(f"Target: {target_project}")
    print_info(f"Skills to check: {len(to_upgrade)}")
    print()

    changed = []
    unchanged = []

    for name in to_upgrade:
        # Compare source and installed content
        src_skill_md = os.path.join(skills_dir, name, "SKILL.md")
        if not os.path.isfile(src_skill_md):
            continue

        with open(src_skill_md, "r", encoding="utf-8") as f:
            src_content = f.read()

        # Get installed content
        installed_content = _get_installed_content(target_project, ide, name)

        if installed_content is None:
            changed.append((name, "new"))
        elif _content_differs(src_content, installed_content):
            changed.append((name, "modified"))
        else:
            unchanged.append(name)

    if unchanged:
        print(f"  {DIM}Unchanged: {len(unchanged)} skill(s){RESET}")

    if not changed:
        print()
        print(f"  {BOLD}All skills are up to date!{RESET}")
        return 0

    print()
    for name, change_type in changed:
        icon = "+" if change_type == "new" else "~"
        label = "new" if change_type == "new" else "updated"
        print(f"  {YELLOW}{icon}{RESET} {name} {DIM}({label}){RESET}")
    print()

    # Perform the upgrade (reinstall changed skills only)
    names_to_install = [name for name, _ in changed]
    count = install_skills(skills_dir, target_project, ide, names_to_install)

    return count


def _get_installed_content(target_project, ide, name):
    """Read the installed skill content for comparison."""
    if ide == "trae":
        path = os.path.join(target_project, ".trae", "skills", name, "SKILL.md")
    elif ide == "cursor":
        path = os.path.join(target_project, ".cursor", "rules", f"{name}.mdc")
    elif ide == "windsurf":
        path = os.path.join(target_project, ".windsurf", "rules", f"{name}.md")
    elif ide == "claude-code":
        path = os.path.join(target_project, ".claude", "commands", f"{name}.md")
    else:
        return None

    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _content_differs(source, installed):
    """Compare source SKILL.md with installed content (ignoring frontmatter/headers added during conversion)."""
    # Normalize: strip leading/trailing whitespace and compare core content
    # For non-trae IDEs, installed content has added frontmatter/headers,
    # so we just check if the source body is a substring of installed
    src_lines = [l.strip() for l in source.strip().split('\n') if l.strip()]
    inst_lines = [l.strip() for l in installed.strip().split('\n') if l.strip()]

    # Quick check: if line counts differ significantly, content changed
    # Use a simple heuristic: check first 5 and last 5 non-empty lines of source body
    if not src_lines or not inst_lines:
        return True

    # Check key content lines from source appear in installed
    sample_lines = src_lines[:5] + src_lines[-5:]
    matches = sum(1 for line in sample_lines if line in inst_lines)
    return matches < len(sample_lines) * 0.6


# ── Entry Point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="BMAD Full Cycle Installer — install BMAD skills into any AI IDE project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python install.py /path/to/project                    # auto-detect or default trae
              python install.py /path/to/project --ide cursor       # Cursor (.mdc rules)
              python install.py /path/to/project --ide windsurf     # Windsurf (Cascade rules)
              python install.py /path/to/project --ide claude-code  # Claude Code (CLAUDE.md + /commands)
              python install.py /path/to/project --select           # interactive group selection
              python install.py /path/to/project --list             # list available skills
              python install.py /path/to/project --no-init          # skip _bmad/ config creation
              python install.py /path/to/project --upgrade          # upgrade existing skills
              python install.py /path/to/project --uninstall        # remove all BMAD skills

            Supported IDEs:
              trae         Trae IDE — .trae/skills/ directories
              cursor       Cursor — .cursor/rules/*.mdc files
              windsurf     Windsurf — .windsurf/rules/*.md files
              claude-code  Claude Code — CLAUDE.md + .claude/commands/
        """),
    )
    parser.add_argument("project", help="Target project root directory")
    parser.add_argument("--ide", choices=list(IDE_CONFIGS.keys()), default=None,
                        help="Target IDE (auto-detected if omitted)")
    parser.add_argument("--list", action="store_true", dest="list_only",
                        help="List available skills without installing")
    parser.add_argument("--select", action="store_true",
                        help="Interactively select skill groups to install")
    parser.add_argument("--no-init", action="store_true",
                        help="Skip _bmad/ config directory creation")
    parser.add_argument("--uninstall", action="store_true",
                        help="Remove all installed BMAD skills from the project")
    parser.add_argument("--upgrade", action="store_true",
                        help="Upgrade installed skills (only update changed files)")

    args = parser.parse_args()
    skills_dir = get_repo_skills_dir()

    if args.list_only:
        list_skills(skills_dir)
        return

    target = os.path.abspath(args.project)
    if not os.path.isdir(target):
        print_error(f"Directory not found: {target}")
        print_info("Create the directory first, or specify an existing project path")
        sys.exit(1)

    # IDE selection: explicit > auto-detect > default
    ide = args.ide
    if ide is None:
        detected = detect_ide(target)
        if detected:
            ide = detected
            print_info(f"Auto-detected IDE: {IDE_CONFIGS[ide]['name']}")
        else:
            ide = "trae"
            print_info(f"No IDE detected, using default: {IDE_CONFIGS[ide]['name']}")

    # Uninstall mode
    if args.uninstall:
        uninstall_skills(target, ide)
        return

    # Upgrade mode
    if args.upgrade:
        upgrade_skills(skills_dir, target, ide)
        return

    # Skill selection
    selected = select_skills_interactive(skills_dir) if args.select else None

    # Install
    count = install_skills(skills_dir, target, ide, selected)
    if count == 0:
        print_warn("No skills installed")
        return

    # Init
    if not args.no_init:
        init_bmad(target, ide)

    # Harness
    install_harness(target)

    # Next steps
    print_next_steps(target, ide)


if __name__ == "__main__":
    main()

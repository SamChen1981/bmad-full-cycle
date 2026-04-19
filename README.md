# BMAD Full Cycle

AI-driven end-to-end development: describe a feature, get working code + full documentation.

Supports **Trae**, **Cursor**, **Windsurf**, and **Claude Code**. One install script adapts to your IDE's native format.

Includes a **Harness runtime** for phase-gated state persistence, gatekeeper validation, and git-integrated rollback — so you can manage the entire lifecycle from a CLI, independent of the AI chat.

## Quick Start

```bash
git clone https://github.com/SamChen1981/bmad-full-cycle.git
python bmad-full-cycle/install.py /path/to/your-project
```

The installer auto-detects your IDE (or defaults to Trae). To specify explicitly:

```bash
python install.py /path/to/project --ide trae        # Trae
python install.py /path/to/project --ide cursor       # Cursor
python install.py /path/to/project --ide windsurf     # Windsurf
python install.py /path/to/project --ide claude-code  # Claude Code
```

### What the installer does

| IDE | Rule format | Location |
|-----|-------------|----------|
| **Trae** | Skill directories (`SKILL.md` + supporting files) | `.trae/skills/bmad-*/` |
| **Cursor** | `.mdc` files (frontmatter: description/alwaysApply) | `.cursor/rules/bmad-*.mdc` |
| **Windsurf** | `.md` workspace rules | `.windsurf/rules/bmad-*.md` |
| **Claude Code** | Slash commands + `CLAUDE.md` | `.claude/commands/bmad-*.md` |

For Cursor/Windsurf/Claude Code, supporting files (templates, steps, scripts) are placed in `_bmad/skills/` and referenced from the rule files. Paths are automatically rewritten to relative form during installation.

The installer also creates `_bmad/bmm/config.yaml` (project config) and `_bmad-output/` (output directories).

### Install options

```bash
python install.py /path/to/project --select      # Interactive group selection
python install.py /path/to/project --list         # List all 47 skills
python install.py /path/to/project --no-init      # Skip _bmad/ config creation
python install.py /path/to/project --upgrade      # Upgrade existing skills to latest
python install.py /path/to/project --uninstall    # Remove all BMAD skills
```

## Repository Structure

```
bmad-full-cycle/
├── install.py              ← One-click installer (multi-IDE, --upgrade, --uninstall)
├── SKILL.md                ← bmad-full-cycle master skill definition
├── skills/                 ← 47 BMAD skills in 9 groups
│   ├── bmad-autopilot/
│   ├── bmad-migration-autopilot/
│   ├── bmad-create-prd/
│   ├── bmad-dev-story/
│   ├── ... (47 total)
│   └── bmad-full-cycle/
├── harness/                ← Runtime infrastructure templates
│   ├── bmad_harness.py     ← Phase controller (atomic I/O, git, retry counters)
│   ├── bmad-gatekeeper.sh  ← Gatekeeper validation script
│   ├── bmad-harness-config.json  ← Phase/agent/subproject config
│   └── memory/
│       └── bmad-state.json ← Persistent state (phases, retries, sprint sync)
├── docs/
│   └── design-principles.md ← Architecture & design rationale
└── README.md
```

## Harness Runtime

The `harness/` directory is a self-contained runtime toolkit that you copy into your project. It solves three problems that AI coding assistants cannot solve on their own: memory across sessions, disciplined phase gates, and automatic git checkpoints.

### Setup

```bash
cp -r bmad-full-cycle/harness/ /path/to/your-project/bmad-harness/
```

Then edit `bmad-harness/bmad-harness-config.json` to match your project's subprojects, phases, and agent roles. Customize `bmad-gatekeeper.sh` with your build/test commands.

### CLI Commands

```bash
# Check current status
python bmad-harness/bmad_harness.py status

# Transition to next phase (gatekeeper checks + auto git commit/tag)
python bmad-harness/bmad_harness.py transition design

# Force transition (skip phase order validation)
python bmad-harness/bmad_harness.py transition implementation --force

# Rollback to previous phase (creates safety branch, then git reset)
python bmad-harness/bmad_harness.py rollback
python bmad-harness/bmad_harness.py rollback design    # rollback to specific phase

# Sync sprint-status.yaml → bmad-state.json
python bmad-harness/bmad_harness.py sync

# Record artifact or blocker
python bmad-harness/bmad_harness.py artifact docs/prd.md
python bmad-harness/bmad_harness.py blocker "Gateway incompatible with WebMVC"

# Retry counter management (compile/test max 3, review max 2)
python bmad-harness/bmad_harness.py retry 1-1 compile     # increment counter
python bmad-harness/bmad_harness.py retry-reset 1-1       # reset all counters for story
```

### Key Features

**Atomic State Persistence** — All writes to `bmad-state.json` use `tempfile + os.replace + fcntl` locking. If the file gets corrupted, the controller automatically recovers from the `.bak` backup.

**Gatekeeper Validation** — Every phase transition triggers `bmad-gatekeeper.sh`, which runs mechanical checks (file existence, compilation, tests). The AI's "I'm done" doesn't count — only the gatekeeper's verdict does.

**Git Integration** — On each successful phase transition, the controller runs `git add -A && git commit && git tag bmad/{phase}/{timestamp}`. Rollback creates a safety branch before `git reset --hard` to the target tag.

**Retry Counters** — Persistent counters track compile/test/review failures per story. When a counter hits the limit (compile/test = 3, review = 2), the system issues a HALT requiring human intervention.

**Sprint Sync** — Reads `sprint-status.yaml` and writes a progress summary into the phase state, keeping the two state files in sync.

**Illegal Phase Jump Blocking** — Phase transitions must follow the `next` pointer in config. Jumps are blocked by default; use `--force` to override.

## Usage

Open your project in your IDE, then use the AI chat:

### Trae / Cursor / Windsurf

Type in the AI chat panel:

```
I want to build: user management with registration, login, roles, and org structure
```

Or in Chinese:

```
我要做一个功能: 用户管理模块，支持注册登录、角色权限、组织架构
```

### Claude Code

Use slash commands in the CLI:

```
/bmad-full-cycle user management with registration, login, roles, and org structure
```

### Trigger Phrases

| Input | Skill triggered | When to use |
|-------|----------------|-------------|
| `I want to build: [desc]` / `我要做一个功能: [desc]` | bmad-full-cycle | From scratch, fully automated |
| `full cycle: [desc]` / `新功能: [desc]` | bmad-full-cycle | Same as above |
| `start autopilot` / `开始开发` | bmad-autopilot | PRD/arch/epics already exist, just code |
| `start migration` / `开始迁移` | bmad-migration-autopilot | Framework migration scenario |
| `bmad-help` | bmad-help | List all available commands |

### Runtime Controls

| Input | Effect |
|-------|--------|
| `pause` / `暂停` | Stop execution, get detailed progress report |
| `continue` / `继续开发` | Resume from where you paused |
| `sprint status` / `当前进度` | Check current sprint progress |
| `full cycle interactive: [desc]` | Pause after each phase for manual review |

## 8 Phases

| Phase | What | Output |
|-------|------|--------|
| 1 | Requirements → PRD | `_bmad-output/planning-artifacts/prd.md` |
| 2 | Architecture design | `_bmad-output/planning-artifacts/architecture.md` |
| 3 | API contract (OpenAPI 3.0) | `docs/api/openapi.yaml` |
| 4 | Epic & Story breakdown | `_bmad-output/planning-artifacts/epics.md` |
| 5 | Implementation readiness check | Pass or auto-fix |
| 6 | Sprint planning | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| 7 | Auto-coding (loop: create → implement → review) | Source code + DDL + Swagger |
| 8 | Documentation generation | `docs/` complete tech docs |

## 47 Skills in 9 Groups

Run `python install.py /path/to/project --list` for the full list. Summary:

| Group | Key Skills | Purpose |
|-------|-----------|---------|
| Core | bmad-init, bmad-help, bmad-router | Infrastructure, initialization |
| Planning | bmad-create-prd, bmad-create-architecture, bmad-sprint-planning | Requirements → sprint plan |
| Development | bmad-create-story, bmad-dev-story, bmad-code-review | Story-level coding loop |
| Automation | bmad-full-cycle, bmad-autopilot, bmad-migration-autopilot | Fully automated orchestration |
| AI Agents | bmad-agent-pm, bmad-agent-architect, bmad-agent-dev, bmad-agent-qa | Role-based AI personas |
| Research | bmad-domain-research, bmad-market-research, bmad-technical-research | Investigation & analysis |
| Review & QA | bmad-review-edge-case-hunter, bmad-qa-generate-e2e-tests | Quality assurance |
| Documentation | bmad-document-project, bmad-generate-project-context | Doc generation & context |
| Creative | bmad-brainstorming, bmad-create-ux-design, bmad-party-mode | Ideation & design |

Use `--select` to install only the groups you need.

## Output

After a full cycle, your project gains:

```
docs/
├── architecture/      ← System overview, module breakdown, tech stack, deployment topology
├── api/               ← OpenAPI spec, endpoint list, request/response examples
├── implementation/    ← Technical decisions, module design, config reference, error handling
├── database/          ← ER diagram, DDL/DML scripts, data dictionary
├── deployment/        ← Deployment guide
└── changelog.md       ← Change log
```

## Override Rules & Priority Chain

BMAD uses a strict priority chain to control AI behavior during automated execution:

```
HALT > Pause > Override > sub-Skill default
```

**HALT** is a system-initiated forced stop (compile fails 3 times, review fails 2 times, unresolvable dependency conflict). It requires human intervention to continue.

**Pause** is a user-initiated stop. The user says "pause" and the system stops at the next safe point, outputting a progress report.

**Override** rules sit at the top of automation skills (bmad-autopilot, bmad-full-cycle) and suppress the AI's natural tendency to stop and ask "should I continue?". These rules are explicitly marked as higher priority than any sub-skill instruction.

**Sub-Skill defaults** are the built-in behaviors of individual skills (create-story, dev-story, code-review), which may include "ask user to confirm" logic that gets overridden by the automation layer.

## Customization

### Non-Java projects

The default SKILL.md includes Java/Spring conventions (Swagger annotations, DDL scripts). For other stacks, edit the installed skill file:

- **Trae**: `.trae/skills/bmad-full-cycle/SKILL.md`
- **Cursor**: `.cursor/rules/bmad-full-cycle.mdc`
- **Windsurf**: `.windsurf/rules/bmad-full-cycle.md`
- **Claude Code**: `.claude/commands/bmad-full-cycle.md`

Modify the "Phase 7: Swagger" and "SQL documentation" sections to match your stack (e.g., Python/FastAPI, Go/Gin, Node/Express).

### Modify document structure

Edit Phase 8 in the same file to change the output `docs/` structure.

### Adjust auto-decision rules

Edit the bmad-autopilot skill file to change when the AI continues vs halts.

### Customize Harness for your project

1. Copy `harness/` to your project as `bmad-harness/`
2. Edit `bmad-harness-config.json`: set project name, list subprojects, adjust phase definitions
3. Edit `bmad-gatekeeper.sh`: set `BACKEND_PROJECTS` and `FRONTEND_PROJECTS` arrays, adjust build/test commands for your toolchain (Maven, Gradle, npm, cargo, etc.)
4. The `bmad_harness.py` controller generally works as-is — it reads all project-specific info from the config file

## FAQ

**Skills not loading in Trae?**
Restart Trae or reopen the project. Trae scans `.trae/skills/` on project open.

**Cursor doesn't pick up the rules?**
Check `.cursor/rules/` contains `.mdc` files. Type `@bmad-full-cycle` in Cursor chat to explicitly reference a rule.

**PRD is wrong mid-execution?**
Type `pause` / `暂停`, edit `_bmad-output/planning-artifacts/prd.md`, then type `continue` / `继续开发`.

**Can I run individual phases?**
Yes. Use the individual skill directly, e.g., `create architecture` triggers bmad-create-architecture.

**How do I upgrade to a new version?**
Pull the latest repo, then run `python install.py /path/to/project --upgrade`. This replaces existing skills while preserving your `_bmad/` configuration.

**How do I remove all BMAD skills?**
Run `python install.py /path/to/project --uninstall`. This removes skill files but leaves your `_bmad-output/` artifacts intact.

**What if bmad-state.json gets corrupted?**
The harness controller automatically recovers from the `.bak` backup file. If both are corrupted, delete `bmad-state.json` and re-initialize — the harness starts fresh.

**Gitee mirror?**
Also available at: https://gitee.com/chnj1981/bmad-full-cycle

## License

MIT

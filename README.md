# BMAD Full Cycle

AI-driven end-to-end development: describe a feature, get working code + full documentation.

Supports **Trae**, **Cursor**, **Windsurf**, and **Claude Code**. One install script adapts to your IDE's native format.

## Install

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

For Cursor/Windsurf/Claude Code, supporting files (templates, steps, scripts) are placed in `_bmad/skills/` and referenced from the rule files.

The installer also creates `_bmad/bmm/config.yaml` (project config) and `_bmad-output/` (output directories).

### Install options

```bash
python install.py /path/to/project --select    # Interactive group selection
python install.py /path/to/project --list       # List all 47 skills
python install.py /path/to/project --no-init    # Skip _bmad/ config creation
```

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

### Trigger phrases

| Input | Skill triggered | When to use |
|-------|----------------|-------------|
| `I want to build: [desc]` / `我要做一个功能: [desc]` | bmad-full-cycle | From scratch, fully automated |
| `full cycle: [desc]` / `新功能: [desc]` | bmad-full-cycle | Same as above |
| `start autopilot` / `开始开发` | bmad-autopilot | PRD/arch/epics already exist, just code |
| `start migration` / `开始迁移` | bmad-migration-autopilot | Framework migration scenario |
| `bmad-help` | bmad-help | List all available commands |

### Runtime controls

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

## FAQ

**Skills not loading in Trae?**
Restart Trae or reopen the project. Trae scans `.trae/skills/` on project open.

**Cursor doesn't pick up the rules?**
Check `.cursor/rules/` contains `.mdc` files. Type `@bmad-full-cycle` in Cursor chat to explicitly reference a rule.

**PRD is wrong mid-execution?**
Type `pause` / `暂停`, edit `_bmad-output/planning-artifacts/prd.md`, then type `continue` / `继续开发`.

**Can I run individual phases?**
Yes. Use the individual skill directly, e.g., `create architecture` triggers bmad-create-architecture.

**Gitee mirror?**
Also available at: https://gitee.com/chnj1981/bmad-full-cycle

## License

MIT

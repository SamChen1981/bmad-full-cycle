#!/usr/bin/env python3
"""
BMAD Full Cycle 安装脚本

将 BMAD skills 安装到目标项目中，支持 Trae / Cursor / Windsurf 等 AI IDE。

用法:
    python install.py /path/to/your-project              # 默认安装到 Trae
    python install.py /path/to/your-project --ide trae    # 指定 IDE
    python install.py /path/to/your-project --ide cursor
    python install.py /path/to/your-project --list        # 仅列出可用 skills
    python install.py /path/to/your-project --select      # 交互选择要安装的 skills
"""

import argparse
import os
import shutil
import sys
import textwrap

# ── IDE 配置 ──────────────────────────────────────────────────────────────

IDE_CONFIGS = {
    "trae": {
        "name": "Trae",
        "skills_dir": ".trae/skills",
        "description": "字节跳动 Trae IDE",
    },
    "cursor": {
        "name": "Cursor",
        "skills_dir": ".cursor/skills",
        "description": "Cursor AI IDE (如果支持 skills 目录)",
    },
    "windsurf": {
        "name": "Windsurf",
        "skills_dir": ".windsurf/skills",
        "description": "Windsurf AI IDE (如果支持 skills 目录)",
    },
}

# ── Skill 分组 ────────────────────────────────────────────────────────────

SKILL_GROUPS = {
    "core": {
        "name": "核心 (必装)",
        "description": "BMAD 基础设施和项目初始化",
        "skills": [
            "bmad-init",
            "bmad-help",
            "bmad-router",
            "bmad-index-docs",
        ],
    },
    "planning": {
        "name": "规划阶段",
        "description": "需求分析、架构设计、Epic/Story 拆分",
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
        "name": "开发阶段",
        "description": "Story 创建、编码实现、代码审查",
        "skills": [
            "bmad-create-story",
            "bmad-dev-story",
            "bmad-code-review",
            "bmad-correct-course",
        ],
    },
    "automation": {
        "name": "自动化编排",
        "description": "全自动循环执行，无需人工干预",
        "skills": [
            "bmad-full-cycle",
            "bmad-autopilot",
            "bmad-migration-autopilot",
            "bmad-quick-dev",
        ],
    },
    "agents": {
        "name": "AI 角色代理",
        "description": "不同角色的 AI 代理（PM、架构师、开发、QA 等）",
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
        "name": "研究与分析",
        "description": "领域研究、市场调研、技术调研",
        "skills": [
            "bmad-domain-research",
            "bmad-market-research",
            "bmad-technical-research",
            "bmad-product-brief",
            "bmad-advanced-elicitation",
        ],
    },
    "review": {
        "name": "审查与质量",
        "description": "文档审查、对抗性测试、边界场景",
        "skills": [
            "bmad-editorial-review-prose",
            "bmad-editorial-review-structure",
            "bmad-review-adversarial-general",
            "bmad-review-edge-case-hunter",
            "bmad-qa-generate-e2e-tests",
            "bmad-retrospective",
        ],
    },
    "docs": {
        "name": "文档工具",
        "description": "项目文档生成、上下文提取、知识蒸馏",
        "skills": [
            "bmad-document-project",
            "bmad-generate-project-context",
            "bmad-shard-doc",
            "bmad-distillator",
        ],
    },
    "creative": {
        "name": "创意与设计",
        "description": "头脑风暴、UX 设计、多角色讨论",
        "skills": [
            "bmad-brainstorming",
            "bmad-create-ux-design",
            "bmad-party-mode",
        ],
    },
}

# ── 颜色输出 ──────────────────────────────────────────────────────────────

def supports_color():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

if supports_color():
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    RED = "\033[31m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"
else:
    GREEN = YELLOW = CYAN = RED = BOLD = DIM = RESET = ""


def print_header(text):
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}\n")


def print_success(text):
    print(f"  {GREEN}✓{RESET} {text}")


def print_warn(text):
    print(f"  {YELLOW}⚠{RESET} {text}")


def print_error(text):
    print(f"  {RED}✗{RESET} {text}")


def print_info(text):
    print(f"  {DIM}→{RESET} {text}")


# ── 核心逻辑 ──────────────────────────────────────────────────────────────

def get_repo_skills_dir():
    """获取本仓库中 skills/ 目录的路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skills_dir = os.path.join(script_dir, "skills")
    if not os.path.isdir(skills_dir):
        print_error(f"找不到 skills 目录: {skills_dir}")
        print_info("请确保在 bmad-full-cycle 仓库根目录运行此脚本")
        sys.exit(1)
    return skills_dir


def discover_available_skills(skills_dir):
    """扫描 skills/ 目录，返回可用的 skill 名称列表"""
    skills = []
    for name in sorted(os.listdir(skills_dir)):
        skill_path = os.path.join(skills_dir, name)
        if os.path.isdir(skill_path) and name.startswith("bmad-"):
            skills.append(name)
    return skills


def list_skills(skills_dir):
    """列出所有可用 skills（按分组）"""
    available = set(discover_available_skills(skills_dir))

    print_header("可用的 BMAD Skills")

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
                with open(skill_md, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("description:"):
                            desc = line.split(":", 1)[1].strip().strip('"')
                            break
                        if line.startswith("# "):
                            desc = line[2:].strip()
                            break
            print(f"    {GREEN}•{RESET} {skill_name}  {DIM}{desc}{RESET}")
            total += 1
        print()

    # 未归类的 skills
    grouped = set()
    for group in SKILL_GROUPS.values():
        grouped.update(group["skills"])
    ungrouped = [s for s in available if s not in grouped]
    if ungrouped:
        print(f"  {BOLD}其他{RESET}")
        for skill_name in ungrouped:
            print(f"    {GREEN}•{RESET} {skill_name}")
            total += 1
        print()

    print(f"  {BOLD}共 {total} 个 skills{RESET}\n")


def select_skills_interactive(skills_dir):
    """交互式选择要安装的 skill 分组"""
    available = set(discover_available_skills(skills_dir))

    print_header("选择要安装的 Skill 分组")
    print("  输入分组编号（逗号分隔），或直接回车安装全部:\n")

    group_list = []
    for i, (group_id, group) in enumerate(SKILL_GROUPS.items(), 1):
        count = len([s for s in group["skills"] if s in available])
        if count == 0:
            continue
        marker = f"{YELLOW}*{RESET}" if group_id in ("core", "planning", "development", "automation") else " "
        print(f"  {marker} [{i}] {group['name']}  {DIM}({count} skills) — {group['description']}{RESET}")
        group_list.append((group_id, group))

    print(f"\n  {DIM}带 * 的是 full-cycle 流程必需的分组{RESET}")
    print()

    try:
        answer = input(f"  选择 (直接回车=全部): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)

    selected_skills = set()

    if not answer:
        # 全部安装
        for s in available:
            selected_skills.add(s)
    else:
        indices = [x.strip() for x in answer.split(",")]
        for idx_str in indices:
            try:
                idx = int(idx_str) - 1
                if 0 <= idx < len(group_list):
                    group_id, group = group_list[idx]
                    for s in group["skills"]:
                        if s in available:
                            selected_skills.add(s)
            except ValueError:
                print_warn(f"忽略无效输入: {idx_str}")

    # 确保 core 始终包含
    for s in SKILL_GROUPS["core"]["skills"]:
        if s in available:
            selected_skills.add(s)

    return sorted(selected_skills)


def install_skills(skills_dir, target_project, ide, skill_names=None):
    """安装 skills 到目标项目"""
    available = discover_available_skills(skills_dir)

    if skill_names is None:
        skill_names = available
    else:
        # 验证所有指定的 skill 存在
        for name in skill_names:
            if name not in available:
                print_warn(f"跳过不存在的 skill: {name}")
        skill_names = [s for s in skill_names if s in available]

    ide_config = IDE_CONFIGS[ide]
    target_skills_dir = os.path.join(target_project, ide_config["skills_dir"])

    print_header(f"安装 BMAD Skills → {ide_config['name']}")
    print_info(f"目标项目: {target_project}")
    print_info(f"Skills 目录: {target_skills_dir}")
    print_info(f"待安装: {len(skill_names)} 个 skills")
    print()

    # 创建目标目录
    os.makedirs(target_skills_dir, exist_ok=True)

    installed = 0
    skipped = 0
    updated = 0

    for skill_name in skill_names:
        src = os.path.join(skills_dir, skill_name)
        dst = os.path.join(target_skills_dir, skill_name)

        if os.path.exists(dst):
            # 已存在 → 覆盖更新
            shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print_success(f"{skill_name} {DIM}(已更新){RESET}")
            updated += 1
        else:
            shutil.copytree(src, dst)
            print_success(f"{skill_name}")
            installed += 1

    print()
    print(f"  {BOLD}完成！{RESET}")
    print_info(f"新安装: {installed}")
    if updated:
        print_info(f"已更新: {updated}")
    if skipped:
        print_info(f"已跳过: {skipped}")

    return installed + updated


def init_bmad(target_project, ide):
    """在目标项目中创建基础 _bmad 目录结构"""
    bmad_dir = os.path.join(target_project, "_bmad", "bmm")
    config_file = os.path.join(bmad_dir, "config.yaml")

    if os.path.isfile(config_file):
        print_info(f"_bmad/bmm/config.yaml 已存在，跳过初始化")
        return

    print_header("初始化 BMAD 项目配置")

    os.makedirs(bmad_dir, exist_ok=True)

    # 获取项目名称（从目录名推导）
    project_name = os.path.basename(os.path.normpath(target_project))

    config_content = textwrap.dedent(f"""\
        # BMAD 项目配置
        # 由 install.py 自动生成，可手动编辑
        #
        # 详细配置说明: 在 Trae AI 对话中输入 "bmad-help" 查看

        project:
          name: {project_name}
          root: .

        # 产出物路径
        paths:
          planning_artifacts: _bmad-output/planning-artifacts
          implementation_artifacts: _bmad-output/implementation-artifacts

        # 如需配置模块、技术栈等高级选项，
        # 请在 {IDE_CONFIGS[ide]['name']} AI 对话中输入:
        #   初始化 bmad 项目
        # AI 会交互式引导你完成完整配置
    """)

    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config_content)

    # 创建输出目录
    os.makedirs(os.path.join(target_project, "_bmad-output", "planning-artifacts"), exist_ok=True)
    os.makedirs(os.path.join(target_project, "_bmad-output", "implementation-artifacts"), exist_ok=True)

    print_success(f"已创建 _bmad/bmm/config.yaml")
    print_success(f"已创建 _bmad-output/ 目录结构")
    print_info(f"如需完整配置，可在 {IDE_CONFIGS[ide]['name']} AI 对话中输入: 初始化 bmad 项目")


def print_next_steps(target_project, ide):
    """打印安装后的操作指引"""
    ide_config = IDE_CONFIGS[ide]
    name = ide_config["name"]

    print_header("下一步操作")

    print(f"  {BOLD}1. 用 {name} 打开项目{RESET}")
    print(f"     File → Open Folder → {target_project}\n")

    print(f"  {BOLD}2. 打开 AI 对话面板{RESET}")
    if ide == "trae":
        print(f"     点击右侧 Chat 面板，或按 Cmd+L (macOS) / Ctrl+L (Windows)\n")
    else:
        print(f"     打开 {name} 的 AI 对话面板\n")

    print(f"  {BOLD}3. 开始使用{RESET}")
    print(f"     在对话框输入以下任一命令:\n")
    print(f"     {CYAN}我要做一个功能: 用户管理模块{RESET}  ← 全流程开发 (bmad-full-cycle)")
    print(f"     {CYAN}开始开发{RESET}                      ← 自动执行已有 Sprint (bmad-autopilot)")
    print(f"     {CYAN}bmad-help{RESET}                     ← 查看所有可用命令")
    print()


# ── 入口 ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="BMAD Full Cycle 安装脚本 — 将 BMAD skills 安装到你的项目中",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            示例:
              python install.py /path/to/my-project                # 安装全部 skills 到 Trae 项目
              python install.py /path/to/my-project --ide cursor   # 安装到 Cursor 项目
              python install.py /path/to/my-project --select       # 交互式选择分组
              python install.py /path/to/my-project --list         # 仅列出可用 skills
              python install.py /path/to/my-project --no-init      # 安装 skills 但不初始化配置
        """),
    )
    parser.add_argument(
        "project",
        help="目标项目的根目录路径",
    )
    parser.add_argument(
        "--ide",
        choices=list(IDE_CONFIGS.keys()),
        default="trae",
        help="目标 IDE (默认: trae)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_only",
        help="仅列出可用的 skills，不安装",
    )
    parser.add_argument(
        "--select",
        action="store_true",
        help="交互式选择要安装的 skill 分组",
    )
    parser.add_argument(
        "--no-init",
        action="store_true",
        help="不创建 _bmad/ 基础配置目录",
    )

    args = parser.parse_args()
    skills_dir = get_repo_skills_dir()

    # 仅列出
    if args.list_only:
        list_skills(skills_dir)
        return

    # 验证目标项目目录
    target = os.path.abspath(args.project)
    if not os.path.isdir(target):
        print_error(f"目标目录不存在: {target}")
        print_info("请先创建项目目录，或指定已有项目路径")
        sys.exit(1)

    # 选择 skills
    if args.select:
        selected = select_skills_interactive(skills_dir)
    else:
        selected = None  # None = 全部

    # 安装
    count = install_skills(skills_dir, target, args.ide, selected)

    if count == 0:
        print_warn("没有安装任何 skill")
        return

    # 初始化
    if not args.no_init:
        init_bmad(target, args.ide)

    # 下一步
    print_next_steps(target, args.ide)


if __name__ == "__main__":
    main()

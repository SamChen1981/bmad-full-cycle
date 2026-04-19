#!/usr/bin/env python3
"""
BMAD Harness Controller - 核心控制器（通用模板）
管理 BMAD 流程的阶段状态和关卡检查。

用法:
  python bmad_harness.py status              - 查看当前状态
  python bmad_harness.py transition <phase>   - 转换到指定阶段
  python bmad_harness.py transition <phase> --force  - 强制跳转
  python bmad_harness.py artifact <path>      - 添加产出物
  python bmad_harness.py blocker <desc>       - 添加阻碍项
  python bmad_harness.py sync                 - 同步 sprint-status.yaml
  python bmad_harness.py rollback [phase]     - 回滚到上一阶段
  python bmad_harness.py retry <story> <type> - 递增重试计数
  python bmad_harness.py retry-reset <story>  - 重置重试计数

安装:
  将本 harness/ 目录复制到你的项目根目录（或其子目录）。
  根据项目需求修改 bmad-harness-config.json 和 bmad-gatekeeper.sh。
"""

import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class BMADHarness:
    def __init__(self):
        # harness 文件所在目录
        self.harness_dir = os.path.dirname(os.path.abspath(__file__))
        # 项目根目录 = harness 目录的上一级
        self.project_root = os.path.dirname(self.harness_dir)
        self.config_path = os.path.join(self.harness_dir, "bmad-harness-config.json")
        self.state_path = os.path.join(self.harness_dir, "memory", "bmad-state.json")
        self.sprint_status_path = os.path.join(
            self.project_root, "_bmad-output", "implementation-artifacts", "sprint-status.yaml"
        )
        self.gatekeeper_path = os.path.join(self.harness_dir, "bmad-gatekeeper.sh")
        self.config = self._load_json(self.config_path)
        self.state = self._load_json(self.state_path)

    # ── Git 操作 ────────────────────────────────────────────────────────

    def _run_git(self, *args):
        """在项目根目录执行 git 命令，返回 (success, stdout, stderr)"""
        try:
            result = subprocess.run(
                ['git'] + list(args),
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except FileNotFoundError:
            return False, "", "git not found"
        except Exception as e:
            return False, "", str(e)

    def _is_git_repo(self):
        """检查项目根目录是否为 git 仓库"""
        ok, _, _ = self._run_git('rev-parse', '--is-inside-work-tree')
        return ok

    def _git_has_changes(self):
        """检查是否有未提交的变更"""
        ok, stdout, _ = self._run_git('status', '--porcelain')
        return ok and len(stdout) > 0

    def git_commit_phase(self, phase_name, message=None):
        """为指定阶段创建 git commit + tag

        Returns:
            (success, commit_hash) 或 (False, error_msg)
        """
        if not self._is_git_repo():
            print("[Harness] 项目不是 git 仓库，跳过 git 操作")
            return True, "no-git"

        if not self._git_has_changes():
            print("[Harness] 没有未提交的变更，跳过 commit")
            tag_name = f"bmad/{phase_name}/{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            ok, _, err = self._run_git('tag', tag_name)
            if ok:
                print(f"[Harness] 已创建 tag: {tag_name}")
            return True, "no-changes"

        # Stage all changes
        ok, _, err = self._run_git('add', '-A')
        if not ok:
            print(f"[Harness] git add 失败: {err}")
            return False, err

        # Commit
        commit_msg = message or f"[BMAD] Phase '{phase_name}' completed"
        ok, stdout, err = self._run_git('commit', '-m', commit_msg)
        if not ok:
            print(f"[Harness] git commit 失败: {err}")
            return False, err

        # 获取 commit hash
        _, commit_hash, _ = self._run_git('rev-parse', '--short', 'HEAD')
        print(f"[Harness] Git commit: {commit_hash} - {commit_msg}")

        # 创建 tag
        tag_name = f"bmad/{phase_name}/{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        ok, _, err = self._run_git('tag', tag_name)
        if ok:
            print(f"[Harness] 已创建 tag: {tag_name}")
        else:
            print(f"[Harness] 创建 tag 失败 (非致命): {err}")

        return True, commit_hash

    def git_rollback_phase(self, phase_name=None):
        """回滚到上一个阶段的 git 状态

        策略: 找到最近的 bmad/ tag 并 reset --hard 到那个点。
        如果指定了 phase_name，则回滚到该阶段对应的最后一个 tag。

        Returns:
            (success, message)
        """
        if not self._is_git_repo():
            print("[Harness] 项目不是 git 仓库，无法回滚")
            return False, "no-git"

        # 查找 bmad tags，按时间倒序
        ok, stdout, _ = self._run_git(
            'tag', '-l', '--sort=-creatordate', 'bmad/*'
        )
        if not ok or not stdout:
            print("[Harness] 没有找到任何 BMAD tag，无法回滚")
            return False, "no-tags"

        tags = stdout.strip().split('\n')

        if phase_name:
            target_tag = None
            for tag in tags:
                if tag.startswith(f"bmad/{phase_name}/"):
                    target_tag = tag
                    break
            if not target_tag:
                print(f"[Harness] 未找到阶段 '{phase_name}' 的 tag")
                return False, f"no-tag-for-{phase_name}"
        else:
            current_phase = self.state.get('currentPhase', '')
            target_tag = None
            for tag in tags:
                if not tag.startswith(f"bmad/{current_phase}/"):
                    target_tag = tag
                    break
            if not target_tag:
                print("[Harness] 没有可回滚的目标 tag")
                return False, "no-rollback-target"

        # 先创建安全分支保存当前状态
        safety_branch = f"bmad-rollback-backup/{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self._run_git('branch', safety_branch)
        print(f"[Harness] 已创建安全备份分支: {safety_branch}")

        # 执行 reset
        ok, _, err = self._run_git('reset', '--hard', target_tag)
        if not ok:
            print(f"[Harness] git reset 失败: {err}")
            return False, err

        print(f"[Harness] 已回滚到: {target_tag}")

        # 同步 harness state: 重新加载回滚后的 state 文件
        self.state = self._load_json(self.state_path)
        print(f"[Harness] 状态已同步到: {self.state.get('currentPhase', 'unknown')}")

        return True, target_tag

    def _load_json(self, path):
        """加载 JSON 文件，带损坏恢复机制"""
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                try:
                    return json.load(f)
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        except json.JSONDecodeError as e:
            # 尝试从备份恢复
            backup_path = path + ".bak"
            if os.path.exists(backup_path):
                print(f"[Harness] {path} 已损坏，正在从备份恢复...")
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self._atomic_write(path, data)
                    print(f"[Harness] 已从备份恢复: {path}")
                    return data
                except (json.JSONDecodeError, IOError):
                    pass
            print(f"[Harness] {path} 已损坏且无可用备份: {e}")
            return {}
        except IOError as e:
            print(f"[Harness] 读取失败 {path}: {e}")
            return {}

    def _atomic_write(self, path, data):
        """原子写入 JSON 文件：先写临时文件再 rename，避免写入中断导致损坏"""
        dir_path = os.path.dirname(path)
        os.makedirs(dir_path, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix='.tmp', prefix='.bmad_')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _save_state(self):
        """保存状态到 bmad-state.json（原子写 + 自动备份）"""
        if os.path.exists(self.state_path):
            backup_path = self.state_path + ".bak"
            try:
                shutil.copy2(self.state_path, backup_path)
            except IOError:
                pass
        self._atomic_write(self.state_path, self.state)

    # ── Sprint Status 同步 ──────────────────────────────────────────────

    def _load_sprint_status(self):
        """加载 sprint-status.yaml，返回解析后的 dict 或 None"""
        if not HAS_YAML:
            return None
        if not os.path.exists(self.sprint_status_path):
            return None
        try:
            with open(self.sprint_status_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[Harness] 读取 sprint-status.yaml 失败: {e}")
            return None

    def _compute_sprint_summary(self, sprint_data):
        """从 sprint-status.yaml 计算进度摘要"""
        if not sprint_data:
            return None
        dev_status = sprint_data.get('development_status', {})
        if not dev_status:
            return None

        total_epics = 0
        done_epics = 0
        total_stories = 0
        done_stories = 0
        in_progress_stories = 0
        backlog_stories = 0

        for epic_key, epic_val in dev_status.items():
            if not isinstance(epic_val, dict):
                continue
            total_epics += 1
            if epic_val.get('status') == 'done':
                done_epics += 1
            stories = epic_val.get('stories', {})
            for story_key, story_val in stories.items():
                if not isinstance(story_val, dict):
                    continue
                total_stories += 1
                s = story_val.get('status', 'backlog')
                if s == 'done':
                    done_stories += 1
                elif s in ('in-progress', 'review', 'ready-for-dev'):
                    in_progress_stories += 1
                else:
                    backlog_stories += 1

        return {
            "epics": {"total": total_epics, "done": done_epics},
            "stories": {
                "total": total_stories,
                "done": done_stories,
                "in_progress": in_progress_stories,
                "backlog": backlog_stories,
            },
        }

    def sync_sprint_status(self):
        """将 sprint-status.yaml 的进度摘要同步到 bmad-state.json"""
        sprint_data = self._load_sprint_status()
        summary = self._compute_sprint_summary(sprint_data)
        if summary is None:
            return

        current_phase = self.state.get('currentPhase')
        if current_phase and current_phase in self.state.get('phases', {}):
            self.state['phases'][current_phase]['sprintSummary'] = summary
            self.state['phases'][current_phase]['sprintSyncedAt'] = datetime.now().isoformat()
            self._save_state()
            done = summary['stories']['done']
            total = summary['stories']['total']
            print(f"[Harness] Sprint 同步完成: {done}/{total} stories done, "
                  f"{summary['epics']['done']}/{summary['epics']['total']} epics done")

    def get_status(self):
        """获取当前项目状态"""
        current_phase = self.state.get('currentPhase', 'unknown')
        phases = self.state.get('phases', {})
        subprojects = self.config.get('subprojects', {})
        project_name = self.state.get('project', self.config.get('project', 'N/A'))
        print(f"\n{'='*55}")
        print(f"  项目: {project_name}")
        print(f"  根目录: {self.project_root}")
        print(f"  当前阶段: {current_phase}")
        print(f"{'='*55}")
        if subprojects:
            print("  子项目:")
            for name, info in subprojects.items():
                print(f"    - {name} ({info.get('tech', 'N/A')})")
            print(f"{'='*55}")
        for phase_name, phase_data in phases.items():
            status = phase_data.get('status', 'unknown')
            icon = '+' if status == 'completed' else '>' if status == 'in_progress' else '-'
            print(f"  [{icon}] {phase_name}: {status}")
        if not phases:
            all_phases = self.config.get('phases', {})
            for p in all_phases:
                icon = '>' if p == current_phase else ' '
                print(f"  [{icon}] {p}")
        # 显示 Sprint 进度（如果有）
        sprint_data = self._load_sprint_status()
        summary = self._compute_sprint_summary(sprint_data)
        if summary:
            s = summary['stories']
            e = summary['epics']
            pct = (s['done'] / s['total'] * 100) if s['total'] > 0 else 0
            print(f"{'='*55}")
            print(f"  Sprint 进度: {s['done']}/{s['total']} stories ({pct:.0f}%)")
            print(f"     Epics: {e['done']}/{e['total']} | "
                  f"进行中: {s['in_progress']} | 待办: {s['backlog']}")
        print(f"{'='*55}\n")
        return self.state

    def transition_phase(self, next_phase_name, force=False):
        """执行阶段转换

        Args:
            next_phase_name: 目标阶段名称
            force: 是否强制跳转（跳过顺序校验），默认 False
        """
        current_phase = self.state.get('currentPhase')

        # 验证下一阶段是否在配置中存在
        if next_phase_name not in self.config.get('phases', {}):
            print(f"[Harness] 未知阶段: {next_phase_name}")
            print(f"   可用阶段: {', '.join(self.config.get('phases', {}).keys())}")
            return False

        # 验证阶段转换顺序是否正确（严格模式）
        if current_phase and current_phase in self.config.get('phases', {}):
            expected_next = self.config['phases'][current_phase].get('next')
            if expected_next and expected_next != next_phase_name:
                if force:
                    print(f"[Harness] 强制跳转: '{current_phase}' -> '{next_phase_name}' "
                          f"(期望: '{expected_next}')")
                else:
                    print(f"[Harness] 非法跳转: 当前阶段 '{current_phase}' 的下一阶段应为 "
                          f"'{expected_next}'，但请求转换到 '{next_phase_name}'")
                    print(f"   如需强制跳转，请使用: python bmad_harness.py transition {next_phase_name} --force")
                    return False

        # 1. 调用 Gatekeeper 进行检查
        print(f"\n[Harness] 正在运行关卡检查: {current_phase} -> {next_phase_name}")
        gatekeeper_result = self._run_gatekeeper(current_phase, next_phase_name)

        if not gatekeeper_result:
            print("[Harness] 关卡检查失败，流程阻断。")
            return False

        # 1.5. Git commit 当前阶段成果（Gatekeeper 通过后）
        if current_phase:
            git_ok, git_info = self.git_commit_phase(current_phase)
            if not git_ok:
                print(f"[Harness] Git commit 失败 (非致命，继续转换): {git_info}")

        # 2. 更新当前阶段为 completed
        if current_phase and current_phase in self.state.get('phases', {}):
            self.state['phases'][current_phase]['status'] = 'completed'
            self.state['phases'][current_phase]['completedAt'] = datetime.now().isoformat()

        # 3. 初始化新阶段
        if 'phases' not in self.state:
            self.state['phases'] = {}

        self.state['currentPhase'] = next_phase_name
        self.state['phases'][next_phase_name] = {
            "status": "in_progress",
            "startedAt": datetime.now().isoformat(),
            "artifacts": [],
            "blockers": []
        }

        self._save_state()
        # 阶段转换后自动同步 Sprint 状态
        self.sync_sprint_status()
        print(f"[Harness] 阶段转换成功: {next_phase_name}")

        # 4. 输出新阶段的 Agent 配置
        agent_config = self.get_current_agent_config()
        if agent_config:
            agent_name = agent_config.get('agent', 'unknown')
            agent_detail = self.config.get('agents', {}).get(agent_name, {})
            print(f"[Harness] 已激活 Agent: {agent_name} ({agent_detail.get('role', 'N/A')})")

        return True

    def _run_gatekeeper(self, current, next_phase):
        """调用 Gatekeeper Shell 脚本进行关卡检查"""
        if not os.path.exists(self.gatekeeper_path):
            print("[Harness] Gatekeeper 脚本不存在，跳过检查。")
            return True

        try:
            result = subprocess.run(
                ['bash', self.gatekeeper_path, str(current or ''), str(next_phase)],
                capture_output=True,
                text=True,
                cwd=self.harness_dir
            )
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(f"[Harness] Gatekeeper stderr: {result.stderr.strip()}")
            return result.returncode == 0
        except Exception as e:
            print(f"[Harness] Gatekeeper 执行异常: {e}")
            return False

    def get_current_agent_config(self):
        """获取当前阶段的 Agent 配置"""
        current_phase = self.state.get('currentPhase')
        if current_phase and current_phase in self.config.get('phases', {}):
            return self.config['phases'][current_phase]
        return None

    def add_artifact(self, artifact_path):
        """为当前阶段添加产出物"""
        current_phase = self.state.get('currentPhase')
        if current_phase and current_phase in self.state.get('phases', {}):
            phase_data = self.state['phases'][current_phase]
            phase_data.setdefault('artifacts', []).append({
                "path": artifact_path,
                "addedAt": datetime.now().isoformat()
            })
            self._save_state()
            print(f"[Harness] 已记录产出物: {artifact_path}")

    def add_blocker(self, description):
        """为当前阶段添加阻碍项"""
        current_phase = self.state.get('currentPhase')
        if current_phase and current_phase in self.state.get('phases', {}):
            phase_data = self.state['phases'][current_phase]
            phase_data.setdefault('blockers', []).append({
                "description": description,
                "addedAt": datetime.now().isoformat(),
                "resolved": False
            })
            self._save_state()
            print(f"[Harness] 已记录阻碍项: {description}")

    # ── 重试计数器（持久化） ─────────────────────────────────────────────

    def get_retry_count(self, story_id, retry_type):
        """获取指定 Story 和类型的当前重试次数

        Args:
            story_id: Story 标识，如 '1-1', '3-2'
            retry_type: 'compile' | 'review' | 'test'

        Returns:
            当前重试次数 (int)
        """
        retries = self.state.get('retryCounters', {})
        key = f"{story_id}:{retry_type}"
        return retries.get(key, {}).get('count', 0)

    def increment_retry(self, story_id, retry_type, reason=""):
        """递增重试计数器并持久化

        Args:
            story_id: Story 标识
            retry_type: 'compile' | 'review' | 'test'
            reason: 失败原因（可选）

        Returns:
            递增后的计数值
        """
        if 'retryCounters' not in self.state:
            self.state['retryCounters'] = {}

        key = f"{story_id}:{retry_type}"
        if key not in self.state['retryCounters']:
            self.state['retryCounters'][key] = {
                "count": 0,
                "storyId": story_id,
                "type": retry_type,
                "history": []
            }

        counter = self.state['retryCounters'][key]
        counter['count'] += 1
        counter['lastRetryAt'] = datetime.now().isoformat()
        if reason:
            counter['history'].append({
                "attempt": counter['count'],
                "reason": reason[:200],  # 截断防止 state 膨胀
                "at": datetime.now().isoformat()
            })

        self._save_state()
        print(f"[Harness] 重试计数 [{story_id}:{retry_type}] = {counter['count']}")
        return counter['count']

    def check_retry_limit(self, story_id, retry_type, max_retries=None):
        """检查是否已达到重试上限

        Args:
            story_id: Story 标识
            retry_type: 'compile' | 'review' | 'test'
            max_retries: 上限值。None 时使用默认值 (compile/test=3, review=2)

        Returns:
            (should_halt, current_count, max_count)
        """
        defaults = {'compile': 3, 'test': 3, 'review': 2}
        limit = max_retries if max_retries is not None else defaults.get(retry_type, 3)
        current = self.get_retry_count(story_id, retry_type)
        return current >= limit, current, limit

    def reset_retry(self, story_id, retry_type=None):
        """重置指定 Story 的重试计数器

        Args:
            story_id: Story 标识
            retry_type: 指定类型，None 表示重置该 Story 的所有计数器
        """
        retries = self.state.get('retryCounters', {})
        if retry_type:
            key = f"{story_id}:{retry_type}"
            if key in retries:
                del retries[key]
                print(f"[Harness] 已重置重试计数 [{key}]")
        else:
            keys_to_remove = [k for k in retries if k.startswith(f"{story_id}:")]
            for k in keys_to_remove:
                del retries[k]
            if keys_to_remove:
                print(f"[Harness] 已重置 [{story_id}] 的所有重试计数")
        self._save_state()


def main():
    """CLI 入口"""
    harness = BMADHarness()

    if len(sys.argv) < 2:
        print("用法:")
        print("  python bmad_harness.py status              - 查看当前状态")
        print("  python bmad_harness.py transition <phase>   - 转换到指定阶段")
        print("  python bmad_harness.py transition <phase> --force  - 强制跳转（跳过顺序校验）")
        print("  python bmad_harness.py artifact <path>      - 添加产出物")
        print("  python bmad_harness.py blocker <desc>       - 添加阻碍项")
        print("  python bmad_harness.py sync                 - 同步 sprint-status.yaml -> bmad-state.json")
        print("  python bmad_harness.py rollback [phase]     - 回滚到上一阶段 (或指定阶段)")
        print("  python bmad_harness.py retry <story> <type>  - 查看/递增重试计数 (type: compile|review|test)")
        print("  python bmad_harness.py retry-reset <story>   - 重置指定 Story 的重试计数")
        return

    command = sys.argv[1]

    if command == "status":
        harness.get_status()
    elif command == "sync":
        harness.sync_sprint_status()
    elif command == "rollback":
        phase = sys.argv[2] if len(sys.argv) >= 3 else None
        success, info = harness.git_rollback_phase(phase)
        if success:
            print(f"\n回滚成功: {info}")
            harness.get_status()
        else:
            print(f"\n回滚失败: {info}")
        sys.exit(0 if success else 1)
    elif command == "transition" and len(sys.argv) >= 3:
        next_phase = sys.argv[2]
        force = "--force" in sys.argv[3:]
        success = harness.transition_phase(next_phase, force=force)
        sys.exit(0 if success else 1)
    elif command == "artifact" and len(sys.argv) >= 3:
        harness.add_artifact(sys.argv[2])
    elif command == "blocker" and len(sys.argv) >= 3:
        harness.add_blocker(' '.join(sys.argv[2:]))
    elif command == "retry" and len(sys.argv) >= 4:
        story_id = sys.argv[2]
        retry_type = sys.argv[3]
        count = harness.increment_retry(story_id, retry_type)
        should_halt, current, limit = harness.check_retry_limit(story_id, retry_type)
        if should_halt:
            print(f"[Harness] HALT: [{story_id}:{retry_type}] 已达上限 {current}/{limit}")
            sys.exit(1)
        else:
            print(f"[{story_id}:{retry_type}] = {current}/{limit}")
    elif command == "retry-reset" and len(sys.argv) >= 3:
        story_id = sys.argv[2]
        retry_type = sys.argv[3] if len(sys.argv) >= 4 else None
        harness.reset_retry(story_id, retry_type)
    else:
        print(f"未知命令或参数不足: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

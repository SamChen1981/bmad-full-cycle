#!/bin/bash
# ============================================
# BMAD Gatekeeper - 阶段关卡检查脚本（通用模板）
#
# 使用方式:
#   bash bmad-gatekeeper.sh <current_phase> <next_phase>
#
# 自定义:
#   1. 修改 SUBPROJECTS 数组为你的子项目名称
#   2. 根据项目构建工具调整编译/测试命令 (Maven/Gradle/npm/...)
#   3. 按需增删阶段检查逻辑
# ============================================

CURRENT="$1"
NEXT="$2"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# harness 文件在子目录中，项目根在上一级
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "[Gatekeeper] 正在检查阶段转换: ${CURRENT:-'(初始)'} -> ${NEXT}"
echo "   项目根目录: ${PROJECT_ROOT}"

# ==== 项目配置（按需修改） ====
# 你的子项目列表，用于编译/测试检查
# 示例: BACKEND_PROJECTS=("server" "service-api")
#        FRONTEND_PROJECTS=("web-app" "mobile-app")
BACKEND_PROJECTS=()
FRONTEND_PROJECTS=()

# ---- 工具函数 ----

check_file_exists() {
    local filepath="$1"
    local description="$2"
    if [ ! -f "${PROJECT_ROOT}/${filepath}" ]; then
        echo "  [FAIL] 缺少 ${description} (${filepath})"
        return 1
    fi
    echo "  [OK] ${description}"
    return 0
}

check_dir_notempty() {
    local dirpath="$1"
    local description="$2"
    if [ ! -d "${PROJECT_ROOT}/${dirpath}" ] || [ -z "$(ls -A "${PROJECT_ROOT}/${dirpath}" 2>/dev/null)" ]; then
        echo "  [FAIL] ${description} (${dirpath} 为空或不存在)"
        return 1
    fi
    echo "  [OK] ${description}"
    return 0
}

# 检查 Maven 项目编译
check_maven_compile() {
    local proj="$1"
    if [ -f "${PROJECT_ROOT}/${proj}/pom.xml" ]; then
        echo "  [BUILD] 正在检查 ${proj} 编译..."
        cd "${PROJECT_ROOT}/${proj}"
        mvn compile -q -DskipTests 2>&1 | tail -3
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            echo "  [FAIL] ${proj} 编译失败"
            cd "${PROJECT_ROOT}"
            return 1
        else
            echo "  [OK] ${proj} 编译通过"
        fi
        cd "${PROJECT_ROOT}"
    fi
    return 0
}

# 检查 Maven 项目测试
check_maven_test() {
    local proj="$1"
    if [ -f "${PROJECT_ROOT}/${proj}/pom.xml" ] && [ -d "${PROJECT_ROOT}/${proj}/src/test" ]; then
        echo "  [TEST] 正在运行 ${proj} 测试..."
        cd "${PROJECT_ROOT}/${proj}"
        mvn test -q 2>&1 | tail -5
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            echo "  [FAIL] ${proj} 测试执行失败"
            cd "${PROJECT_ROOT}"
            return 1
        else
            echo "  [OK] ${proj} 测试通过"
        fi
        cd "${PROJECT_ROOT}"
    fi
    return 0
}

# ---- 阶段检查 ----

ERRORS=0

case "${CURRENT}" in
    "requirements")
        echo "[Gatekeeper] 正在验证需求阶段产出物..."
        # 检查 PRD 文档 (docx 或 md)
        PRD_FOUND=0
        for ext in md docx pdf; do
            if ls "${PROJECT_ROOT}"/docs/*PRD*."${ext}" 1>/dev/null 2>&1 || \
               ls "${PROJECT_ROOT}"/docs/*prd*."${ext}" 1>/dev/null 2>&1; then
                PRD_FOUND=1
                echo "  [OK] PRD 文档存在"
                break
            fi
        done
        if [ ${PRD_FOUND} -eq 0 ]; then
            echo "  [FAIL] 缺少 PRD / 产品需求文档"
            ERRORS=$((ERRORS + 1))
        fi
        # Sprint 计划（如果使用 Sprint 模式）
        # check_file_exists "docs/01_agile_sprint_plan.md" "Sprint 计划文档" || ERRORS=$((ERRORS + 1))
        ;;

    "design")
        echo "[Gatekeeper] 正在验证设计阶段产出物..."
        check_file_exists "docs/architecture_design.md" "架构设计文档" || ERRORS=$((ERRORS + 1))
        # 按需添加更多设计文档检查
        # check_file_exists "docs/database_design.md" "数据库设计文档" || ERRORS=$((ERRORS + 1))

        # 检查至少一个子项目已初始化
        PROJ_INIT=0
        for proj in "${BACKEND_PROJECTS[@]}" "${FRONTEND_PROJECTS[@]}"; do
            if [ -f "${PROJECT_ROOT}/${proj}/pom.xml" ] || \
               [ -f "${PROJECT_ROOT}/${proj}/package.json" ] || \
               [ -f "${PROJECT_ROOT}/${proj}/build.gradle" ]; then
                PROJ_INIT=1
            fi
        done
        if [ ${#BACKEND_PROJECTS[@]} -gt 0 ] || [ ${#FRONTEND_PROJECTS[@]} -gt 0 ]; then
            if [ ${PROJ_INIT} -eq 0 ]; then
                echo "  [FAIL] 没有子项目包含构建配置文件"
                ERRORS=$((ERRORS + 1))
            else
                echo "  [OK] 子项目已初始化"
            fi
        fi
        ;;

    "implementation")
        echo "[Gatekeeper] 正在验证实现阶段产出物..."
        # 检查后端子项目有源码
        for proj in "${BACKEND_PROJECTS[@]}"; do
            check_dir_notempty "${proj}/src" "${proj}/src 目录有代码" || ERRORS=$((ERRORS + 1))
        done
        # 后端编译检查
        for proj in "${BACKEND_PROJECTS[@]}"; do
            check_maven_compile "${proj}" || ERRORS=$((ERRORS + 1))
        done

        # ---- Java 静态质量检测 (bmad-java-code-standards) ----
        JAVA_WARNINGS=0
        JAVA_BLOCKS=0
        for proj in "${BACKEND_PROJECTS[@]}"; do
            JAVA_SRC="${PROJECT_ROOT}/${proj}/src/main/java"
            if [ ! -d "${JAVA_SRC}" ]; then
                continue
            fi
            echo "  [JAVA] 正在扫描 ${proj} Java 代码质量..."

            # [阻断] 扫描 System.out.println / System.err.println / e.printStackTrace()
            SYSOUT_COUNT=$(grep -rn "System\.out\.\|System\.err\.\|\.printStackTrace()" "${JAVA_SRC}" --include="*.java" 2>/dev/null | wc -l | tr -d ' ')
            if [ "${SYSOUT_COUNT}" -gt 0 ]; then
                echo "  [BLOCK] 发现 ${SYSOUT_COUNT} 处 System.out/err 或 printStackTrace（必须替换为 SLF4J 日志）"
                grep -rn "System\.out\.\|System\.err\.\|\.printStackTrace()" "${JAVA_SRC}" --include="*.java" 2>/dev/null | head -5
                JAVA_BLOCKS=$((JAVA_BLOCKS + SYSOUT_COUNT))
            else
                echo "  [OK] 未发现 System.out/err 或 printStackTrace"
            fi

            # [告警] 扫描类头部是否有 @author 和 @since
            MISSING_HEADER=0
            while IFS= read -r jfile; do
                if ! grep -q "@author" "$jfile" 2>/dev/null; then
                    echo "  [WARN] 缺少 @author: ${jfile#${PROJECT_ROOT}/}"
                    MISSING_HEADER=$((MISSING_HEADER + 1))
                fi
                if ! grep -q "@since" "$jfile" 2>/dev/null; then
                    echo "  [WARN] 缺少 @since: ${jfile#${PROJECT_ROOT}/}"
                    MISSING_HEADER=$((MISSING_HEADER + 1))
                fi
            done < <(find "${JAVA_SRC}" -name "*.java" -type f 2>/dev/null)
            if [ "${MISSING_HEADER}" -gt 0 ]; then
                JAVA_WARNINGS=$((JAVA_WARNINGS + MISSING_HEADER))
            else
                echo "  [OK] 所有 Java 类包含 @author 和 @since"
            fi

            # [告警] 扫描超过 300 行的 Java 类文件
            while IFS= read -r jfile; do
                LINE_COUNT=$(wc -l < "$jfile" | tr -d ' ')
                if [ "${LINE_COUNT}" -gt 300 ]; then
                    echo "  [WARN] 类文件超过 300 行 (${LINE_COUNT} 行): ${jfile#${PROJECT_ROOT}/}"
                    JAVA_WARNINGS=$((JAVA_WARNINGS + 1))
                fi
            done < <(find "${JAVA_SRC}" -name "*.java" -type f 2>/dev/null)

            # [告警] 扫描超过 80 行的方法（简易检测：从方法签名到对应的闭合大括号）
            while IFS= read -r jfile; do
                awk '
                /^[[:space:]]*(public|private|protected)[[:space:]]/ && /\{[[:space:]]*$/ {
                    method_start = NR
                    method_line = $0
                    brace_count = 1
                    next
                }
                method_start > 0 {
                    gsub(/[^{]/, "", tmp=$0); brace_count += length(tmp)
                    gsub(/[^}]/, "", tmp=$0); brace_count -= length(tmp)
                    if (brace_count <= 0) {
                        method_len = NR - method_start
                        if (method_len > 80) {
                            printf "  [WARN] 方法超过 80 行 (%d 行) @ %s:%d\n", method_len, FILENAME, method_start
                        }
                        method_start = 0
                    }
                }
                ' "$jfile"
            done < <(find "${JAVA_SRC}" -name "*.java" -type f 2>/dev/null)

            # [阻断] 扫描空 catch 块
            EMPTY_CATCH=$(grep -Pzn "catch\s*\([^)]*\)\s*\{[\s]*\}" "${JAVA_SRC}"/*.java 2>/dev/null | wc -l | tr -d ' ')
            if [ "${EMPTY_CATCH}" -gt 0 ]; then
                echo "  [BLOCK] 发现 ${EMPTY_CATCH} 处空 catch 块（必须记录日志或抛出异常）"
                JAVA_BLOCKS=$((JAVA_BLOCKS + EMPTY_CATCH))
            fi
        done

        if [ ${JAVA_BLOCKS} -gt 0 ]; then
            echo "  [JAVA] 阻断级问题: ${JAVA_BLOCKS} 处，必须修复后才能通过"
            ERRORS=$((ERRORS + JAVA_BLOCKS))
        fi
        if [ ${JAVA_WARNINGS} -gt 0 ]; then
            echo "  [JAVA] 告警级问题: ${JAVA_WARNINGS} 处，建议修复"
        fi
        ;;

    "testing")
        echo "[Gatekeeper] 正在验证测试阶段产出物..."
        TEST_FOUND=0
        for proj in "${BACKEND_PROJECTS[@]}"; do
            if [ -d "${PROJECT_ROOT}/${proj}/src/test" ]; then
                TEST_FOUND=1
                echo "  [OK] ${proj} 有测试目录"
            fi
        done
        for proj in "${FRONTEND_PROJECTS[@]}"; do
            if [ -d "${PROJECT_ROOT}/${proj}/__tests__" ] || \
               [ -d "${PROJECT_ROOT}/${proj}/tests" ] || \
               [ -d "${PROJECT_ROOT}/${proj}/test" ]; then
                TEST_FOUND=1
                echo "  [OK] ${proj} 有测试目录"
            fi
        done
        if [ ${TEST_FOUND} -eq 0 ] && ([ ${#BACKEND_PROJECTS[@]} -gt 0 ] || [ ${#FRONTEND_PROJECTS[@]} -gt 0 ]); then
            echo "  [FAIL] 没有任何子项目包含测试代码"
            ERRORS=$((ERRORS + 1))
        fi
        # 后端测试执行
        for proj in "${BACKEND_PROJECTS[@]}"; do
            check_maven_test "${proj}" || ERRORS=$((ERRORS + 1))
        done
        ;;

    "review")
        echo "[Gatekeeper] 正在验证审查阶段产出物..."
        check_file_exists "_bmad-output/review-report.md" "代码审查报告" || ERRORS=$((ERRORS + 1))
        # 检查编译仍然通过（审查可能引入修改 — 回归检查）
        for proj in "${BACKEND_PROJECTS[@]}"; do
            check_maven_compile "${proj}" || ERRORS=$((ERRORS + 1))
        done
        ;;

    ""|"null"|"None")
        echo "  初始启动，无前置条件检查"
        ;;

    *)
        echo "  未定义的阶段检查: ${CURRENT}，跳过"
        ;;
esac

# ---- 汇总 ----

if [ ${ERRORS} -gt 0 ]; then
    echo ""
    echo "[Gatekeeper] 关卡检查失败: 共 ${ERRORS} 项未通过"
    echo "   请修复以上问题后重试阶段转换。"
    exit 1
fi

echo ""
echo "[Gatekeeper] 关卡检查全部通过，可以进入阶段: ${NEXT}"
exit 0

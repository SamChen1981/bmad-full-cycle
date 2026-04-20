---
failed_layers: '' # set at runtime: comma-separated list of layers that failed or returned empty
---

# Step 2: Review

## RULES

- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- The Blind Hunter subagent receives NO project context — diff only.
- The Edge Case Hunter subagent receives diff and project read access.
- The Acceptance Auditor subagent receives diff, spec, and context docs.

## INSTRUCTIONS

1. If `{review_mode}` = `"no-spec"`, note to the user: "Acceptance Auditor skipped — no spec file provided."

2. Launch parallel subagents without conversation context. If subagents are not available, **and `{autopilot_mode}` = true:** skip subagent delegation — perform all three review roles yourself inline (Blind Hunter, Edge Case Hunter, Acceptance Auditor) and proceed to step 3 without halting. **If `{autopilot_mode}` = false and subagents are not available:** generate prompt files in `{implementation_artifacts}` — one per reviewer role below — and HALT. Ask the user to run each in a separate session (ideally a different LLM) and paste back the findings. When findings are pasted, resume from this point and proceed to step 3.

   - **Blind Hunter** — receives `{diff_output}` only. No spec, no context docs, no project access. Invoke via the `bmad-review-adversarial-general` skill.

   - **Edge Case Hunter** — receives `{diff_output}` and read access to the project. Invoke via the `bmad-review-edge-case-hunter` skill.

   - **Acceptance Auditor** (only if `{review_mode}` = `"full"`) — receives `{diff_output}`, the content of the file at `{spec_file}`, and any loaded context docs. Its prompt:
     > You are an Acceptance Auditor. Review this diff against the spec and context docs. Check for: violations of acceptance criteria, deviations from spec intent, missing implementation of specified behavior, contradictions between spec constraints and actual code. Output findings as a Markdown list. Each finding: one-line title, which AC/constraint it violates, and evidence from the diff.

3. **Subagent failure handling**: If any subagent fails, times out, or returns empty results, append the layer name to `{failed_layers}` (comma-separated) and proceed with findings from the remaining layers.

4. Collect all findings from the completed layers.

5. **Java Standards Auditor** (only if project contains `pom.xml` or `build.gradle` — Java project detected):

   Run an additional review layer using the `bmad-java-code-standards` skill's `review-checklist.md`. Check ALL changed `.java` files in `{diff_output}` against the 8 mandatory rules:

   - **R1 SRP** — single responsibility for classes and methods
   - **R2 OCP** — open-closed principle, no excessive type branching
   - **R3 Factory+Strategy** — design pattern usage for multi-type dispatching
   - **R4 Java Standards** — naming, structure, exception handling, null safety
   - **R5 Class Header** — @author, @since, @modified tags present
   - **R6 Method Docs** — Javadoc + process comments + key-node logging
   - **R7 Log Spec** — unified format `[Module][Operation][Param]`, correct levels, no sensitive data
   - **R8 Code Reuse** — no duplicate code, proper use of utils/base classes/templates

   Each violation produces a finding with: rule ID, severity (`patch` or `critical`), file:line, and specific issue description. Output as a structured table per `review-checklist.md` format.

   If `bmad-java-code-standards` skill is not installed, skip this layer and note: "Java Standards Auditor skipped — bmad-java-code-standards skill not installed."

6. Merge all findings from all layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor, Java Standards Auditor).


## NEXT

Read fully and follow `./step-03-triage.md`

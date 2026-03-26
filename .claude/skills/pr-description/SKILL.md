---
name: pr-description
description: Generate a pull request description from branch commits and diffs. Use this skill whenever the user asks to write, create, generate, or draft a PR description, pull request summary, PR body, or merge request description. Also trigger when the user says things like "describe this PR", "what should the PR say", "write up these changes", or "summarize this branch for a PR". Even casual phrases like "PR desc" or "write the PR" should trigger this skill.
---

# PR Description Generator

Generate a structured pull request description by analyzing all commits on the current branch compared to the base branch.

## Gathering context

1. Determine the base branch. If the user provides one as an argument, use that. Otherwise default to `main`.
2. Get the merge base: `git merge-base <base-branch> HEAD`
3. Get all commits since the merge base with full messages: `git log --reverse --format="### %s%n%n%b" <merge-base>..HEAD`
4. Get the full diff: `git diff <merge-base>..HEAD`
5. Get the list of changed files grouped by status: `git diff --stat <merge-base>..HEAD`

Read through the commits and diff carefully. Understand not just *what* changed but *why*—commit messages often explain motivation, and the diff reveals the actual behavioral changes.

## Writing the description

The description has three sections: a summary paragraph, a categorized summary, and an actions breakdown.

### The summary paragraph

Write 1-3 natural paragraphs at the top (no heading) that explain the overall motivation and purpose of the changes. This is the most important part—it should tell someone *why* this PR exists, not just catalog what it touches.

Lead with specific, concrete names—action names, parameter names, the actual things that changed. Don't abstract them into vague categories like "new looping capabilities" when you can say "Adds `do_while_item` action." The reader should know exactly what's in this PR from the first sentence.

Think about it from the perspective of a reviewer or someone reading the changelog: what problem was being solved? What was broken or missing before? If there are breaking changes, call them out here so they're impossible to miss.

Don't start with "This PR..."—just lead with the substance. For example: "Adds `do_while_item` action and fixes several issues with Docker sandbox environments..." or "The caching layer was silently dropping entries when..."

### The categorized summary

```
## Summary

### Enhancements
 - Description of each enhancement, being specific about parameter names and behaviors added.

### Bug Fixes
 - **Breaking: description here** (for fixes that change existing behavior)
 - Description of each fix
```

Guidelines:
- Only include `### Enhancements` or `### Bug Fixes` if there are items for that category. Skip empty categories entirely.
- Do not include Documentation or Refactoring sections. Only include Enhancements and Bug Fixes. If a refactor changes observable behavior, list it as an enhancement.
- Each bullet should be concise but specific—mention parameter names, function names, and concrete behavioral changes rather than vague descriptions.
- For new actions or parameters with non-obvious behavior, explain the semantics. For example: "Unlike `while_item`, the condition is evaluated after the actions, so `iteration` is 1 on the first condition check."
- Use parenthetical format for secondary identifiers: `--max-tokens` CLI option (`DF_MAX_TOKENS` for env) rather than `--max-tokens` / `DF_MAX_TOKENS`.
- For bug fixes, describe outcomes rather than implementation details. Say "Both the full and log displays can now be cleanly exited" rather than "by raising `KeyboardInterrupt` from the signal handler."
- Explain *why* something matters, not just what it does. Say "making it easier to see which parameters were actually used" rather than "for easier debugging."
- Bold any breaking changes with the `**Breaking:**` prefix. A change is breaking if it alters existing behavior that consumers may depend on.

### The actions breakdown

This section only covers actions (the building blocks of pipelines). Other changes like CLI, infrastructure, or internal refactoring belong in the Summary section bullets, not here.

```
## Actions

### Updated

#### Item

`action_name`
: Description of what changed.

#### Dataset

`another_action`
: Description of what changed.

### Added

#### Item

`new_action`
: What it does and why it was added.

### Removed

#### Item

`removed_action`
: Why it was removed.
```

Guidelines:
- Only include actions—the functions defined in `actions/item/` and `actions/dataset/`. Do not include CLI changes, Docker infrastructure, utility modules, or other non-action code.
- Group actions under `#### Item` or `#### Dataset` sub-headings based on whether they live in `actions/item/` or `actions/dataset/`.
- Use the definition list format: backtick-wrapped name on its own line, then `: ` followed by the description on the next line.
- Only include `### Updated`, `### Added`, or `### Removed` sections that have content. Skip empty ones.
- Skip the entire `## Actions` section if no actions were changed.

### The dependencies breakdown

Place this section between Summary and Components. Check the diff for changes to dependency files (e.g., `pyproject.toml`, `uv.lock`, `package.json`, `requirements.txt`, `Cargo.toml`, `go.mod`, etc.) and list any dependency changes.

```
## Dependencies

### New
- `dependency-name` v0.0.0

### Upgraded
- `dependency-name` v0.0.0 -> v1.0.0

### Removed
- `dependency-name`
```

Guidelines:
- Only include `### New`, `### Upgraded`, or `### Removed` subsections that have content.
- Skip the entire `## Dependencies` section if there are no dependency changes.
- Include the version for New and Upgraded dependencies. For Upgraded, show the old and new version with `->`.
- For Removed dependencies, just the name is sufficient.

## Output

Output the full PR description as markdown. Do not wrap it in a code fence—just output the raw markdown text so the user can copy it directly.

## Example

Here's an example of a well-written PR description to calibrate tone and structure:

---

Adds `do_while_item` action and fixes several issues with Docker sandbox environments, particularly around Python/pip availability and repository setup reliability. The Codex agent Dockerfile was missing Python entirely, setup scripts were silently swallowing errors, and `~/.local/bin` wasn't on PATH—all of which caused repo setup failures that were difficult to diagnose.

This release also introduces pytest plugin support, allowing pipelines to inject custom test behavior without modifying the tests themselves.

Additionally, the `--max-tokens` CLI option enables longer model responses, and Ctrl-C now works correctly when using the `log` display mode.

## Summary

### Enhancements
 - Added `--max-tokens` CLI option (`DF_MAX_TOKENS` for env) to override the default token limit (8096), enabling longer model responses.
 - Add `do_while_item` action, which executes actions at least once and then repeatedly while a condition is true. Unlike `while_item`, the condition is evaluated after the actions, so iteration is 1 on the first condition check.
 - Refactored `while_item` to align its iteration-counting behavior with `do_while_item`.
 - Introduced `test_plugins_dir` parameter to `run_unit_tests` and `run_swe_agent`, allowing pytest plugins to be mounted and auto-loaded in sandbox containers.
 - Pipeline parameters are now logged at startup, making it easier to see which parameters were actually used.
 - Active pytest plugins and environment variables are logged when set.

### Bug Fixes
 - Fixed `setup-repo.sh` swallowing errors by running setup scripts with `bash -e`, so failures propagate instead of being silently ignored.
 - Fixed Codex agent Dockerfile missing Python and pip entirely, which caused repo setup scripts to fail.
 - Fixed permissions issue in Codex Dockerfile where `setup-repo.sh` copy required root.
 - Added `~/.local/bin` to PATH in sandbox and agent Dockerfiles to quiet pip warnings and ensure installed executables are findable.
 - Set `PIP_BREAK_SYSTEM_PACKAGES=1` in Codex Dockerfile to allow pip installs without a virtual environment.
 - Set `HOMEBREW_NO_AUTO_UPDATE=1` in Codex Dockerfile to reduce noise and improve build speed.
 - Fixed Ctrl-C not working when `--display` is `log`. Both the full and log displays can now be cleanly exited.
 - Ensured `updated_at` is set on first run so it is always present in item metadata.

## Dependencies

### Upgraded
- `openai` v1.68.2 -> v1.72.0

## Actions

### Added

#### Item

`do_while_item`
: Executes actions at least once, then continues while a condition is true. Complements the existing `while_item` action.

### Updated

#### Item

`while_item`
: Aligned iteration counter to increment before the loop body, matching `do_while_item` semantics.

`run_swe_agent`
: Added `test_plugins_dir` parameter for mounting pytest plugins into the agent container.

`run_unit_tests`
: Added `test_plugins_dir` parameter for mounting pytest plugins into the sandbox container.

`set_item_metadata`
: Set `updated_at` on first run so it always exists in metadata.

---

Notice how:
- The opening paragraph names `do_while_item` directly instead of saying "new looping capabilities"
- Enhancements explain behavioral semantics ("Unlike `while_item`, the condition is evaluated after the actions...")
- The `while_item` refactor is listed as an enhancement because it changes observable behavior
- Bug fixes describe outcomes ("Both the full and log displays can now be cleanly exited") not implementation ("by raising `KeyboardInterrupt`")
- Secondary identifiers use parenthetical format: `--max-tokens` CLI option (`DF_MAX_TOKENS` for env)
- No spaces around em dashes

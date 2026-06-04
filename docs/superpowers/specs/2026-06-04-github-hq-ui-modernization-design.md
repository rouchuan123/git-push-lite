# GitHub HQ UI Modernization Design

Date: 2026-06-04
Status: Approved design

## Summary

GitHub HQ should keep its lightweight Windows desktop app shape while moving away from the current old-style stacked form layout. The selected direction is a single-page dashboard refresh: the app remains one Tkinter window and keeps the existing Git workflow, but the UI gains a clearer status summary, stronger visual hierarchy, better spacing, and a more prominent primary action area.

The redesign is intentionally scoped to the UI layer. Git command behavior, repository workflow, validation rules, and service boundaries remain the same unless a small UI helper is needed to display state clearly.

## Confirmed Direction

- Direction: light refresh, not a full product redesign.
- Intensity: single-page dashboard.
- Keep the existing Tkinter/ttk desktop stack.
- Keep one selected repository at a time.
- Keep the existing Git command flow through `RepoService` and `GitRunner`.
- Keep the existing change tree behavior and file/folder selection model.
- Keep existing blocking validation for missing repository, missing identity, missing remote, empty commit message, and no selected changes.
- Add a clearer status summary and primary operation area.
- Improve visual hierarchy, spacing, grouping, and button priority.
- Do not add clone, GitHub API repository creation, diff preview, conflict resolution, reset, force push, or branch deletion.

## Window Structure

The main window remains a single Tkinter window, but the layout becomes a dashboard rather than a vertical stack of equal-weight `LabelFrame` sections.

### Top Status Summary

The top area shows the current working context at a glance:

- Selected repository path.
- Current branch.
- `origin` configuration state.
- Git availability.
- Selected change count.

This area should not contain complex editing controls. It is a summary layer that tells the user whether the app is ready to commit or push.

### Main Work Area

The middle area is split into two functional regions:

- Change selection tree: the largest area, because choosing what to commit is the primary task.
- Repository configuration panel: username, email, identity scope, `origin`, branch, and their save actions.

The configuration panel remains editable, but it should not visually dominate the change selection workflow.

### Primary Action Area

The bottom action area contains:

- Commit message input.
- Commit button.
- Push button.
- Commit and Push primary button.
- Pull Remote Updates secondary button.

`Commit and Push` is the primary visual action. Other Git operations are styled as secondary commands.

### Output And Log Area

The output section remains at the bottom, split clearly into:

- Git command output.
- Recent commit log.

The design should make raw output readable without making it compete with the main workflow.

## Code Boundaries

The modernization should mostly affect `src/github_hq/ui.py`.

Existing modules keep their responsibilities:

- `repo_service`: business workflow and Git operation orchestration.
- `git_runner`: subprocess execution and command result capture.
- `status_parser`: status parsing, selection tree creation, and selection state helpers.
- `app_config`: app settings and recent folders.

`GitHubHQApp` remains the window controller. The UI construction code can be reorganized into smaller private builder methods so layout changes stay readable:

- Build theme/style configuration.
- Build top status summary.
- Build repository selector.
- Build repository configuration panel.
- Build change selection panel.
- Build primary action area.
- Build output/log area.

This refactor should stay local to the UI. It should not create a new framework or change the public app entrypoint.

## Data Flow

The existing refresh flow remains:

1. User selects a folder or refreshes the repository.
2. `_refresh_repository()` validates repository state and reads branch, identity, remote, changes, and logs.
3. UI fields are updated.
4. Change tree is rebuilt.
5. Log list is refreshed.
6. Top status summary is refreshed from the same state.

Selection changes should also refresh the selected change count shown in the status summary. Commit, push, commit-and-push, and pull continue to reuse the current service methods and refresh behavior after each operation.

## Error Handling

The redesign does not silently fix risky states. Existing `messagebox` validation and blocking behavior stays in place:

- Missing Git disables Git actions and shows an explanatory status.
- Missing repository blocks repository-specific operations.
- Non-repository folders still ask before `git init`.
- Missing identity still asks the user to fill name and email before saving.
- Missing or invalid `origin` still blocks or reports the remote configuration error.
- Missing branch still asks before creating and switching.
- Empty commit message blocks commit.
- No selected changes blocks commit.
- Pull and push failures still show a dialog and raw Git output.

The new status summary should make these states visible earlier, but it should not replace the existing confirmation and error dialogs for risky operations.

## Testing

The test plan stays focused on logic, not pixel-perfect visual snapshots.

Existing tests should continue to pass. New or adjusted tests should cover pure helper behavior where practical:

- Status summary text or state calculation.
- Selected change count calculation.
- Button enabled/disabled state helper behavior if extracted.
- Preservation of existing tree open-state behavior.

Manual UI verification is required after implementation:

- Launch the app from source.
- Confirm the window opens without layout overlap.
- Confirm repository selection, recent folders, refresh, identity save, remote save, branch field, change selection, commit, push, commit-and-push, pull, output, and log display still behave as before.
- Confirm the UI remains usable at the default `1100x760` window size.

## Acceptance Criteria

- The app still runs as `python -m github_hq`.
- Existing automated tests pass.
- GitHub HQ still supports the version 1 workflow documented in the original design.
- The UI no longer reads as a stack of old-style form boxes.
- The top summary makes repository readiness obvious.
- Change selection is visually prioritized.
- `Commit and Push` is the most prominent action.
- Output and logs remain visible but secondary.
- No Git command behavior changes unexpectedly.

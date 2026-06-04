# GitHub HQ

GitHub HQ is a lightweight Windows desktop tool for committing and pushing a local folder to GitHub.

## Run From Source 

```powershell
$env:PYTHONPATH="src"
python -m github_hq
```

## Test

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

## Build

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

## Version 1 Scope

- Requires Git for Windows.
- Uses the local Git CLI.
- Does not store GitHub credentials.
- Supports selecting all changes, folders, files, and mixed folder/file selections.
- Supports commit, pull with rebase, push, and recent log display.
- Does not support clone, reset, force push, branch deletion, remote deletion, or conflict resolution.

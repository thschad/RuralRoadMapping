$ErrorActionPreference = "Stop"

param(
    [Parameter(Mandatory = $true)]
    [string]$RepoUrl,
    [string]$Branch = "main"
)

if (-not (git rev-parse --is-inside-work-tree 2>$null)) {
    throw "Kein Git-Repository im aktuellen Ordner."
}

$hasOrigin = (git remote | Select-String -Pattern "^origin$" -Quiet)
if ($hasOrigin) {
    git remote set-url origin $RepoUrl
} else {
    git remote add origin $RepoUrl
}

git push -u origin $Branch
Write-Host "Push abgeschlossen: $RepoUrl ($Branch)"

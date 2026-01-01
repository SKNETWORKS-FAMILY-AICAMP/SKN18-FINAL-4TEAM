param(
  [string]$SourceDir = "$(Resolve-Path 'docker/csv_files')",
  [string]$DestDir = "$(Resolve-Path 'docker/database/neo4j/import')"
)

New-Item -ItemType Directory -Force -Path $DestDir | Out-Null

Copy-Item -Path (Join-Path $SourceDir 'coding_problems.csv') -Destination $DestDir -Force
Copy-Item -Path (Join-Path $SourceDir 'coding_problem_language.csv') -Destination $DestDir -Force
Copy-Item -Path (Join-Path $SourceDir 'coding_problems_testcases.csv') -Destination $DestDir -Force

Write-Host "Copied CSVs to $DestDir"

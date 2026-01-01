param(
  [string]$EnvPath = ".env",
  [string]$OutCsv = "docker/database/neo4j/import/livecoding_reports_export.csv"
)

if (!(Test-Path $EnvPath)) {
  throw "Env file not found: $EnvPath"
}

$envPathFull = (Resolve-Path $EnvPath).Path
$outCsvFull = (Resolve-Path (Split-Path $OutCsv -Parent)).Path + [IO.Path]::DirectorySeparatorChar + (Split-Path $OutCsv -Leaf)

$envLines = Get-Content $EnvPath
$DB_USER = ($envLines | Where-Object { $_ -match '^DB_USER=' } | ForEach-Object { $_.Split('=', 2)[1] })
$DB_NAME = ($envLines | Where-Object { $_ -match '^DB_NAME=' } | ForEach-Object { $_.Split('=', 2)[1] })

if (-not $DB_USER -or -not $DB_NAME) {
  throw "DB_USER/DB_NAME not found in .env"
}

$sql = @'
COPY (
  SELECT
    r.session_id,
    r.user_id,
    r.created_at,
    COALESCE((r.graph_output->>'problem_id')::int, cp.problem_id) AS problem_id,
    (COALESCE(r.graph_output->'problem_algorithms', r.problem_evidence->'problem_algorithms', cp.algorithm))::text AS problem_algorithms,
    (COALESCE(r.graph_output->'strategy_algorithms', r.problem_evidence->'strategy_algorithms'))::text AS strategy_algorithms,
    r.problem_eval_score,
    (1 - COALESCE(r.problem_eval_score, 0))::float AS gap_weight,
    r.consistency_status
  FROM livecoding_reports r
  LEFT JOIN coding_problem cp
    ON cp.problem = r.problem_text
  ORDER BY r.created_at DESC
) TO STDOUT WITH CSV HEADER
'@

$cmd = "docker compose -f docker/docker-compose.yml --env-file $envPathFull exec postgres psql -U $DB_USER -d $DB_NAME -c `"$sql`""

$csv = Invoke-Expression $cmd
$csv | Set-Content -Path $outCsvFull
Write-Host "Exported reports to $outCsvFull"

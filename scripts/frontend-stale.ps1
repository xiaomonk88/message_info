# 退出码 1 = 前端源码比 dist 新，需要重新打包；0 = 打包产物是最新的
param([Parameter(Mandatory = $true)][string]$Frontend)

$index = Join-Path $Frontend 'dist\index.html'
if (-not (Test-Path $index)) { exit 1 }
$built = (Get-Item $index).LastWriteTime

$sources = @(Get-ChildItem (Join-Path $Frontend 'src') -Recurse -File -ErrorAction SilentlyContinue)
foreach ($name in 'index.html', 'package.json', 'vite.config.ts') {
    $p = Join-Path $Frontend $name
    if (Test-Path $p) { $sources += Get-Item $p }
}

$newest = ($sources | Measure-Object -Property LastWriteTime -Maximum).Maximum
if ($newest -gt $built) { exit 1 }
exit 0

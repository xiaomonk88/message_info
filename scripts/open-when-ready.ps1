# 等后端可以响应后再打开浏览器，最多等 30 秒
param([int]$Port = 8010)

for ($i = 0; $i -lt 60; $i++) {
    try {
        Invoke-WebRequest -UseBasicParsing -TimeoutSec 1 "http://127.0.0.1:$Port/api/v1/system/health" | Out-Null
        Start-Process "http://localhost:$Port"
        exit 0
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

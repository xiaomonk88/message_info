# 结束之前启动的 Message_Info：旧版双窗口启动器的 cmd 窗口、占用端口的后端 / Vite 进程
param([int]$Port = 8010)

# 旧版 start.bat / dev.bat 打开的 "cmd /k ... uvicorn" 与 "cmd /k ... npm run dev" 窗口
Get-CimInstance Win32_Process -Filter "Name = 'cmd.exe'" |
    Where-Object {
        $_.CommandLine -like '*message_info*backend*uvicorn app.main*' -or
        $_.CommandLine -like '*message_info*frontend*npm run dev*'
    } |
    ForEach-Object { & taskkill.exe /PID $_.ProcessId /T /F | Out-Null }

# 仍在监听端口的进程（后端 / Vite 开发服务器）
Get-NetTCPConnection -LocalPort $Port, 5173 -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

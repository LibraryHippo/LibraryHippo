start "LH dev server" /D%~p0 cmd /C powershell -NoExit .\serve.bat
start "LH tests" /D%~p0 cmd /C powershell -NoExit .\test.cmd
powershell

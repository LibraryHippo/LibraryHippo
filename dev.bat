start "LH dev server" /D%~p0\App cmd /C powershell -NoExit dev_appserver.py --show_mail_body yes .
start "LH working dir" /D%~p0 cmd /C powershell -NoExit

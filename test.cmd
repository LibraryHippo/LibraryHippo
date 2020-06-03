@echo off
setlocal
set PYTHONPATH=%PYTHONPATH%;%ProgramFiles(x86)%\Google\google_appengine;%~dp0\App
set AUTH_DOMAIN=LibraryHippoAuthDomain
py -2.7 -m pytest --looponfail %*

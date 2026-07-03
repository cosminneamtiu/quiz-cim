@echo off
setlocal

set "QUIZ_FILE=%~dp0quiz_site\index.html"

if not exist "%QUIZ_FILE%" (
  echo Could not find the quiz file:
  echo %QUIZ_FILE%
  echo.
  echo Make sure this batch file is still in the main quiz folder.
  pause
  exit /b 1
)

start "" "%QUIZ_FILE%"

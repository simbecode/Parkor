@echo off
echo ============================
echo  Parkor Analyzer 빌드 시작
echo ============================

pyinstaller ^
  --onefile ^
  --windowed ^
  --add-data "main.ui;." ^
  --name "ParkorAnalyzer" ^
  main.py

echo.
if exist dist\ParkorAnalyzer.exe (
    echo 빌드 성공 : dist\ParkorAnalyzer.exe
) else (
    echo 빌드 실패 - 오류 메시지를 확인하세요
)

pause

@echo off
goto :BEGIN
:QTFIVEORG
del dist\%APPNAME%\qtcore4.dll
del dist\%APPNAME%\qtgui4.dll
del dist\%APPNAME%\qtopengl4.dll
del dist\%APPNAME%\qtsvg4.dll
del dist\%APPNAME%\qtxml4.dll
exit /b 0
:BUILDWITHICON
pyinstaller.exe -F --uac-admin --onedir --noconsole --name=%APPNAME% %FILENAME% --clean --paths="%~dp0..\Lib\site-packages" --icon="%SOURCE_PATH%\icon.ico"
exit /b 0
:BUILDWITHOUTICON
pyinstaller.exe -F --uac-admin --onedir --noconsole --name=%APPNAME% %FILENAME% --clean --paths="%~dp0..\Lib\site-packages"
exit /b 0
:BEGIN
set SOURCE_PATH=%~dp1
IF %SOURCE_PATH:~-1%==\ SET SOURCE_PATH=%SOURCE_PATH:~0,-1%
for %%a in (%SOURCE_PATH%) do set APPNAME=%%~na
set FILENAME=%1
set ORIGINAL_PATH="%~dp1"
set OUTPUT_PATH="%~dp1Winx64\"
cd /d "%~dp0"
FOR /D %%p IN ("build") DO rmdir "%%p" /s /q
rmdir build
FOR /D %%p IN ("dist") DO rmdir "%%p" /s /q
rmdir dist
if exist "%SOURCE_PATH%\icon.ico" ( call :BUILDWITHICON ) else ( call :BUILDWITHOUTICON )
del dist\%APPNAME%\libopenblas*.dll /q
if exist "%CD%\dist\%APPNAME%\pyqt5" ( call :QTFIVEORG )
xcopy /s dist\*.* %OUTPUT_PATH% /y
del %APPNAME%.spec
FOR /D %%p IN ("build") DO rmdir "%%p" /s /q
rmdir build
FOR /D %%p IN ("dist") DO rmdir "%%p" /s /q
rmdir dist
pause

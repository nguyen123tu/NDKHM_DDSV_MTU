@echo off
echo ==============================================================
echo FIXING FLUTTER UNICODE PATH ERROR (NO COPY NEEDED)
echo ==============================================================

set VIRTUAL_DRIVE=Z:

subst %VIRTUAL_DRIVE% /D >nul 2>&1
subst %VIRTUAL_DRIVE% "%~dp0."

echo 1. Created virtual drive %VIRTUAL_DRIVE% successfully!
echo 2. Changing working directory...
%VIRTUAL_DRIVE%
cd \

echo 3. Starting Flutter...
echo Tip: To build APK, change 'run' to 'build apk' in this file.
echo.

call flutter run

echo.
echo ==============================================================
echo Finished! Cleaning up...
C:
subst %VIRTUAL_DRIVE% /D
echo Done. Press any key to exit.
pause

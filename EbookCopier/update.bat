@echo off
setlocal

:: === Configuration ===
set "LOCAL_VERSION_FILE=%~dp0EbookCopier\__init__.py"
set "REPO_OWNER=GoobersGaming"
set "REPO_NAME=EbookCopier"
set "BRANCH=main"
set "GITHUB_RAW_URL=https://raw.githubusercontent.com/%REPO_OWNER%/%REPO_NAME%/%BRANCH%/EbookCopier/__init__.py"
set "TARGET_DIR=%~dp0"

:: === Check local version ===
:: Extract local version from __init__.py (local version)
for /f "tokens=2 delims==" %%a in ('findstr "__version__ =" "%LOCAL_VERSION_FILE%"') do set result=%%a
set result=%result:"=%

:: Remove leading and trailing spaces
for /f "tokens=* delims= " %%b in ("%result%") do set LOCAL_VERSION=%%b

:: Debug: Print the local version
echo Local version: %LOCAL_VERSION%

:: === Get GitHub version ===
:: Fetch raw __init__.py from GitHub to check version
echo Fetching GitHub __init__.py to check version...
curl -s "%GITHUB_RAW_URL%" -o "%TEMP%\github_init.py"

:: Extract version from raw GitHub __init__.py
for /f "tokens=2 delims==" %%a in ('findstr "__version__ =" "%TEMP%\github_init.py"') do set result=%%a
set result=%result:"=%

:: Remove leading and trailing spaces
for /f "tokens=* delims= " %%b in ("%result%") do set GITHUB_VERSION=%%b

:: Debug: Print the GitHub version
echo GitHub version: %GITHUB_VERSION%

:: Compare versions
echo Comparing versions...
if "%LOCAL_VERSION%" == "%GITHUB_VERSION%" (
    echo Versions are up to date.
    goto :end
)

:: If GitHub version is newer, download and update
echo Local version is older. Downloading latest version from GitHub...

:: === Download and Extract Zip ===
:: URL for zip download
set "ZIP_URL=https://github.com/%REPO_OWNER%/%REPO_NAME%/archive/refs/heads/%BRANCH%.zip"

:: Temp download location
set "ZIP_FILE=%TEMP%\repo.zip"

echo Downloading repo zip...
curl -L %ZIP_URL% -o "%ZIP_FILE%"

echo Extracting...
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%~dp0' -Force"

:: Move all files and folders from EbookCopier-main to the same folder as the .bat file
echo Moving all contents from EbookCopier-main...
cd "%~dp0"
for /D %%d in (*) do (
    if exist "%%d\EbookCopier.bat" (
        xcopy /E /Y "%%d\*" "%TARGET_DIR%\" >nul
        rmdir /S /Q "%%d"
        echo Moved contents from %%d to %TARGET_DIR%
    )
)

:: Clean up by deleting the zip file
del "%ZIP_FILE%"

echo Done.

:end
pause
endlocal
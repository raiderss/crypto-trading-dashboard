@echo off
setlocal

set "api_keys_file=api_keys.json"

:main_menu
cls
echo *********************************
echo *       Crypto Dashboard        *
echo *********************************
echo * 1. Start Application          *
echo * 2. Exit                       *
echo *********************************
echo.
set /p choice="Please enter your choice (1 to start application, 2 to exit): "

if "%choice%"=="1" goto check_api_keys
if "%choice%"=="2" goto end
goto main_menu

:check_api_keys
if exist "%api_keys_file%" (
    goto verify_api_keys
) else (
    goto request_api_keys
)

:request_api_keys
cls
echo API keys not found. Please enter your API keys.
echo.
set /p newsapi_key="Enter your NewsAPI.org API Key: "
set /p cryptocompare_key="Enter your CryptoCompare API Key: "
(
    echo {^"newsapi^":^"%newsapi_key%^",^"cryptocompare^":^"%cryptocompare_key%^"}
) > "%api_keys_file%"
echo API keys saved to %api_keys_file%.
goto start_app

:verify_api_keys
cls
echo Verifying API keys...
REM Read the api_keys.json file and check if both keys are present
findstr /c:"newsapi" "%api_keys_file%" > nul
if errorlevel 1 (
    echo NewsAPI key not found.
    del "%api_keys_file%"
    goto request_api_keys
)
findstr /c:"cryptocompare" "%api_keys_file%" > nul
if errorlevel 1 (
    echo CryptoCompare key not found.
    del "%api_keys_file%"
    goto request_api_keys
)
goto start_app

:start_app
cls
echo Starting Crypto Dashboard...
python "C:\Users\Raider\OneDrive\Desktop\Crypto\exe.py"
echo Application stopped. Press Enter to return to the main menu...
pause >nul
goto main_menu

:end
echo Exiting...
exit

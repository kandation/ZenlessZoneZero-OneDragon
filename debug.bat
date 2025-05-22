@echo off
chcp 65001 >nul 2>&1
rem เปลี่ยน codepage ของ command prompt เป็น UTF-8 (65001) และซ่อน output รวมถึง error

rem ตรวจสอบว่ารันด้วยสิทธิ์ผู้ดูแลระบบหรือไม่
net session >nul 2>&1
rem คำสั่งนี้จะพยายามแสดงข้อมูล session ปัจจุบัน หากไม่สำเร็จ (เช่น ไม่มีสิทธิ์) จะคืนค่า errorlevel ที่ไม่ใช่ 0 และซ่อน output
if %errorlevel% neq 0 (
    echo -------------------------------
    echo กำลังพยายามขอสิทธิ์ผู้ดูแลระบบ...
    echo -------------------------------
    rem เพิ่มเวลาหน่วง หากเกิดการวนซ้ำไม่สิ้นสุด สามารถหยุดการทำงานของโปรแกรมได้ที่นี่
    timeout /t 2 >nul
    PowerShell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

rem ตรวจสอบว่าพาธมีอักขระภาษาจีนหรือช่องว่างหรือไม่
powershell -command "if ('%~dp0' -match '[\u4e00-\u9fff]') { exit 1 } else { exit 0 }"
if %errorlevel% equ 1 echo [WARN] พาธปัจจุบันมีอักขระภาษาจีน

set "path_check=%~dp0"
if "%path_check%" neq "%path_check: =%" echo [WARN] พาธมีช่องว่าง

:MENU
echo -------------------------------
echo กำลังรันด้วยสิทธิ์ผู้ดูแลระบบ...
echo -------------------------------
echo.&echo 1. กำหนดค่าสภาพแวดล้อม Python (บังคับ)&echo 2. เพิ่มไดเรกทอรีที่ปลอดภัยสำหรับ Git&echo 3. ติดตั้งไลบรารี Pyautogui ใหม่&echo 4. ตรวจสอบพาธ PowerShell&echo 5. สร้างสภาพแวดล้อมเสมือนใหม่ &echo 6. ติดตั้ง PIP และ VIRTUALENV ใหม่&echo 7. ติดตั้ง onnxruntime&echo 8. รันในโหมด DEBUG&echo 9. ออก
echo.
set /p choice=กรุณาใส่ตัวเลขตัวเลือกแล้วกด Enter:

if "%choice%"=="1" goto :CONFIG_PYTHON_ENV
if "%choice%"=="2" goto :ADD_GIT_SAFE_DIR
if "%choice%"=="3" goto :REINSTALL_PY_LIBS_CHOOSE_SOURCE
if "%choice%"=="4" goto :CHECK_PS_PATH
if "%choice%"=="5" goto :VENV
if "%choice%"=="6" goto :PIP_CHOOSE_SOURCE
if "%choice%"=="7" goto :ONNX
if "%choice%"=="8" goto :DEBUG
if "%choice%"=="9" exit /b
echo [ERROR] ตัวเลือกไม่ถูกต้อง กรุณาเลือกใหม่

goto :MENU

:CONFIG_PYTHON_ENV
echo -------------------------------
echo กำลังกำหนดค่าสภาพแวดล้อม Python...
echo -------------------------------

set "MAINPATH=zzz_od\gui\app.py"
set "ENV_DIR=%~dp0.env"

rem เรียกสคริปต์ตั้งค่าสภาพแวดล้อม
call "%~dp0env.bat"
setx "PYTHON" "%~dp0.env\venv\scripts\python.exe"
setx "PYTHONPATH" "%~dp0src"
setx "PYTHONUSERBASE" "%~dp0.env"

set "PYTHON=%~dp0.env\venv\scripts\python.exe"
set "PYTHONPATH=%~dp0src"
set "APPPATH=%PYTHONPATH%\%MAINPATH%"
set "PYTHONUSERBASE=%~dp0.env"

if not exist "%PYTHON%" echo [WARN] ไม่ได้กำหนดค่า Python.exe & pause & exit /b 1
if not exist "%PYTHONPATH%" echo [WARN] ไม่ได้ตั้งค่า PYTHONPATH & pause & exit /b 1
if not exist "%PYTHONUSERBASE%" echo [WARN] ไม่ได้ตั้งค่า PYTHONUSERBASE & pause & exit /b 1
if not exist "%APPPATH%" echo [WARN] การตั้งค่า PYTHONPATH ผิดพลาด ไม่พบ %APPPATH% & pause & exit /b 1

goto :END

:ADD_GIT_SAFE_DIR
echo -------------------------------
echo กำลังพยายามเพิ่มไดเรกทอรีที่ปลอดภัยสำหรับ Git...
echo -------------------------------
setlocal enabledelayedexpansion
set "GIT_PATH=%~dp0.env\PortableGit\bin\git.exe"
set "DIR_PATH=%~dp0"
set "DIR_PATH=%DIR_PATH:\=/%"
set "DIR_PATH=%DIR_PATH:\\=/%"
if "%DIR_PATH:~-1%"=="/" set "DIR_PATH=%DIR_PATH:~0,-1%"
"%GIT_PATH%" config --global --add safe.directory "%DIR_PATH%"
if %errorlevel% neq 0 echo [ERROR] เพิ่มล้มเหลว & pause & exit /b 1
echo [PASS] เพิ่มไดเรกทอรีที่ปลอดภัยสำหรับ Git สำเร็จ

goto :END

:REINSTALL_PY_LIBS_CHOOSE_SOURCE
echo.&echo 1. แหล่ง Tsinghua&echo 2. แหล่ง Aliyun&echo 3. แหล่งทางการ&echo 4. กลับไปเมนูหลัก
echo.
set /p pip_choice=กรุณาเลือกแหล่ง PIP แล้วกด Enter:
if /i "%pip_choice%"=="1" (
set "PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple"
    set "PIP_TRUSTED_HOST_CMD="
    goto :REINSTALL_PY_LIBS
)
if /i "%pip_choice%"=="2" (
    set "PIP_INDEX_URL=http://mirrors.aliyun.com/pypi/simple"
    set "PIP_TRUSTED_HOST_CMD=--trusted-host mirrors.aliyun.com"
    goto :REINSTALL_PY_LIBS
)
if /i "%pip_choice%"=="3" (
    set "PIP_INDEX_URL=https://pypi.org/simple"
    set "PIP_TRUSTED_HOST_CMD="
goto :REINSTALL_PY_LIBS
)
if /i "%pip_choice%"=="4" goto :MENU
echo [ERROR] ตัวเลือกไม่ถูกต้อง กรุณาเลือกใหม่
goto :REINSTALL_PY_LIBS_CHOOSE_SOURCE

:REINSTALL_PY_LIBS
echo -------------------------------
echo กำลังติดตั้งไลบรารี Pyautogui ใหม่...
echo -------------------------------

call "%~dp0env.bat"

set "PYTHON=%~dp0.env\venv\scripts\python.exe"
set "PYTHONPATH=%~dp0src"
set "APPPATH=%PYTHONPATH%\%MAINPATH%"
set "PYTHONUSERBASE=%~dp0.env"

if not exist "%PYTHON%" echo [WARN] ไม่ได้กำหนดค่า Python.exe & pause & exit /b 1
if not exist "%PYTHONPATH%" echo [WARN] ไม่ได้ตั้งค่า PYTHONPATH & pause & exit /b 1
if not exist "%PYTHONUSERBASE%" echo [WARN] ไม่ได้ตั้งค่า PYTHONUSERBASE & pause & exit /b 1
if not exist "%APPPATH%" echo [WARN] การตั้งค่า PYTHONPATH ผิดพลาด ไม่พบ %APPPATH% & pause & exit /b 1

%PYTHON% -m pip uninstall pyautogui -y
%PYTHON% -m pip install -i %PIP_INDEX_URL% %PIP_TRUSTED_HOST_CMD% pyautogui
%PYTHON% -m pip uninstall pygetwindow -y
%PYTHON% -m pip install -i %PIP_INDEX_URL% %PIP_TRUSTED_HOST_CMD% pygetwindow

echo ติดตั้งเสร็จสมบูรณ์...

goto :END

:CHECK_PS_PATH
echo -------------------------------
echo กำลังตรวจสอบและเพิ่มพาธ PowerShell...
echo -------------------------------

set PS_PATH=C:\Windows\System32\WindowsPowerShell\v1.0\
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo ไม่พบพาธ PowerShell กำลังพยายามเพิ่ม...
    setx PATH "%PATH%;C:\Windows\System32\WindowsPowerShell\v1.0\"
    echo เพิ่มพาธ PowerShell ใน System Path แล้ว...
) else (
    echo พาธ PowerShell มีอยู่แล้ว
)

goto :END

:VENV
echo -------------------------------
echo กำลังสร้างสภาพแวดล้อมเสมือนใหม่...
echo -------------------------------

set "PYTHON=%~dp0.env\python\python.exe"

if not exist "%PYTHON%" (
    echo [WARN] ไม่ได้กำหนดค่า Python.exe
    pause
    exit /b 1
)

%PYTHON% -m virtualenv "%~dp0.env\venv" --always-copy

set "input_file=%~dp0config\env.yml"
set "replace_text=python_path: %~dp0.env\venv\scripts\python.exe"

REM ใช้ PowerShell แก้ไขไฟล์ YAML
powershell -Command "(Get-Content '%input_file%') -replace '^(python_path:).*', '%replace_text%' | Set-Content '%input_file%'"

echo สร้างสภาพแวดล้อมเสมือนเสร็จสมบูรณ์...

goto :END

:PIP_CHOOSE_SOURCE
echo.&echo 1. แหล่ง Tsinghua&echo 2. แหล่ง Aliyun&echo 3. แหล่งทางการ&echo 4. กลับไปเมนูหลัก
echo.
set /p pip_choice=กรุณาเลือกแหล่ง PIP แล้วกด Enter:
if /i "%pip_choice%"=="1" (
set "PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple"
    set "PIP_TRUSTED_HOST_CMD="
    goto :PIP
)
if /i "%pip_choice%"=="2" (
    set "PIP_INDEX_URL=http://mirrors.aliyun.com/pypi/simple"
    set "PIP_TRUSTED_HOST_CMD=--trusted-host mirrors.aliyun.com"
    goto :PIP
)
if /i "%pip_choice%"=="3" (
    set "PIP_INDEX_URL=https://pypi.org/simple"
    set "PIP_TRUSTED_HOST_CMD="
goto :PIP
)
if /i "%pip_choice%"=="4" goto :MENU
echo [ERROR] ตัวเลือกไม่ถูกต้อง กรุณาเลือกใหม่
goto :PIP_CHOOSE_SOURCE

:PIP
echo -------------------------------
echo กำลังติดตั้ง PIP และไลบรารี VIRTUALENV ใหม่...
echo -------------------------------

call "%~dp0env.bat"

set "PYTHON=%~dp0.env\python\python.exe"

if not exist "%PYTHON%" echo [WARN] ไม่ได้กำหนดค่า Python.exe & pause & exit /b 1

%PYTHON% %~dp0get-pip.py
%PYTHON% -m pip install virtualenv --index-url %PIP_INDEX_URL% %PIP_TRUSTED_HOST_CMD%
echo ติดตั้งเสร็จสมบูรณ์...

goto :END

:ONNX
echo -------------------------------
echo กำลังติดตั้ง onnxruntime
echo -------------------------------

call "%~dp0env.bat"

set "PYTHON=%~dp0.env\venv\scripts\python.exe"

if not exist "%PYTHON%" echo [WARN] ไม่ได้กำหนดค่า Python.exe & pause & exit /b 1

%PYTHON% -m pip install onnxruntime==1.18.0 --index-url https://pypi.tuna.tsinghua.edu.cn/simple


echo ติดตั้งเสร็จสมบูรณ์...

goto :END

:DEBUG
set "MAINPATH=zzz_od\gui\app.py"
set "ENV_DIR=%~dp0.env"

rem เรียกสคริปต์ตั้งค่าสภาพแวดล้อม
call "%~dp0env.bat"
set "PYTHON=%~dp0.env\venv\scripts\python.exe"
set "PYTHONPATH=%~dp0src"
set "APPPATH=%PYTHONPATH%\%MAINPATH%"
set "PYTHONUSERBASE=%~dp0.env"

rem พิมพ์ข้อมูล
echo [PASS] PYTHON: %PYTHON%
echo [PASS] PYTHONPATH: %PYTHONPATH%
echo [PASS] APPPATH: %APPPATH%
echo [PASS] PYTHONUSERBASE: %PYTHONUSERBASE%

rem ตรวจสอบพาธของไฟล์ Python executable
if not exist "%PYTHON%" (
    echo [WARN] ไม่ได้กำหนดค่า Python.exe
    pause
    exit /b 1
)

rem ตรวจสอบไดเรกทอรี PythonPath
if not exist "%PYTHONPATH%" (
    echo [WARN] ไม่ได้ตั้งค่า PYTHONPATH
    pause
    exit /b 1
)

rem ตรวจสอบไดเรกทอรี PythonUserBase
if not exist "%PYTHONUSERBASE%" (
    echo [WARN] ไม่ได้ตั้งค่า PYTHONUSERBASE
    pause
    exit /b 1
)

rem ตรวจสอบพาธของสคริปต์แอปพลิเคชัน
if not exist "%APPPATH%" (
    echo [WARN] การตั้งค่า PYTHONPATH ผิดพลาด ไม่พบ %APPPATH%
    pause
    exit /b 1
)

echo [INFO] กำลังเริ่ม... เปลี่ยนเป็นโหมด DEBUG

%PYTHON% %APPPATH%

goto :END

:END
echo การดำเนินการเสร็จสมบูรณ์
pause
cls
goto :MENU

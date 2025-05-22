@echo off
chcp 65001 >nul 2>&1

rem ตรวจสอบว่าสคริปต์กำลังทำงานด้วยสิทธิ์ผู้ดูแลระบบหรือไม่
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo -------------------------------
    echo จำเป็นต้องใช้สิทธิ์ผู้ดูแลระบบ!
    echo -------------------------------
    PowerShell -Command "Start-Process '%~dpnx0'  -WindowStyle Hidden -Verb RunAs"
    exit /b
)

echo -------------------------------
echo กำลังทำงานด้วยสิทธิ์ผู้ดูแลระบบ...
echo -------------------------------


set "MAINPATH=zzz_od\application\zzz_one_dragon_app.py"

REM เรียกใช้สคริปต์ตั้งค่าสภาพแวดล้อม
call "%~dp0env.bat"
set "PYTHONPATH=%~dp0src"
set "APPPATH=%PYTHONPATH%\%MAINPATH%"
echo PYTHON=%PYTHON%
echo PYTHONPATH=%PYTHONPATH%
echo APPPATH=%APPPATH%

REM ใช้ PowerShell เพื่อตรวจสอบว่ามีอักขระภาษาจีนในพาธหรือไม่
powershell -command "if ('%~dp0' -match '[\u4e00-\u9fff]') { exit 1 } else { exit 0 }"
if %errorlevel% equ 1 (
    echo คำเตือน: พาธปัจจุบันมีอักขระภาษาจีน
)

REM ตรวจสอบว่ามีช่องว่างในพาธหรือไม่
set "path_check=%~dp0"
if "%path_check%" neq "%path_check: =%" (
    echo คำเตือน: พาธมีช่องว่าง
)

REM รับวันที่ปัจจุบันและจัดรูปแบบเป็น YYYYMMDD
for /f "tokens=2-4 delims=/ " %%a in ('echo %date%') do (
    set year=%%c
    set month=%%a
    set day=%%b
)

REM รับเวลาปัจจุบัน
for /f "tokens=1-3 delims=/: " %%i in ('echo %time%') do (
    set hour=%%i
    set minute=%%j
    set second=%%k
)

REM จัดรูปแบบชั่วโมง นาที และวินาทีให้เป็นเลขสองหลัก
set hour=%hour: =0%
set minute=%minute: =0%
set second=%second: =0%

REM สร้างไดเรกทอรีและชื่อไฟล์ล็อก โดยมีรูปแบบเป็น YYYYMMDD และ HH.MM.SS
set log_dir=%~dp0.log\%year%%month%%day%
set timestamp=%hour%.%minute%.%second%
set "BAT_LOG=%log_dir%\bat_%timestamp%.log"

REM ตรวจสอบและสร้างไดเรกทอรีล็อก
if not exist "%log_dir%" (
    echo ไดเรกทอรีล็อกไม่มีอยู่ กำลังสร้าง...
    mkdir "%log_dir%"
    if %errorlevel% neq 0 (
        echo การสร้างไดเรกทอรีล็อกล้มเหลว
        pause
        exit /b 1
    )
    echo สร้างไดเรกทอรีล็อกสำเร็จ
)

REM ลบไฟล์ทั้งหมดที่ขึ้นต้นด้วย 'bat_' และลงท้ายด้วย '.log'
for /r "%log_dir%" %%F in (bat_*.log) do (
    del "%%F"
    echo กำลังลบไฟล์ล็อกเก่า: %%F
)

REM ตรวจสอบพาธของไฟล์ εκτελέσιμο Python
if not exist "%PYTHON%" (
    echo "ไม่ได้กำหนดค่า Python.exe"
    pause
    exit /b 1
)

REM ตรวจสอบไดเรกทอรี PYTHONPATH
if not exist "%PYTHONPATH%" (
    echo "PYTHONPATH ไม่ได้ตั้งค่า"
    pause
    exit /b 1
)

REM ตรวจสอบพาธของสคริปต์แอปพลิเคชัน
if not exist "%APPPATH%" (
    echo "การตั้งค่า PYTHONPATH ผิดพลาด ไม่พบ %APPPATH%"
    pause
    exit /b 1
)

echo "กำลังเริ่มต้น... อาจใช้เวลาประมาณ 10+ วินาที"
"%PYTHON%" "%APPPATH%" >> "%BAT_LOG%" 2>&1
if %errorlevel% neq 0 (
    echo "เกิดข้อผิดพลาดในการทำงาน โปรดส่งข้อมูลข้อผิดพลาดไปที่ %BAT_LOG%"
    pause
    exit /b 1
)

timeout /t 10

exit 0

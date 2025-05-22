@echo off
rem ปิดการแสดงผลคำสั่งบนหน้าจอ

chcp 65001 2>&1
rem เปลี่ยน codepage ของ command prompt เป็น UTF-8 (65001) และส่ง output รวมถึง error (2>&1) ไปยัง nul (เพื่อไม่ให้แสดงผล)

rem ตรวจสอบว่ารันด้วยสิทธิ์ผู้ดูแลระบบหรือไม่
net session 2>&1
rem คำสั่งนี้จะพยายามแสดงข้อมูล session ปัจจุบัน หากไม่สำเร็จ (เช่น ไม่มีสิทธิ์) จะคืนค่า errorlevel ที่ไม่ใช่ 0
if %errorlevel% neq 0 (
rem ถ้า errorlevel ไม่เท่ากับ 0 (แสดงว่าไม่ได้รันด้วยสิทธิ์ผู้ดูแล)
    echo -------------------------------
    echo กำลังพยายามขอสิทธิ์ผู้ดูแลระบบ...
    echo -------------------------------
    rem เพิ่มเวลาหน่วง หากเกิดการวนซ้ำไม่สิ้นสุด สามารถหยุดการทำงานของโปรแกรมได้ที่นี่
    timeout /t 2
rem หน่วงเวลา 2 วินาที
    PowerShell -Command "Start-Process '%~dpnx0' -Verb RunAs"
rem ใช้ PowerShell เพื่อรันสคริปต์ปัจจุบัน ('%~dpnx0') อีกครั้งด้วยสิทธิ์ผู้ดูแล (-Verb RunAs)
    exit /b
rem ออกจากสคริปต์ปัจจุบัน
)

echo -------------------------------
echo กำลังรันด้วยสิทธิ์ผู้ดูแลระบบ...
echo -------------------------------

set "MAINPATH=zzz_od\gui\app.py"
rem กำหนดตัวแปร MAINPATH เป็นพาธของไฟล์ Python หลัก

set "ENV_DIR=%~dp0.env"
rem กำหนดตัวแปร ENV_DIR เป็นพาธของไดเรกทอรีสภาพแวดล้อมเสมือน (.env) โดย %~dp0 คือพาธของไดเรกทอรีที่สคริปต์นี้อยู่

REM เรียกสคริปต์ตั้งค่าสภาพแวดล้อม
call "%~dp0env.bat"
rem เรียกไฟล์ env.bat ที่อยู่ในไดเรกทอรีเดียวกับสคริปต์นี้ เพื่อตั้งค่าสภาพแวดล้อม
set "PYTHONPATH=%~dp0src"
rem กำหนดตัวแปร PYTHONPATH เป็นพาธของไดเรกทอรี src (ที่อยู่ในไดเรกทอรีเดียวกับสคริปต์นี้)
set "APPPATH=%PYTHONPATH%\%MAINPATH%"
rem กำหนดตัวแปร APPPATH เป็นพาธเต็มของไฟล์ Python หลัก
set "PYTHONUSERBASE=%~dp0.env"
rem กำหนดตัวแปร PYTHONUSERBASE เป็นพาธของไดเรกทอรี .env (สำหรับติดตั้งแพ็คเกจ Python เฉพาะผู้ใช้)

REM พิมพ์ข้อมูล
echo [PASS] PYTHON: %PYTHON%
rem แสดงพาธของ Python executable ที่ถูกตั้งค่าโดย env.bat
echo [PASS] PYTHONPATH: %PYTHONPATH%
rem แสดงค่า PYTHONPATH
echo [PASS] APPPATH: %APPPATH%
rem แสดงพาธของแอปพลิเคชัน
echo [PASS] PYTHONUSERBASE: %PYTHONUSERBASE%
rem แสดงค่า PYTHONUSERBASE

REM ใช้ PowerShell ตรวจสอบว่ามีอักขระภาษาจีนในพาธหรือไม่
powershell -command "if ('%~dp0' -match '[\u4e00-\u9fff]') { exit 1 } else { exit 0 }"
rem ใช้ PowerShell ตรวจสอบว่าพาธปัจจุบัน (%~dp0) มีอักขระภาษาจีน (ช่วง Unicode \u4e00-\u9fff) หรือไม่ ถ้ามี ให้ exit code เป็น 1 ถ้าไม่มี ให้เป็น 0
if %errorlevel% equ 1 (
rem ถ้า exit code จาก PowerShell คือ 1 (มีอักขระภาษาจีน)
    echo [WARN] พาธปัจจุบันมีอักขระภาษาจีน
)

REM ตรวจสอบว่ามีช่องว่างในพาธหรือไม่
set "path_check=%~dp0"
rem กำหนดตัวแปร path_check เป็นพาธปัจจุบัน
if "%path_check%" neq "%path_check: =%" (
rem ตรวจสอบว่า path_check แตกต่างจาก path_check ที่ถูกลบช่องว่างทั้งหมดออกหรือไม่ (ถ้าต่างกัน แสดงว่ามีช่องว่าง)
    echo [WARN] พาธมีช่องว่าง
)

REM ดึงวันที่ปัจจุบันและจัดรูปแบบเป็น YYYYMMDD
for /f "tokens=2-4 delims=/ " %%a in ('echo %date%') do (
rem วนลูปเพื่อแยกส่วนของวันที่ (รูปแบบวันที่ขึ้นอยู่กับการตั้งค่าระบบ อาจจะต้องปรับ delims และ tokens)
    set year=%%c
rem กำหนดปี
    set month=%%a
rem กำหนดเดือน
    set day=%%b
rem กำหนดวัน
)

REM ดึงเวลาปัจจุบัน
for /f "tokens=1-3 delims=/: " %%i in ('echo %time%') do (
rem วนลูปเพื่อแยกส่วนของเวลา (รูปแบบเวลาขึ้นอยู่กับการตั้งค่าระบบ อาจจะต้องปรับ delims และ tokens)
    set hour=%%i
rem กำหนดชั่วโมง
    set minute=%%j
rem กำหนดนาที
    set second=%%k
rem กำหนดวินาที
)

REM จัดรูปแบบชั่วโมงและนาทีเป็นเลขสองหลัก
set hour=%hour: =0%
rem ถ้าชั่วโมงมีช่องว่างนำหน้า (เช่น ' 9') ให้แทนที่ด้วย '0' (เป็น '09')
set minute=%minute: =0%
rem ถ้าทีมีช่องว่างนำหน้า ให้แทนที่ด้วย '0'
set second=%second: =0%
rem ถ้านาทีมีช่องว่างนำหน้า ให้แทนที่ด้วย '0'

REM สร้างไดเรกทอรีและชื่อไฟล์ล็อก รูปแบบเป็น YYYYMMDD และ HH.MM.SS
set log_dir=%~dp0.log\%year%%month%%day%
rem กำหนดพาธไดเรกทอรีล็อก เป็น .log/YYYYMMDD ภายในไดเรกทอรีปัจจุบัน
set timestamp=%hour%.%minute%.%second%
rem กำหนด timestamp เป็น HH.MM.SS
set "BAT_LOG=%log_dir%\bat_%timestamp%.log"
rem กำหนดชื่อไฟล์ล็อกของสคริปต์ batch
set "PYTHON_LOG=%log_dir%\python_%timestamp%.log"
rem กำหนดชื่อไฟล์ล็อกของสคริปต์ Python

REM ตรวจสอบและสร้างไดเรกทอรีล็อก
if not exist "%log_dir%" (
rem ถ้าไดเรกทอรีล็อกไม่มีอยู่
    echo [WARN] ไดเรกทอรีล็อกไม่มีอยู่ กำลังสร้าง...
    mkdir "%log_dir%"
rem สร้างไดเรกทอรีล็อก
    if %errorlevel% neq 0 (
rem ถ้าการสร้างไดเรกทอรีล้มเหลว
        echo [WARN] สร้างไดเรกทอรีล็อกล้มเหลว
        pause
rem หยุดรอการกดปุ่ม
        exit /b 1
rem ออกจากสคริปต์ด้วย error code 1
    )
    echo [PASS] สร้างไดเรกทอรีล็อกสำเร็จ
)

REM ลบไฟล์ทั้งหมดที่ขึ้นต้นด้วย 'bat_' และลงท้ายด้วย '.log'
for /r "%log_dir%" %%F in (bat_*.log) do (
rem วนลูปในไดเรกทอรีล็อกและไดเรกทอรีย่อย (/r) เพื่อหาไฟล์ที่ตรงตามรูปแบบ bat_*.log
    del "%%F"
rem ลบไฟล์ที่พบ
    echo [INFO] ลบไฟล์ล็อกเก่า: %%F
)

REM ตรวจสอบพาธของไฟล์ Python executable
if not exist "%PYTHON%" (
rem ถ้าพาธของ Python executable ที่ตั้งค่าไว้ไม่มีอยู่จริง
    echo [WARN] ไม่ได้กำหนดค่า Python.exe
    pause
    exit /b 1
)

REM ตรวจสอบไดเรกทอรี PythonPath
if not exist "%PYTHONPATH%" (
rem ถ้าไดเรกทอรี PYTHONPATH ไม่มีอยู่จริง
    echo [WARN] ไม่ได้ตั้งค่า PYTHONPATH
    pause
    exit /b 1
)

REM ตรวจสอบไดเรกทอรี PythonUserBase
if not exist "%PYTHONUSERBASE%" (
rem ถ้าไดเรกทอรี PYTHONUSERBASE ไม่มีอยู่จริง
    echo [WARN] ไม่ได้ตั้งค่า PYTHONUSERBASE
    pause
    exit /b 1
)

REM ตรวจสอบพาธของสคริปต์แอปพลิเคชัน
if not exist "%APPPATH%" (
rem ถ้าพาธของสคริปต์แอปพลิเคชันไม่มีอยู่จริง
    echo [WARN] การตั้งค่า PYTHONPATH ผิดพลาด ไม่พบ %APPPATH%
    pause
    exit /b 1
)

echo กำลังเริ่ม... ใช้เวลาประมาณ 5+ วินาที
powershell -Command "& {Start-Process '%PYTHON%' -ArgumentList '%APPPATH%' -NoNewWindow -RedirectStandardOutput '%PYTHON_LOG%' -PassThru}"
rem ใช้ PowerShell เพื่อรันสคริปต์ Python ('%APPPATH%') ด้วย Python executable ('%PYTHON%')
rem -NoNewWindow: ไม่เปิดหน้าต่างใหม่
rem -RedirectStandardOutput '%PYTHON_LOG%': ส่ง output มาตรฐานไปยังไฟล์ล็อก Python
rem -PassThru: ส่งผ่าน object ของ process ที่สร้างขึ้น

REM รอสักครู่แล้วออก
timeout /t 5
rem หน่วงเวลา 5 วินาที

exit 0
rem ออกจากสคริปต์ด้วย error code 0 (สำเร็จ)

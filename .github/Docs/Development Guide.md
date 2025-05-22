# 1. สภาพแวดล้อมการพัฒนา

## 1.1. Python

แนะนำให้ใช้ [3.11.9](https://www.python.org/downloads/release/python-3119/)

## 1.2. สภาพแวดล้อมเสมือน (Virtual Environment)

การรันปกติ

```shell
pip install -r requirements-dev.txt
````

สิ่งที่ต้องใช้เพิ่มเติมสำหรับการพัฒนาและการแพ็กเกจ

```shell
pip install -r requirements-dev-ext.txt
```

สร้างรายการ dependency ที่ใช้จริง

```shell
pip-compile --annotation-style=line --index-url=[https://pypi.tuna.tsinghua.edu.cn/simple](https://pypi.tuna.tsinghua.edu.cn/simple) --output-file=requirements-prod.txt requirements-dev.txt
```

# 2\. การแพ็กเกจ

เข้าไปที่โฟลเดอร์ deploy

## 2.1. ตัวติดตั้ง (Installer)

สร้างไฟล์ spec และทำการแพ็กเกจ

```shell
pyinstaller --onefile --windowed --uac-admin --icon="../assets/ui/installer_logo.ico" --add-data "../config/project.yml;config" ../src/zzz_od/gui/zzz_installer.py -n "OneDragon Installer"
```

แพ็กเกจโดยใช้ไฟล์ spec

```shell
pyinstaller "OneDragon Installer.spec"
```

## 2.2. ตัวเรียกใช้งานแบบเต็ม (Full Launcher)

สร้างไฟล์ spec และทำการแพ็กเกจ

```shell
pyinstaller --onefile --uac-admin --icon="../assets/ui/zzz_logo.ico" ../src/zzz_od/win_exe/full_launcher.py -n "OneDragon Launcher"
```

แพ็กเกจโดยใช้ไฟล์ spec

```shell
pyinstaller "OneDragon Launcher.spec"
```

## 2.3. ตัวเรียกใช้งานแบบครบวงจร (One-Dragon Launcher/Scheduler)

สร้างไฟล์ spec และทำการแพ็กเกจ

```shell
pyinstaller --onefile --uac-admin --icon="../assets/ui/scheduler_logo.ico" ../src/zzz_od/win_exe/scheduler_launcher.py -n "OneDragon Scheduler"
```

แพ็กเกจโดยใช้ไฟล์ spec

```shell
pyinstaller "OneDragon Scheduler.spec"
```


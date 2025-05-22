import sys
import time
import datetime
import os
import subprocess
import yaml
from colorama import init, Fore, Style

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext

# เริ่มต้นการทำงานของ colorama
init(autoreset=True)

# ตั้งค่าไดเรกทอรีการทำงานปัจจุบัน
# ไดเรกทอรีที่เก็บไฟล์ exe สุดท้าย
path = os.path.dirname(sys.argv[0])
os.chdir(path)

def print_message(message, level="INFO"):
    # พิมพ์ข้อความ พร้อมประทับเวลาและระดับของล็อก
    delay(0.1)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    colors = {"INFO": Fore.CYAN, "ERROR": Fore.YELLOW + Style.BRIGHT, "PASS": Fore.GREEN}
    color = colors.get(level, Fore.WHITE)
    print(f"{timestamp} | {color}{level}{Style.RESET_ALL} | {message}")

def delay(seconds):
    # พักการทำงานตามจำนวนวินาทีที่ระบุ
    time.sleep(seconds)

def verify_path_issues():
    # ตรวจสอบปัญหาที่อาจเกิดขึ้นกับพาธ
    if any('\u4e00' <= char <= '\u9fff' for char in path): # ตรวจสอบอักขระภาษาจีน
        print_message("พาธมีอักขระภาษาจีน", "ERROR")
        sys.exit(1)
    if ' ' in path:
        print_message("มีช่องว่างในพาธ", "ERROR")
        sys.exit(1)
    print_message("การตรวจสอบไดเรกทอรีผ่าน", "PASS")

def load_yaml_config(file_path):
    # อ่านไฟล์การกำหนดค่า YAML
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print_message(f"เกิดข้อผิดพลาดในการอ่านไฟล์ YAML: {e}", "ERROR")
        sys.exit(1)

def get_python_path_from_yaml(yaml_file_path):
    # ดึงข้อมูลพาธของไฟล์ εκτελέσιμο Python จากไฟล์ YAML
    print_message("กำลังอ่านไฟล์ YAML...", "INFO")
    config = load_yaml_config(yaml_file_path)
    print_message("อ่านไฟล์ YAML สำเร็จ", "PASS")
    print_message("กำลังเริ่มกำหนดค่าตัวแปรสภาพแวดล้อม...", "INFO")
    python_path = config.get('python_path')
    if not python_path:
        print_message("ไม่สามารถดึงข้อมูล python_path ได้ โปรดตรวจสอบการตั้งค่าพาธ", "ERROR")
        sys.exit(1)
    return python_path

def configure_environment():
    # กำหนดค่าตัวแปรสภาพแวดล้อม
    yaml_file_path = os.path.join(path, "config", "env.yml")
    python_executable_path = get_python_path_from_yaml(yaml_file_path)
    if not os.path.exists(python_executable_path):
        print_message("ไม่พบไฟล์ executable Python โปรดตรวจสอบการตั้งค่าพาธ", "ERROR")
        sys.exit(1)
    os.environ.update({
        'PYTHON': python_executable_path,
        'PYTHONPATH': os.path.join(path, "src"),
        'PYTHONUSERBASE': os.path.join(path, ".env")
    })
    for var in ['PYTHON', 'PYTHONPATH', 'PYTHONUSERBASE']:
        if not os.environ.get(var):
            print_message(f"{var} ไม่ได้ตั้งค่า", "ERROR")
            sys.exit(1)
    print_message(f"PYTHON: {os.environ['PYTHON']}", "PASS")
    print_message(f"PYTHONPATH: {os.environ['PYTHONPATH']}", "PASS")
    print_message(f"PYTHONUSERBASE: {os.environ['PYTHONUSERBASE']}", "PASS")

def create_log_folder():
    # สร้างโฟลเดอร์ล็อก
    print_message("กำลังเริ่มกำหนดค่าล็อก...", "INFO")
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    log_folder = os.path.join(path, ".log", date_str)
    os.makedirs(log_folder, exist_ok=True)
    print_message(f"พาธโฟลเดอร์ล็อก: {log_folder}", "PASS")
    return log_folder

def clean_old_logs(log_folder):
    # ลบไฟล์ล็อกเก่า
    for root, _, files in os.walk(log_folder):
        for file in files:
            if file.startswith('bat_') and file.endswith('.log'):
                os.remove(os.path.join(root, file))
                print_message(f"ลบไฟล์ล็อกเก่าแล้ว: {file}", "PASS")

def execute_python_script(app_path, log_folder, no_windows: bool):
    # รันสคริปต์ Python และเปลี่ยนเส้นทางเอาต์พุตไปยังไฟล์ล็อก
    timestamp = datetime.datetime.now().strftime("%H.%M")
    log_file_path = os.path.join(log_folder, f"python_{timestamp}.log")
    python_executable = os.environ.get('PYTHON')
    app_script_path = os.environ.get('PYTHONPATH')
    for sub_path in app_path: # สร้างพาธเต็มไปยังสคริปต์เป้าหมาย
        app_script_path = os.path.join(app_script_path, sub_path)

    if not os.path.exists(app_script_path):
        print_message(f"การตั้งค่า PYTHONPATH ผิดพลาด ไม่พบ {app_script_path}", "ERROR")
        sys.exit(1)

    # ใช้ PowerShell เพื่อเริ่มสคริปต์ Python และเปลี่ยนเส้นทางเอาต์พุต
    powershell_command = (
        f"Start-Process '{python_executable}' -ArgumentList '{app_script_path}' -NoNewWindow -RedirectStandardOutput '{log_file_path}' -PassThru"
    )
    # ใช้ subprocess.Popen เพื่อเริ่มหน้าต่าง PowerShell ใหม่และรันคำสั่ง
    if no_windows:
        subprocess.Popen(["powershell", "-Command", powershell_command], creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        subprocess.Popen(["powershell", "-Command", powershell_command])
    print_message("OneDragon กำลังเริ่มต้น อาจใช้เวลาประมาณ 5+ วินาที...", "INFO")


def fetch_latest_code(ctx: OneDragonEnvContext) -> None:
    """
    ดึงข้อมูลโค้ดล่าสุด
    """
    if not ctx.env_config.auto_update:
        print_message("ไม่ได้เปิดใช้งานการอัปเดตโค้ดอัตโนมัติ ข้ามขั้นตอนนี้", "INFO")
        return
    print_message("กำลังเริ่มดึงข้อมูลโค้ดล่าสุด...", "INFO")
    success, msg = ctx.git_service.fetch_latest_code()
    if success:
        print_message("ดึงข้อมูลโค้ดล่าสุดสำเร็จ", "PASS")
    else:
        print_message(f'การอัปเดตโค้ดล้มเหลว {msg}', "ERROR")

    check_dependencies(ctx) # ตรวจสอบ dependency หลังจากการดึงโค้ด


def check_dependencies(ctx: OneDragonEnvContext):
    """
    ติดตั้ง dependency ล่าสุด
    :return:
    """
    current = ctx.env_config.requirement_time
    latest = ctx.git_service.get_requirement_time()
    if current == latest:
        print_message("dependency ในการรันไม่มีการอัปเดต ข้ามขั้นตอนนี้", "INFO")
        return

    success, msg = ctx.python_service.install_requirements()
    if success:
        print_message("ติดตั้ง dependency ในการรันสำเร็จ", "PASS")
        ctx.env_config.requirement_time = latest
    else:
        print_message(f'การติดตั้ง dependency ในการรันล้มเหลว {msg}', "ERROR")


def run_python(app_path, no_windows: bool = True):
    # ฟังก์ชันหลักสำหรับรันสคริปต์ Python พร้อมการตั้งค่าสภาพแวดล้อม
    try:
        ctx = OneDragonEnvContext() # สร้าง context สำหรับสภาพแวดล้อม
        print_message(f"ไดเรกทอรีการทำงานปัจจุบัน: {path}", "INFO")
        verify_path_issues()
        configure_environment()
        log_folder = create_log_folder()
        clean_old_logs(log_folder) # ล้างเฉพาะ bat_*.log ไม่ใช่ python_*.log
        fetch_latest_code(ctx)
        execute_python_script(app_path, log_folder, no_windows)
    except SystemExit as e:
        print_message(f"โปรแกรมออกแล้ว รหัสสถานะ: {e.code}", "ERROR")
    except Exception as e:
        print_message(f"เกิดข้อยกเว้นที่ไม่ได้รับการจัดการ: {e}", "ERROR")
    finally:
        time.sleep(5) # ให้เวลาก่อนที่หน้าต่าง (ถ้ามี) จะปิด


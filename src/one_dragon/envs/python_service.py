import os.path
import time

import re
import shutil
import urllib.parse
from typing import Optional, Callable, Tuple

from one_dragon.envs.env_config import DEFAULT_ENV_PATH, DEFAULT_PYTHON_DIR_PATH, EnvConfig, \
    DEFAULT_VENV_DIR_PATH, DEFAULT_VENV_PYTHON_PATH, DEFAULT_PYTHON_PATH, PipSourceEnum
from one_dragon.envs.git_service import GitService
from one_dragon.envs.project_config import ProjectConfig
from one_dragon.utils import file_utils, cmd_utils, os_utils
from one_dragon.utils.log_utils import log


class PythonService:

    def __init__(self, project_config: ProjectConfig, env_config: EnvConfig, git_service: GitService):
        self.project_config = project_config
        self.env_config = env_config
        self.git_service: GitService = git_service

    def install_default_python(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> bool:
        """
        ติดตั้ง Python เริ่มต้น
        :param progress_callback: ฟังก์ชันเรียกกลับความคืบหน้า แจ้งผู้เรียกเมื่อความคืบหน้าเปลี่ยนแปลง
        :return: ติดตั้งสำเร็จหรือไม่
        """
        if self.get_python_version() == self.project_config.python_version:
            log.info('ได้ติดตั้ง Python เวอร์ชันที่แนะนำแล้ว')
            return True
        log.info('เริ่มติดตั้ง Python')
        for _ in range(2):
            zip_file_name = f'python-{self.project_config.python_version}-embed-amd64.zip'
            zip_file_path = os.path.join(DEFAULT_ENV_PATH, zip_file_name)
            if not os.path.exists(zip_file_path):
                success = self.git_service.download_env_file(zip_file_name, zip_file_path,
                                                             progress_callback=progress_callback)
                if not success:
                    return False  # ดาวน์โหลดล้มเหลว ส่งคืนค่า False ทันที ไม่ลองใหม่
            msg = f'เริ่มคลายการบีบอัด {zip_file_name}'
            log.info(msg)
            if progress_callback:
                progress_callback(-1, msg)
            success = file_utils.unzip_file(zip_file_path, DEFAULT_PYTHON_DIR_PATH)
            msg = 'คลายการบีบอัดสำเร็จ' if success else 'คลายการบีบอัดล้มเหลว เตรียมลองใหม่'
            log.info(msg)
            if progress_callback:
                progress_callback(1 if success else 0, msg)

            if not success:  # ถ้าคลายการบีบอัดล้มเหลว อาจเป็นเพราะไฟล์ zip ที่ดาวน์โหลดมาเสียหาย ลองลบแล้วเริ่มใหม่
                os.remove(zip_file_path)
                continue
            else:
                pth_path = os.path.join(DEFAULT_PYTHON_DIR_PATH, 'python311._pth')
                with open(pth_path, 'a') as file:
                    file.write('\nLib\\site-packages\n')
                return True

        # ยังคงล้มเหลวหลังจากลองใหม่
        return False

    def is_virtual_python(self) -> bool:
        """
        เป็น Python ในสภาพแวดล้อมเสมือนหรือไม่
        :return:
        """
        is_virtual_str = cmd_utils.run_command([self.env_config.python_path, "-c", "import sys; print(getattr(sys, 'base_prefix', sys.prefix) != sys.prefix)"])
        if is_virtual_str is None:
            return False
        else:
            return is_virtual_str == 'True'

    def install_default_pip(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> bool:
        """
        ติดตั้ง pip เริ่มต้น ต้องติดตั้ง Python ก่อน
        :param progress_callback: ฟังก์ชันเรียกกลับความคืบหน้า แจ้งผู้เรียกเมื่อความคืบหน้าเปลี่ยนแปลง
        :return: ติดตั้งสำเร็จหรือไม่
        """
        if self.get_pip_version() is not None:
            log.info('ได้ติดตั้ง pip แล้ว')
            return True
        log.info('เริ่มติดตั้ง pip')
        python_path = self.env_config.python_path
        for _ in range(2):
            py_file_name = 'get-pip.py'
            py_file_path = os.path.join(DEFAULT_ENV_PATH, py_file_name)
            if not os.path.exists(py_file_path):
                success = self.git_service.download_env_file(py_file_name, py_file_path,
                                                             progress_callback=progress_callback)
                if not success:  # ดาวน์โหลดล้มเหลว ส่งคืนค่า False ทันที ไม่ลองใหม่
                    return False

            if progress_callback:
                progress_callback(-1, 'กำลังติดตั้ง pip')
            self.choose_best_pip_source(progress_callback)
            result = cmd_utils.run_command([python_path, py_file_path, '--index-url', self.env_config.pip_source])
            success = result is not None
            msg = 'ติดตั้ง pip สำเร็จ' if success else 'ติดตั้ง pip ล้มเหลว เตรียมลองใหม่'
            log.info(msg)
            if progress_callback:
                progress_callback(1 if success else 0, msg)
            if not success:
                # ถ้าติดตั้งล้มเหลว อาจเป็นเพราะไฟล์ที่ดาวน์โหลดมาเสียหาย ลองลบแล้วเริ่มใหม่
                os.remove(py_file_path)
                continue
            else:
                return True

        # ยังคงล้มเหลวหลังจากลองใหม่
        return False

    def install_default_virtualenv(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> bool:
        """
        ติดตั้ง virtualenv เริ่มต้น ต้องติดตั้ง pip ก่อน
        :param progress_callback: ฟังก์ชันเรียกกลับความคืบหน้า แจ้งผู้เรียกเมื่อความคืบหน้าเปลี่ยนแปลง
        :return: ติดตั้งสำเร็จหรือไม่
        """
        if progress_callback:
            progress_callback(-1, 'กำลังติดตั้ง virtualenv')
        python_path = self.env_config.python_path
        result = cmd_utils.run_command([python_path, '-m', 'pip', 'install', 'virtualenv', '--index-url', self.env_config.pip_source, '--trusted-host', self.env_config.pip_trusted_host])
        success = result is not None
        msg = 'ติดตั้ง virtualenv สำเร็จ' if success else 'ติดตั้ง virtualenv ล้มเหลว'
        log.info(msg)
        if progress_callback:
            progress_callback(1 if success else 0, msg)
        return success

    def create_default_venv(self, progress_callback: Optional[Callable[[float, str], None]]):
        """
        สร้างสภาพแวดล้อมเสมือนเริ่มต้น
        :param progress_callback:
        :return:
        """
        if progress_callback:
            progress_callback(-1, 'กำลังเตรียมสร้างสภาพแวดล้อมเสมือน')
        python_path = self.env_config.python_path
        result = cmd_utils.run_command([python_path, '-m', 'virtualenv', DEFAULT_VENV_DIR_PATH, '--always-copy'])
        success = result is not None
        msg = 'สร้างสภาพแวดล้อมเสมือนสำเร็จ' if success else 'สร้างสภาพแวดล้อมเสมือนล้มเหลว'
        log.info(msg)
        if progress_callback:
            progress_callback(1 if success else 0, msg)
        return success

    def get_os_python_path(self) -> Optional[str]:
        """
        รับพาธ Python ในตัวแปรสภาพแวดล้อมของระบบปัจจุบัน
        :return:
        """
        log.info('กำลังรับพาธ Python ในตัวแปรสภาพแวดล้อมของระบบ')
        message = cmd_utils.run_command(['where', 'python'])
        if message is not None and message.endswith('.exe'):
            return message
        else:
            return None

    def get_python_version(self) -> Optional[str]:
        """
        :return: เวอร์ชัน Python ที่ใช้อยู่ในปัจจุบัน
        """
        log.info('กำลังตรวจสอบเวอร์ชัน Python ปัจจุบัน')
        python_path = self.env_config.python_path
        if python_path == '' or not os.path.exists(python_path):
            return None

        version = cmd_utils.run_command([python_path, '--version'])  # Ex: Python 3.11.9
        if version is not None:
            return version[7:]
        else:
            return None

    def get_os_pip_path(self) -> Optional[str]:
        """
        รับพาธ pip ในตัวแปรสภาพแวดล้อมของระบบปัจจุบัน
        :return:
        """
        log.info('กำลังรับพาธ pip ในตัวแปรสภาพแวดล้อมของระบบ')
        message = cmd_utils.run_command(['where', 'pip'])
        if message is not None and message.endswith('.exe'):
            return message
        else:
            return None

    def get_pip_version(self) -> Optional[str]:
        """
        :return: เวอร์ชัน pip ที่ใช้อยู่ในปัจจุบัน
        """
        log.info('กำลังตรวจสอบเวอร์ชัน pip ปัจจุบัน')
        python_path = self.env_config.python_path
        if python_path == '' or not os.path.exists(python_path):
            return None

        version = cmd_utils.run_command([python_path, '-m', 'pip', '--version'])  # Ex: pip 24.0 from xxxx
        if version is not None:
            return version[4: version.find('from') - 1]
        else:
            return None

    def install_default_python_venv(self, progress_callback: Optional[Callable[[float, str], None]]) -> Tuple[bool, str]:
        """
        กระบวนการติดตั้งสภาพแวดล้อม Python แบบครบวงจร
        :param progress_callback:
        :return:
        """
        if progress_callback is not None:
            progress_callback(-1, 'กำลังล้างไฟล์เก่า')
        self.env_config.python_path = ''
        if os.path.exists(DEFAULT_PYTHON_DIR_PATH):
            shutil.rmtree(DEFAULT_PYTHON_DIR_PATH)

        if os.path.exists(DEFAULT_VENV_DIR_PATH):
            shutil.rmtree(DEFAULT_VENV_DIR_PATH)

        if not self.install_default_python(progress_callback):
            return False, 'ติดตั้ง Python ล้มเหลว โปรดลองเปลี่ยนพร็อกซีเครือข่ายใน "สภาพแวดล้อมสคริปต์"'
        self.env_config.python_path = DEFAULT_PYTHON_PATH
        if not self.install_default_pip(progress_callback):
            return False, 'ติดตั้ง pip ล้มเหลว โปรดลองเปลี่ยนพร็อกซีเครือข่ายใน "สภาพแวดล้อมสคริปต์"'
        if not self.install_default_virtualenv(progress_callback):
            return False, 'ติดตั้ง virtualenv ล้มเหลว'
        if not self.create_default_venv(progress_callback):
            return False, 'สร้างสภาพแวดล้อมเสมือนล้มเหลว'
        self.env_config.python_path = DEFAULT_VENV_PYTHON_PATH

        return True, ''

    def install_requirements(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[bool, str]:
        """
        ติดตั้ง Dependencies
        :return:
        """
        if progress_callback is not None:
            progress_callback(-1, 'กำลังติดตั้ง... กระบวนการติดตั้งจะใช้เวลา 5-10 นาที โปรดรอสักครู่')

        # บางคนอาจติดตั้งล้มเหลวหากไม่อัปเกรด pip ไม่ทราบสาเหตุ
        result = cmd_utils.run_command([self.env_config.python_path, '-m', 'pip', 'install', '--upgrade', 'pip',
                                        '--index-url', self.env_config.pip_source, '--trusted-host', self.env_config.pip_trusted_host])
        success = result is not None
        msg = 'ติดตั้ง dependencies สำเร็จ' if success else 'ติดตั้ง dependencies ล้มเหลว'
        if not success:
            return success, msg

        result = cmd_utils.run_command([self.env_config.python_path, '-m', 'pip', 'install', '--upgrade',
                                        '-r', os.path.join(os_utils.get_work_dir(), self.project_config.requirements),
                                        '--index-url', self.env_config.pip_source, '--trusted-host', self.env_config.pip_trusted_host])
        success = result is not None
        msg = 'ติดตั้ง dependencies สำเร็จ' if success else 'ติดตั้ง dependencies ล้มเหลว'
        return success, msg

    def get_module_version(self) -> Optional[str]:
        """
        :return: เวอร์ชัน pip ที่ใช้อยู่ในปัจจุบัน (ชื่อฟังก์ชันอาจไม่ตรงกับสิ่งที่ทำจริงๆ - หมายเหตุผู้แปล)
        """
        log.info('กำลังตรวจสอบเวอร์ชัน pip ปัจจุบัน')
        python_path = self.env_config.python_path
        if python_path == '' or not os.path.exists(python_path):
            return None

        version = cmd_utils.run_command([python_path, '-m', 'pip', '--version'])  # Ex: pip 24.0 from xxxx
        if version is not None:
            return version[4: version.find('from') - 1]
        else:
            return None

    def choose_best_pip_source(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> None:
        """
        ทำการทดสอบความเร็วของแหล่ง pip และเลือกแหล่งที่ดีที่สุด
        :return:
        """
        display_log = 'เริ่มทดสอบความเร็วแหล่ง pip'
        log.info(display_log)
        if progress_callback is not None:
            progress_callback(-1, display_log)
        ping_result_list = []
        for source_enum in PipSourceEnum:
            source = source_enum.value
            source_url = source.value
            parsed_url = urllib.parse.urlparse(source_url)
            domain = parsed_url.netloc
            start_time = time.time()
            result = cmd_utils.run_command(['ping', '-n', '1', '-w', '1000', domain])
            end_time = time.time()
            if result is None:
                result = ''
            ms_match = re.search(r'(\d+)ms', result)
            if ms_match:
                ms = int(ms_match.group(1))
            else:
                ms = int(1000 * (end_time - start_time))

            display_log = f'{source.label} ใช้เวลา {ms}ms'
            log.info(display_log)
            if progress_callback is not None:
                progress_callback(-1, display_log)

            ping_result_list.append((source, ms))

        ping_result_list.sort(key=lambda x: x[1])

        best_source = ping_result_list[0][0]
        display_log = f'เลือกแหล่ง pip ที่ดีที่สุดคือ {best_source.label}'
        log.info(display_log)
        if progress_callback is not None:
            progress_callback(-1, display_log)
        self.env_config.pip_source = best_source.value

if __name__ == '__main__':
    python_service = PythonService(ProjectConfig, EnvConfig, GitService)
    python_service.choose_best_pip_source()
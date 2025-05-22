import time

import onnxruntime as ort
import os
import urllib.request
import zipfile
from typing import Optional, List

from one_dragon.yolo.log_utils import log

_GH_PROXY_URL = 'https://ghfast.top'


class OnnxModelLoader:

    def __init__(self,
                 model_name: str,
                 model_download_url: str,
                 model_parent_dir_path: str = os.path.abspath(__file__),  # ค่าเริ่มต้นจะใช้ไดเรกทอรีของไฟล์นี้
                 gh_proxy: bool = True,
                 gh_proxy_url: str = _GH_PROXY_URL,
                 personal_proxy: Optional[str] = '',
                 gpu: bool = False,
                 backup_model_name: Optional[str] = None,
                 ):
        self.model_name: str = model_name
        self.backup_model_name: str = backup_model_name  # โมเดลสำรอง โมเดลที่มีอยู่แล้วในเครื่อง ใช้เมื่อไม่สามารถดาวน์โหลดหรือใช้โมเดลใหม่ได้
        self.model_download_url: str = model_download_url  # URL ดาวน์โหลดโมเดล
        self.model_parent_dir_path: str = model_parent_dir_path
        self.model_dir_path = os.path.join(self.model_parent_dir_path, self.model_name)
        self.gh_proxy: bool = gh_proxy
        self.gh_proxy_url: str = gh_proxy_url
        self.personal_proxy: Optional[str] = personal_proxy
        self.gpu: bool = gpu  # ใช้ GPU acceleration หรือไม่

        # ข้อมูลอินพุตและเอาต์พุตที่อ่านจากโมเดล
        self.session: ort.InferenceSession = None
        self.input_names: List[str] = []
        self.onnx_input_width: int = 0
        self.onnx_input_height: int = 0
        self.output_names: List[str] = []

        if not self.check_and_download_model():  # โมเดลใหม่ไม่พร้อมใช้งาน
            log.error(f'โมเดล {self.model_name} ดาวน์โหลดไม่สำเร็จ โปรดลองเปลี่ยนพร็อกซีเพื่อดาวน์โหลด')
            log.info(f'กำลังลองใช้โมเดลสำรอง {self.backup_model_name}')
            self.model_name = self.backup_model_name
            self.model_dir_path = os.path.join(self.model_parent_dir_path, self.model_name)

        self.load_model()

    def check_and_download_model(self) -> bool:
        """
        ตรวจสอบว่าโมเดลถูกดาวน์โหลดเรียบร้อยแล้วหรือไม่ หากไดเรกทอรีไม่มีอยู่ หรือไฟล์ขาดหายไป จะทำการดาวน์โหลด
        :return: คืนค่าสถานะความสำเร็จของการตรวจสอบและดาวน์โหลดโมเดล
        """
        if not self.check_model_exists():
            download = self.download_model()
            if not download:
                return False
        return True

    def check_model_exists(self) -> bool:
        """
        ตรวจสอบว่าโมเดลถูกดาวน์โหลดเรียบร้อยแล้วหรือไม่ ที่นี่สามารถตรวจสอบได้เพียงว่าไฟล์ onnx มีอยู่หรือไม่ ไฟล์ประกอบอื่นๆ คลาสลูกจะต้องตรวจสอบด้วยตัวเอง
        :return: คืนค่า True หากโมเดลมีอยู่, False หากไม่มี
        """
        onnx_path = os.path.join(self.model_dir_path, 'model.onnx')

        return os.path.exists(self.model_dir_path) and os.path.exists(onnx_path)

    def download_model(self) -> bool:
        """
        ดาวน์โหลดโมเดล
        :return: ดาวน์โหลดโมเดลสำเร็จหรือไม่
        """
        if not os.path.exists(self.model_dir_path):
            os.mkdir(self.model_dir_path)

        download_url = f'{self.model_download_url}/{self.model_name}.zip'
        if self.personal_proxy is not None and len(self.personal_proxy) > 0:
            os.environ['http_proxy'] = self.personal_proxy
            os.environ['https_proxy'] = self.personal_proxy
        elif self.gh_proxy:
            download_url = f'{self.gh_proxy_url}/{self.model_download_url}/{self.model_name}.zip'
        log.info('เริ่มดาวน์โหลด %s %s', self.model_name, download_url)
        zip_file_path = os.path.join(self.model_dir_path, f'{self.model_name}.zip')
        last_log_time = time.time()

        def log_download_progress(block_num, block_size, total_size):
            nonlocal last_log_time
            if time.time() - last_log_time < 1:
                return
            last_log_time = time.time()
            downloaded = block_num * block_size / 1024.0 / 1024.0
            total_size_mb = total_size / 1024.0 / 1024.0
            progress = downloaded / total_size_mb * 100
            log.info(f"กำลังดาวน์โหลด {self.model_name}: {downloaded:.2f}/{total_size_mb:.2f} MB ({progress:.2f}%)")

        try:
            _, _ = urllib.request.urlretrieve(download_url, zip_file_path, log_download_progress)
            log.info('ดาวน์โหลดเสร็จสิ้น %s', self.model_name)
            self.unzip_model(zip_file_path)
            return True
        except Exception:
            log.error('ดาวน์โหลดโมเดลล้มเหลว', exc_info=True)
            return False

    def unzip_model(self, zip_file_path: str):
        """
        คลายการบีบอัดไฟล์
        :param zip_file_path: พาธของไฟล์ที่บีบอัด
        :return:
        """
        log.info('เริ่มคลายการบีบอัดไฟล์ %s', zip_file_path)

        if not os.path.exists(self.model_dir_path):
            os.mkdir(self.model_dir_path)

        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(self.model_dir_path)

        log.info('คลายการบีบอัดเสร็จสิ้น %s', zip_file_path)

    def load_model(self) -> None:
        """
        โหลดโมเดล
        :return:
        """
        availables = ort.get_available_providers()
        providers = ['DmlExecutionProvider' if self.gpu else 'CPUExecutionProvider']
        if self.gpu and 'DmlExecutionProvider' not in availables:
            log.error('เครื่องไม่รองรับ DirectML จะใช้ CPU แทน')
            providers = ['CPUExecutionProvider']

        onnx_path = os.path.join(self.model_dir_path, 'model.onnx')
        log.info('กำลังโหลดโมเดล %s', onnx_path)
        self.session = ort.InferenceSession(
            onnx_path,
            providers=providers
        )
        self.get_input_details()
        self.get_output_details()

    def get_input_details(self):
        model_inputs = self.session.get_inputs()
        self.input_names = [model_inputs[i].name for i in range(len(model_inputs))]

        shape = model_inputs[0].shape
        self.onnx_input_height = shape[2]
        self.onnx_input_width = shape[3]

    def get_output_details(self):
        model_outputs = self.session.get_outputs()
        self.output_names = [model_outputs[i].name for i in range(len(model_outputs))]
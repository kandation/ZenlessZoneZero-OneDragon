import time

import numpy as np
from cv2.typing import MatLike
from typing import Optional, List

from one_dragon.yolo import onnx_utils
from one_dragon.yolo.onnx_model_loader import OnnxModelLoader


class RunContext:

    def __init__(self, raw_image: MatLike, run_time: Optional[float] = None):
        """
        บริบทของกระบวนการอนุมาน
        ใช้สำหรับบันทึกตัวแปรชั่วคราว
        """
        self.run_time: float = time.time() if run_time is None else run_time
        """เวลาที่ใช้ในการระบุ"""

        self.img: MatLike = raw_image
        """รูปภาพที่ใช้สำหรับการทำนาย"""

        self.img_height: int = raw_image.shape[0]
        """ความสูงของรูปภาพต้นฉบับ"""

        self.img_width: int = raw_image.shape[1]
        """ความกว้างของรูปภาพต้นฉบับ"""

        self.conf: float = 0.9
        """ค่าเกณฑ์ความเชื่อมั่นที่ใช้ในการตรวจจับ"""

        self.scale_height: int = 0
        """ความสูงหลังจากการปรับขนาด"""

        self.scale_width: int = 0
        """ความกว้างหลังจากการปรับขนาด"""


class ClassificationResult:

    def __init__(self,
                 raw_image: MatLike,
                 class_idx: int,
                 run_time: Optional[float] = None,):
        self.run_time: float = time.time() if run_time is None else run_time  # เวลาที่ใช้ในการระบุ
        self.raw_image: MatLike = raw_image  # รูปภาพต้นฉบับที่ใช้ในการระบุ
        self.class_idx: int = class_idx  # ดัชนีการจัดหมวดหมู่ -1 หมายถึงไม่สามารถระบุได้ (ไม่ถึงเกณฑ์)


class Yolov8Classifier(OnnxModelLoader):

    def __init__(self,
                 model_name: str,
                 model_parent_dir_path: str,  # ค่าเริ่มต้นจะใช้ไดเรกทอรีของไฟล์นี้
                 model_download_url: str,
                 gh_proxy: bool = True,
                 gh_proxy_url: Optional[str] = None,
                 personal_proxy: Optional[str] = None,
                 gpu: bool = False,
                 backup_model_name: Optional[str] = None,
                 keep_result_seconds: float = 2,
                 ):
        """
        :param model_name: ชื่อโมเดล จะมีโฟลเดอร์ย่อยที่สร้างขึ้นตามชื่อโมเดลในไดเรกทอรีราก
        :param model_parent_dir_path: ไดเรกทอรีรากสำหรับจัดเก็บโมเดลทั้งหมด
        :param gpu: เปิดใช้งานการเร่งความเร็ว GPU หรือไม่
        :param keep_result_seconds: ระยะเวลาที่จะเก็บผลลัพธ์การระบุ
        """
        OnnxModelLoader.__init__(
            self,
            model_name=model_name,
            model_download_url=model_download_url,
            model_parent_dir_path=model_parent_dir_path,
            gh_proxy=gh_proxy,
            gh_proxy_url=gh_proxy_url,
            personal_proxy=personal_proxy,
            gpu=gpu,
            backup_model_name=backup_model_name
        )

        self.keep_result_seconds: float = keep_result_seconds  # จำนวนวินาทีที่เก็บผลลัพธ์การระบุ
        self.run_result_history: List[ClassificationResult] = []  # ผลลัพธ์การระบุในอดีต

    def run(self, image: MatLike, conf: float = 0.9, run_time: Optional[float] = None) -> ClassificationResult:
        """
        ทำการระบุรูปภาพ
        :param image: รูปภาพที่อ่านโดย opencv ช่อง RGB
        :param conf: เกณฑ์ความเชื่อมั่น
        :return: ผลลัพธ์การระบุ
        """
        t1 = time.time()
        context = RunContext(image, run_time)
        context.conf = conf

        input_tensor = self.prepare_input(context)
        t2 = time.time()

        outputs = self.inference(input_tensor)
        t3 = time.time()

        result = self.process_output(outputs, context)
        t4 = time.time()

        # log.info(f'ระบุเสร็จสิ้น ใช้เวลาประมวลผลล่วงหน้า {t2 - t1:.3f}s, เวลาอนุมาน {t3 - t2:.3f}s, เวลาประมวลผลหลัง {t4 - t3:.3f}s')

        self.record_result(context, result)
        return result

    def prepare_input(self, context: RunContext) -> np.ndarray:
        """
        การประมวลผลล่วงหน้าก่อนการอนุมาน
        """
        input_tensor, scale_height, scale_width = onnx_utils.scale_input_image_u(context.img, self.onnx_input_width, self.onnx_input_height)
        context.scale_height = scale_height
        context.scale_width = scale_width
        return input_tensor

    def inference(self, input_tensor: np.ndarray):
        """
        ป้อนรูปภาพเข้าสู่โมเดลเพื่อทำการอนุมาน
        :param input_tensor: รูปภาพที่ป้อนเข้าโมเดล ช่อง RGB
        :return: ผลลัพธ์ที่ได้จากการอนุมานโมเดล onnx
        """
        outputs = self.session.run(self.output_names, {self.input_names[0]: input_tensor})
        return outputs

    def process_output(self, output, context: RunContext) -> ClassificationResult:
        """
        :param output: ผลลัพธ์การอนุมาน
        :param context: บริบท
        :return: ผลลัพธ์การระบุที่ได้สุดท้าย
        """
        scores = np.squeeze(output[0]).T
        idx = np.argmax(scores)
        conf = scores[idx]
        result = ClassificationResult(
            raw_image=context.img,
            run_time=context.run_time,
            class_idx=idx if conf >= context.conf else -1
        )
        return result

    def record_result(self, context: RunContext, result: ClassificationResult) -> None:
        """
        บันทึกผลลัพธ์การระบุของเฟรมปัจจุบัน
        :param context: บริบทการระบุ
        :param result: ผลลัพธ์การระบุ
        :return: ผลลัพธ์รวม
        """
        self.run_result_history.append(result)
        self.run_result_history = [i for i in self.run_result_history
                                   if context.run_time - i.run_time > self.keep_result_seconds]

    @property
    def last_run_result(self) -> Optional[ClassificationResult]:
        if len(self.run_result_history) > 0:
            return self.run_result_history[len(self.run_result_history) - 1]
        else:
            return None
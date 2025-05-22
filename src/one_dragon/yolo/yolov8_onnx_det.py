import time

import csv
import numpy as np
import os
from cv2.typing import MatLike
from typing import Optional, List

from one_dragon.yolo import onnx_utils
from one_dragon.yolo.detect_utils import DetectFrameResult, DetectClass, DetectContext, DetectObjectResult, xywh2xyxy, \
    multiclass_nms
from one_dragon.yolo.onnx_model_loader import OnnxModelLoader


class Yolov8Detector(OnnxModelLoader):

    def __init__(self,
                 model_name: str,
                 model_parent_dir_path: str,
                 model_download_url: str,
                 gh_proxy: bool = True,
                 gh_proxy_url: Optional[str] = None,
                 personal_proxy: Optional[str] = None,
                 gpu: bool = False,
                 backup_model_name: Optional[str] = None,
                 keep_result_seconds: float = 2
                 ):
        """
        yolov8 detect ที่ส่งออกเป็น onnx แล้วนำมาใช้
        อ้างอิงจาก https://github.com/ibaiGorordo/ONNX-YOLOv8-Object-Detection
        :param model_name: ชื่อโมเดล จะมีโฟลเดอร์ย่อยที่สร้างขึ้นตามชื่อโมเดลในไดเรกทอรีราก
        :param backup_model_name: ชื่อโมเดลสำรอง โดยปกติจะเป็นโมเดลเวอร์ชันก่อนหน้า ใช้เป็นโมเดลสำรองเมื่อไม่สามารถดาวน์โหลดโมเดลเวอร์ชันใหม่ได้
        :param model_parent_dir_path: ไดเรกทอรีรากสำหรับจัดเก็บโมเดลทั้งหมด
        :param gpu: เปิดใช้งานการคำนวณด้วย GPU หรือไม่
        :param keep_result_seconds: ระยะเวลาที่จะเก็บผลลัพธ์การระบุ
        """
        OnnxModelLoader.__init__(
            self,
            model_name=model_name,
            model_parent_dir_path=model_parent_dir_path,
            model_download_url=model_download_url,
            gh_proxy=gh_proxy,
            gh_proxy_url=gh_proxy_url,
            personal_proxy=personal_proxy,
            gpu=gpu,
            backup_model_name=backup_model_name
        )

        self.keep_result_seconds: float = keep_result_seconds  # จำนวนวินาทีที่เก็บผลลัพธ์การระบุ
        self.run_result_history: List[DetectFrameResult] = []  # ผลลัพธ์การระบุในอดีต

        self.idx_2_class: dict[int, DetectClass] = {}  # การจัดหมวดหมู่
        self.class_2_idx: dict[str, int] = {}
        self.category_2_idx: dict[str, List[int]] = {}
        self._load_detect_classes(self.model_dir_path)

    def run(self, image: MatLike, conf: float = 0.6, iou: float = 0.5, run_time: Optional[float] = None,
            label_list: Optional[List[str]] = None,
            category_list: Optional[List[str]] = None) -> DetectFrameResult:
        """
        ทำการระบุรูปภาพ
        :param image: รูปภาพที่อ่านโดย opencv ช่อง RGB
        :param conf: เกณฑ์ความเชื่อมั่น
        :param iou: เกณฑ์ IOU
        :return: ผลลัพธ์การระบุ
        """
        t1 = time.time()
        context = DetectContext(image, run_time)
        context.conf = conf
        context.iou = iou
        context.label_list = label_list
        context.category_list = category_list

        input_tensor = self.prepare_input(context)
        t2 = time.time()

        outputs = self.inference(input_tensor)
        t3 = time.time()

        results = self.process_output(outputs, context)
        t4 = time.time()

        # log.info(f'ระบุเสร็จสิ้น ได้ผลลัพธ์ {len(results)} รายการ ใช้เวลาประมวลผลล่วงหน้า {t2 - t1:.3f}s, เวลาอนุมาน {t3 - t2:.3f}s, เวลาประมวลผลหลัง {t4 - t3:.3f}s')

        return self.record_result(context, results)

    def prepare_input(self, context: DetectContext) -> np.ndarray:
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

    def process_output(self, output, context: DetectContext) -> List[DetectObjectResult]:
        """
        :param output: ผลลัพธ์การอนุมาน
        :param context: บริบท
        :return: ผลลัพธ์การระบุที่ได้สุดท้าย
        """
        predictions = np.squeeze(output[0]).T

        keep = np.ones(shape=(predictions.shape[1]), dtype=bool)

        if context.label_list is not None or context.category_list is not None:
            keep[4:] = False  # 4 ตำแหน่งแรกคือพิกัด ตั้งค่าแท็กทั้งหมดเป็น False ก่อน
            if context.label_list is not None:
                for label in context.label_list:
                    idx = self.class_2_idx.get(label)
                    if idx is not None:
                        keep[idx + 4] = True

            if context.category_list is not None:
                for category in context.category_list:
                    for idx in self.category_2_idx.get(category, []):
                        keep[idx + 4] = True

        predictions[:, keep == False] = 0

        # กรองเบื้องต้นตามเกณฑ์ความเชื่อมั่น
        scores = np.max(predictions[:, 4:], axis=1)
        predictions = predictions[scores > context.conf, :]
        scores = scores[scores > context.conf]

        results: List[DetectObjectResult] = []
        if len(scores) == 0:
            return results

        # เลือกคลาสที่มีความเชื่อมั่นสูงสุด
        class_ids = np.argmax(predictions[:, 4:], axis=1)

        # ดึง Bounding box
        boxes = predictions[:, :4]  # ผลลัพธ์การอนุมานดั้งเดิม xywh
        scale_shape = np.array([context.scale_width, context.scale_height, context.scale_width, context.scale_height])  # ขนาดรูปภาพหลังจากการปรับขนาด
        boxes = np.divide(boxes, scale_shape, dtype=np.float32)  # แปลงเป็น 0~1
        boxes *= np.array([context.img_width, context.img_height, context.img_width, context.img_height])  # คืนค่าพิกัดไปยังรูปภาพต้นฉบับ
        boxes = xywh2xyxy(boxes)  # แปลงเป็น xyxy

        # ทำ NMS เพื่อให้ได้ผลลัพธ์สุดท้าย
        indices = multiclass_nms(boxes, scores, class_ids, context.iou)

        for idx in indices:
            result = DetectObjectResult(rect=boxes[idx].tolist(),
                                        score=float(scores[idx]),
                                        detect_class=self.idx_2_class[int(class_ids[idx])]
                                        )
            results.append(result)

        return results

    def record_result(self, context: DetectContext, results: List[DetectObjectResult]) -> DetectFrameResult:
        """
        บันทึกผลลัพธ์การระบุของเฟรมปัจจุบัน
        :param context: บริบทการระบุ
        :param results: ผลลัพธ์การระบุ
        :return: ผลลัพธ์รวม
        """
        new_frame = DetectFrameResult(
            raw_image=context.img,
            results=results,
            run_time=context.run_time
        )
        self.run_result_history.append(new_frame)
        self.run_result_history = [i for i in self.run_result_history
                                   if context.run_time - i.run_time <= self.keep_result_seconds]

        return new_frame

    @property
    def last_run_result(self) -> Optional[DetectFrameResult]:
        if len(self.run_result_history) > 0:
            return self.run_result_history[len(self.run_result_history) - 1]
        else:
            return None

    def _load_detect_classes(self, model_dir_path: str):
        """
        โหลดการจัดหมวดหมู่
        :param model_dir_path: model_dir_path: str
        :return:
        """
        csv_path = os.path.join(model_dir_path, 'labels.csv')
        with open(csv_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if row[0] == 'idx':
                    continue
                c = DetectClass(int(row[0]), row[1], category=None if len(row) < 3 else row[2])
                self.idx_2_class[c.class_id] = c
                self.class_2_idx[c.class_name] = c.class_id

                if c.class_category not in self.category_2_idx:
                    self.category_2_idx[c.class_category] = []
                self.category_2_idx[c.class_category].append(c.class_id)
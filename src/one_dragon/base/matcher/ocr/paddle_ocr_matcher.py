import time

import logging
import os
from cv2.typing import MatLike

from one_dragon.base.matcher.match_result import MatchResult, MatchResultList
from one_dragon.base.matcher.ocr import ocr_utils
from one_dragon.base.matcher.ocr.ocr_matcher import OcrMatcher
from one_dragon.utils import os_utils
from one_dragon.utils.log_utils import log


class PaddleOcrMatcher(OcrMatcher):
    """
    https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/doc/doc_ch/quickstart.md
    ocr.ocr(img) คืนค่าเป็น list, ตัวอย่างเช่น:
    [
        [ [[894.0, 252.0], [1024.0, 252.0], [1024.0, 288.0], [894.0, 288.0]], ('快速恢复', 0.9989572763442993)],
        [ [[450.0, 494.0], [560.0, 494.0], [560.0, 530.0], [450.0, 530.0]], ('奇巧零食', 0.9995825290679932)]
    ]
    พิกัดของ anchor box ที่คืนค่าคือ [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
    ไม่สามารถใช้พร้อมกันได้ จะมีปัญหาเรื่อง thread safety
    หลังจาก enable_mkldnn=True แล้วกลับช้าลง ไม่ทราบสาเหตุ
    ควรหลีกเลี่ยงการส่งรูปภาพที่มีจุดดำหรือเส้นแนวนอนที่ไม่ชัดเจน ซึ่งอาจถูกระบุว่าเป็นเครื่องหมายวรรคตอน
    ทดสอบการใช้ส่วนการรู้จำพร โดยการส่งรูปภาพขาวดำไม่ได้ช่วยให้เร็วขึ้น การดึงสีที่ไม่ดีอาจทำให้ความแม่นยำในการรู้จำลดลง
    """

    def __init__(self):
        OcrMatcher.__init__(self)
        self.ocr = None

    def init_model(self) -> bool:
        log.info('กำลังโหลดโมเดล OCR')

        if self.ocr is None:
            from paddleocr import PaddleOCR
            logging.getLogger().handlers.clear()  # ไม่ทราบว่าทำไมถึงมีการนำเข้า logger นี้เข้ามา ล้างออกเพื่อหลีกเลี่ยงการบันทึกซ้ำในคอนโซล
            models_dir = os_utils.get_path_under_work_dir('assets', 'models', 'ocr')

            try:
                self.ocr = PaddleOCR(
                    use_angle_cls=False, use_gpu=False, drop_score=0.5,
                    det_model_dir=os.path.join(models_dir, 'ch_PP-OCRv4_det_infer'),
                    rec_model_dir=os.path.join(models_dir, 'ch_PP-OCRv4_rec_infer'),
                    cls_model_dir=os.path.join(models_dir, 'ch_ppocr_mobile_v2.0_cls_slim_infer')
                )
                return True
            except Exception:
                log.error('เกิดข้อผิดพลาดในการโหลดโมเดล OCR', exc_info=True)
                return False

        return True

    def run_ocr_single_line(self, image: MatLike, threshold: float = None, strict_one_line: bool = True) -> str:
        """
        การรู้จำข้อความบรรทัดเดียว โดยการรวมเป็นบรรทัดเดียวด้วยตนเอง ตามผลการจับคู่จากซ้ายไปขวา จากบนลงล่าง
        ในทางทฤษฎีภาษาจีนจะไม่เกิดการแบ่งบรรทัดที่ยาวเกินไป ที่นี่เพียงเพื่อรองรับกรณีภาษาอังกฤษ
        :param image: รูปภาพ
        :param threshold: ค่าเกณฑ์
        :param strict_one_line: True หากมีข้อความเพียงบรรทัดเดียว False หากโปรแกรมต้องรวมเป็นบรรทัดเดียว
        :return:
        """
        if strict_one_line:
            return self._run_ocr_without_det(image, threshold)
        else:
            ocr_map: dict = self.run_ocr(image, threshold)
            tmp = ocr_utils.merge_ocr_result_to_single_line(ocr_map, join_space=False)
            return tmp

    def run_ocr(self, image: MatLike, threshold: float = None,
                merge_line_distance: float = -1) -> dict[str, MatchResultList]:
        """
        ทำการ OCR บนรูปภาพ และคืนค่าผลลัพธ์การจับคู่ทั้งหมด
        :param image: รูปภาพ
        :param threshold: ค่าเกณฑ์การจับคู่
        :param merge_line_distance: ระยะห่างระหว่างบรรทัดที่จะรวมผลลัพธ์ -1 คือไม่รวม ในทางทฤษฎีภาษาจีนจะไม่เกิดการแบ่งบรรทัดที่ยาวเกินไป ที่นี่เพียงเพื่อรองรับกรณีภาษาอังกฤษ
        :return: {key_word: []}
        """
        start_time = time.time()
        result_map: dict = {}
        scan_result_list: list = self.ocr.ocr(image, cls=False)
        if len(scan_result_list) == 0:
            log.debug('ผลลัพธ์ OCR %s ใช้เวลา %.2f', result_map.keys(), time.time() - start_time)
            return result_map

        scan_result = scan_result_list[0]
        for anchor in scan_result:
            anchor_position = anchor[0]
            anchor_text = anchor[1][0]
            anchor_score = anchor[1][1]
            if threshold is not None and anchor_score < threshold:
                continue
            if anchor_text not in result_map:
                result_map[anchor_text] = MatchResultList(only_best=False)
            result_map[anchor_text].append(MatchResult(anchor_score,
                                                       anchor_position[0][0],
                                                       anchor_position[0][1],
                                                       anchor_position[1][0] - anchor_position[0][0],
                                                       anchor_position[3][1] - anchor_position[0][1],
                                                       data=anchor_text))

        if merge_line_distance != -1:
            result_map = ocr_utils.merge_ocr_result_to_multiple_line(result_map, join_space=True,
                                                                     merge_line_distance=merge_line_distance)
        log.debug('ผลลัพธ์ OCR %s ใช้เวลา %.2f', result_map.keys(), time.time() - start_time)
        return result_map

    def _run_ocr_without_det(self, image: MatLike, threshold: float = None) -> str:
        """
        ไม่ใช้โมเดลตรวจจับเพื่อวิเคราะห์การกระจายตัวของข้อความในรูปภาพ
        โดยค่าเริ่มต้น รูปภาพที่ป้อนเข้ามาจะมีเพียงข้อมูลข้อความเท่านั้น
        :param image: รูปภาพ
        :param threshold: ค่าเกณฑ์การจับคู่
        :return: [[("text", "score"),]] เนื่องจากปิดใช้งานช่องว่าง จึงสามารถนำองค์ประกอบแรกมาใช้ได้โดยตรง
        """
        start_time = time.time()
        scan_result: list = self.ocr.ocr(image, det=False, cls=False)
        img_result = scan_result[0]  # นำรูปภาพแรก
        if len(img_result) > 1:
            log.debug("โมเดล OCR ที่ปิดใช้งานการตรวจจับคืนค่าผลลัพธ์การรู้จำหลายรายการ")  # ปัจจุบันยังไม่เคยเกิดกรณีนี้

        if threshold is not None and scan_result[0][1] < threshold:
            log.debug("ความเชื่อมั่นของผลลัพธ์การรู้จำที่โมเดล OCR คืนค่าต่ำกว่าเกณฑ์")
            return ""
        log.debug('ผลลัพธ์ OCR %s ใช้เวลา %.2f', scan_result, time.time() - start_time)
        return img_result[0][0]
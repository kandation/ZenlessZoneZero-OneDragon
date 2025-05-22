import time

import os
from cv2.typing import MatLike
from typing import List

from one_dragon.base.matcher.match_result import MatchResult, MatchResultList
from one_dragon.base.matcher.ocr import ocr_utils
from one_dragon.base.matcher.ocr.ocr_matcher import OcrMatcher
from one_dragon.utils import os_utils
from one_dragon.utils import str_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log


class OnnxOcrMatcher(OcrMatcher):
    """
    ใช้โมเดล OCR ของ onnx ซึ่งเร็วกว่า
    TODO ยังไม่ได้ทดสอบว่ามีผลกระทบกับการใช้รูปภาพ RGB หรือไม่
    """

    def __init__(self):
        OcrMatcher.__init__(self)
        self._model = None
        self._loading: bool = False

    def init_model(self) -> bool:
        log.info('กำลังโหลดโมเดล OCR')
        while self._loading:
            time.sleep(1)
            return True
        self._loading = True

        if self._model is None:
            from onnxocr.onnx_paddleocr import ONNXPaddleOcr
            models_dir = os_utils.get_path_under_work_dir('assets', 'models', 'onnx_ocr')

            try:
                self._model = ONNXPaddleOcr(
                    use_angle_cls=False, use_gpu=False,
                    det_model_dir=os.path.join(models_dir, 'det.onnx'),
                    rec_model_dir=os.path.join(models_dir, 'rec.onnx'),
                    cls_model_dir=os.path.join(models_dir, 'cls.onnx'),
                    rec_char_dict_path=os.path.join(models_dir, 'ppocr_keys_v1.txt'),
                    vis_font_path=os.path.join(models_dir, 'simfang.tt'),
                )
                self._loading = False
                log.info('โหลดโมเดล OCR เสร็จสิ้น')
                return True
            except Exception:
                log.error('เกิดข้อผิดพลาดในการโหลดโมเดล OCR', exc_info=True)
                self._loading = False
                return False

        log.info('โหลดโมเดล OCR เสร็จสิ้น')
        self._loading = False
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
        scan_result_list: list = self._model.ocr(image, cls=False)
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
        scan_result: list = self._model.ocr(image, det=False, cls=False)
        img_result = scan_result[0]  # นำรูปภาพแรก
        if len(img_result) > 1:
            log.debug("โมเดล OCR ที่ปิดใช้งานการตรวจจับคืนค่าผลลัพธ์การรู้จำหลายรายการ")  # ปัจจุบันยังไม่เคยเกิดกรณีนี้

        if threshold is not None and scan_result[0][1] < threshold:
            log.debug("ความเชื่อมั่นของผลลัพธ์การรู้จำที่โมเดล OCR คืนค่าต่ำกว่าเกณฑ์")
            return ""
        log.debug('ผลลัพธ์ OCR %s ใช้เวลา %.2f', scan_result, time.time() - start_time)
        return img_result[0][0]

    def match_words(self, image: MatLike, words: List[str], threshold: float = None,
                    same_word: bool = False,
                    ignore_case: bool = True, lcs_percent: float = -1, merge_line_distance: float = -1) -> dict[
        str, MatchResultList]:
        """
        ค้นหาคำหลักในรูปภาพ และคืนค่าตำแหน่งที่สอดคล้องกับคำเหล่านั้นทั้งหมด
        :param image: รูปภาพ
        :param words: คำหลัก
        :param threshold: ค่าเกณฑ์การจับคู่
        :param same_word: ต้องการให้คำทั้งหมดเหมือนกัน
        :param ignore_case: ไม่สนใจตัวพิมพ์เล็ก/ใหญ่
        :param lcs_percent: เปอร์เซ็นต์ความยาวของลำดับย่อยร่วมที่ยาวที่สุด -1 หมายถึงไม่ใช้ ไม่ทำงานเมื่อ same_word=True
        :param merge_line_distance: ระยะห่างระหว่างบรรทัดที่จะรวมผลลัพธ์ -1 คือไม่รวม
        :return: {key_word: []}
        """
        all_match_result: dict = self.run_ocr(image, threshold, merge_line_distance=merge_line_distance)
        match_key = set()
        for k in all_match_result.keys():
            for w in words:
                ocr_result: str = k
                ocr_target = gt(w, 'ocr')
                if ignore_case:
                    ocr_result = ocr_result.lower()
                    ocr_target = ocr_target.lower()

                if same_word:
                    if ocr_result == ocr_target:
                        match_key.add(k)
                else:
                    if lcs_percent == -1:
                        if ocr_result.find(ocr_target) != -1:
                            match_key.add(k)
                    else:
                        if str_utils.find_by_lcs(ocr_target, ocr_result, percent=lcs_percent):
                            match_key.add(k)

        return {key: all_match_result[key] for key in match_key if key in all_match_result}
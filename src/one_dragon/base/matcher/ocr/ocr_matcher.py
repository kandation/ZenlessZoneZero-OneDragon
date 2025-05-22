from cv2.typing import MatLike

from one_dragon.base.matcher.match_result import MatchResultList


class OcrMatcher:

    def __init__(self):
        pass

    def init_model(self) -> bool:
        pass

    def run_ocr_single_line(self, image: MatLike, threshold: float = None, strict_one_line: bool = True) -> str:
        """
        การรู้จำข้อความบรรทัดเดียว โดยการรวมเป็นบรรทัดเดียวด้วยตนเอง ตามผลการจับคู่จากซ้ายไปขวา จากบนลงล่าง
        ในทางทฤษฎีภาษาจีนจะไม่เกิดการแบ่งบรรทัดที่ยาวเกินไป ที่นี่เพียงเพื่อรองรับกรณีภาษาอังกฤษ
        :param image: รูปภาพ
        :param threshold: ค่าเกณฑ์
        :param strict_one_line: True หากมีข้อความเพียงบรรทัดเดียว False หากโปรแกรมต้องรวมเป็นบรรทัดเดียว
        :return:
        """
        pass

    def run_ocr(self, image: MatLike, threshold: float = None,
                merge_line_distance: float = -1) -> dict[str, MatchResultList]:
        """
        ทำการ OCR บนรูปภาพ และคืนค่าผลลัพธ์การจับคู่ทั้งหมด
        :param image: รูปภาพ
        :param threshold: ค่าเกณฑ์การจับคู่
        :param merge_line_distance: ระยะห่างระหว่างบรรทัดที่จะรวมผลลัพธ์ -1 คือไม่รวม ในทางทฤษฎีภาษาจีนจะไม่เกิดการแบ่งบรรทัดที่ยาวเกินไป ที่นี่เพียงเพื่อรองรับกรณีภาษาอังกฤษ
        :return: {key_word: []}
        """
        pass
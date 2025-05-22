from typing import List, Optional, Any

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect


class MatchResult:

    def __init__(self, c, x, y, w, h, template_scale: float = 1, data: Any = None):
        """
        ผลลัพธ์การรู้จำ ใช้สำหรับ cv2 และ ocr
        """
        self.confidence: float = float(c)
        self.x: int = int(x)
        self.y: int = int(y)
        self.w: int = int(w)
        self.h: int = int(h)
        self.template_scale: float = template_scale
        self.data: Any = data

    def __repr__(self):
        return '(%.2f, %d, %d, %d, %d, %.2f)' % (self.confidence, self.x, self.y, self.w, self.h, self.template_scale)

    @property
    def left_top(self) -> Point:
        return Point(self.x, self.y)

    @property
    def center(self) -> Point:
        return Point(self.x + self.w // 2, self.y + self.h // 2)

    @property
    def right_bottom(self) -> Point:
        return Point(self.x + self.w, self.y + self.h)

    @property
    def rect(self) -> Rect:
        return Rect(self.x, self.y, self.x + self.w, self.y + self.h)

    def add_offset(self, p: Point):
        self.x += p.x
        self.y += p.y


class MatchResultList:
    def __init__(self, only_best: bool = True):
        """
        การรวมผลลัพธ์การรู้จำหลายรายการ เหมาะสำหรับรูปภาพที่มีเป้าหมายหลายรายการ
        """
        self.only_best: bool = only_best
        self.arr: List[MatchResult] = []
        self.max: Optional[MatchResult] = None

    def __repr__(self):
        return '[%s]' % ', '.join(str(i) for i in self.arr)

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index < len(self.arr):
            value = self.arr[self.index]
            self.index += 1
            return value
        else:
            raise StopIteration

    def __len__(self):
        return len(self.arr)

    def append(self, a: MatchResult, auto_merge: bool = True, merge_distance: float = 10):
        """
        เพิ่มผลลัพธ์การจับคู่ หากเปิดใช้งานการรวม จะเก็บผลลัพธ์ที่มีความเชื่อมั่นสูงกว่า
        :param a: โครงสร้างที่ต้องการเพิ่ม
        :param auto_merge: รวมกับผลลัพธ์ก่อนหน้าโดยอัตโนมัติหรือไม่
        :param merge_distance: ระยะห่างที่จะรวม
        :return:
        """
        if self.only_best:
            if self.max is None:
                self.max = a
                self.arr.append(a)
            elif a.confidence > self.max.confidence:
                self.max = a
                self.arr[0] = a
        else:
            if auto_merge:
                for i in self.arr:
                    if (i.x - a.x) ** 2 + (i.y - a.y) ** 2 <= merge_distance ** 2:
                        if a.confidence > i.confidence:
                            i.x = a.x
                            i.y = a.y
                            i.confidence = a.confidence
                        return

            self.arr.append(a)
            if self.max is None or a.confidence > self.max.confidence:
                self.max = a

    def __getitem__(self, item):
        return self.arr[item]

    def add_offset(self, lt: Point) -> None:
        """
        เพิ่มการชดเชยที่มุมซ้ายบนให้กับผลลัพธ์ทั้งหมด
        ใช้หลังจากตัดพื้นที่
        """
        for mr in self.arr:
            mr.add_offset(lt)
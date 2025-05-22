from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Optional, Callable
from io import BytesIO

from one_dragon.base.notify.push import Push
from one_dragon.base.operation.application_run_record import AppRunRecord
from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.base.operation.operation import Operation
from one_dragon.base.operation.operation_base import OperationResult

# Executor สำหรับการอุ่นเครื่องแอปพลิเคชันล่วงหน้า
_app_preheat_executor = ThreadPoolExecutor(thread_name_prefix='od_app_preheat', max_workers=1)
# Executor สำหรับการแจ้งเตือน
_notify_executor = ThreadPoolExecutor(thread_name_prefix='od_app_notify', max_workers=1)


class ApplicationEventId(Enum):
    """
    Enum สำหรับ ID ของเหตุการณ์ที่เกี่ยวข้องกับแอปพลิเคชัน
    """
    APPLICATION_START: str = 'แอปพลิเคชันเริ่มทำงาน'
    APPLICATION_STOP: str = 'แอปพลิเคชันหยุดทำงาน'


class Application(Operation):
    """
    คลาสหลักสำหรับ "แอปพลิเคชัน" หรือ "งาน" หนึ่งๆ ในระบบ
    จัดการวงจรชีวิต, การบันทึก, การแจ้งเตือน, และการโต้ตอบกับ context ของ OneDragon
    """

    def __init__(self, ctx: OneDragonContext, app_id: str,
                 node_max_retry_times: int = 1,
                 op_name: str = None,
                 timeout_seconds: float = -1,
                 op_callback: Optional[Callable[[OperationResult], None]] = None,
                 need_check_game_win: bool = True,
                 op_to_enter_game: Optional[Operation] = None,
                 init_context_before_start: bool = True,
                 stop_context_after_stop: bool = True,
                 run_record: Optional[AppRunRecord] = None,
                 need_ocr: bool = True,
                 retry_in_od: bool = False,
                 need_notify: bool = False
                 ):
        """
        คอนสตรัคเตอร์ของคลาส Application

        :param ctx: Context ของ OneDragon
        :param app_id: ID เฉพาะของแอปพลิเคชัน
        :param node_max_retry_times: จำนวนครั้งสูงสุดในการลองใหม่สำหรับโหนด
        :param op_name: ชื่อของ Operation
        :param timeout_seconds: เวลาหมดเวลาเป็นวินาที
        :param op_callback: Callback ที่จะถูกเรียกเมื่อ Operation เสร็จสิ้น
        :param need_check_game_win: ต้องการตรวจสอบหน้าต่างเกมหรือไม่
        :param op_to_enter_game: Operation ที่จะใช้เพื่อเข้าสู่เกม
        :param init_context_before_start: จะเริ่มต้น context ก่อนเริ่มทำงานหรือไม่
        :param stop_context_after_stop: จะหยุด context หลังจากหยุดทำงานหรือไม่
        :param run_record: อ็อบเจกต์สำหรับบันทึกการทำงาน
        :param need_ocr: ต้องการใช้ OCR หรือไม่
        :param retry_in_od: จะทำการลองใหม่ภายใน OneDragon หรือไม่
        :param need_notify: ต้องการส่งการแจ้งเตือนหรือไม่
        """
        super().__init__(ctx, node_max_retry_times=node_max_retry_times, op_name=op_name,
                         timeout_seconds=timeout_seconds,
                         op_callback=op_callback,
                         need_check_game_win=need_check_game_win,
                         op_to_enter_game=op_to_enter_game)

        self.app_id: str = app_id
        """ตัวระบุเฉพาะของแอปพลิเคชัน"""

        self.run_record: Optional[AppRunRecord] = run_record
        """บันทึกการทำงาน"""

        self.init_context_before_start: bool = init_context_before_start
        """จะเริ่มต้น Context ก่อนเริ่มทำงานหรือไม่ (OneDragon ต้องการเฉพาะแอปพลิเคชันแรก)"""

        self.stop_context_after_stop: bool = stop_context_after_stop
        """จะหยุด Context หลังจากหยุดทำงานหรือไม่ (OneDragon ต้องการเฉพาะแอปพลิเคชันสุดท้าย)"""

        self.need_ocr: bool = need_ocr
        """ต้องการ OCR"""

        self._retry_in_od: bool = retry_in_od  # ทำการลองใหม่ใน OneDragon

        self.need_notify: bool = need_notify  # ส่งการแจ้งเตือนหลังจากโหนดทำงานเสร็จสิ้น

        self.notify_screenshot: Optional[BytesIO] = None  # ภาพหน้าจอสำหรับส่งการแจ้งเตือน

    def _init_before_execute(self) -> None:
        """
        เมธอดที่ถูกเรียกก่อนการ execute หลักของ Operation
        ทำการอัปเดตสถานะการทำงาน, ส่งการแจ้งเตือนเริ่มต้น (ถ้ามี), และเริ่มต้น context
        """
        Operation._init_before_execute(self)
        if self.run_record is not None:
            self.run_record.update_status(AppRunRecord.STATUS_RUNNING)
        if self.need_notify:
            self.notify(None)  # ส่งการแจ้งเตือนว่า "เริ่ม"

        self.init_for_application()
        self.ctx.start_running()
        self.ctx.dispatch_event(ApplicationEventId.APPLICATION_START.value, self.app_id)

    def handle_resume(self) -> None:
        """
        การประมวลผลหลังจากการทำงานต่อ (Resume) ให้คลาสลูก implement
        :return:
        """
        pass

    def after_operation_done(self, result: OperationResult):
        """
        การประมวลผลหลังจาก Operation (งานหลักของแอปพลิเคชัน) เสร็จสิ้น
        อัปเดตบันทึก, หยุด context (ถ้าจำเป็น), และส่งการแจ้งเตือนผลลัพธ์
        :param result: ผลลัพธ์ของ Operation
        :return:
        """
        Operation.after_operation_done(self, result)
        self._update_record_after_stop(result)
        if self.stop_context_after_stop:
            self.ctx.stop_running()
        self.ctx.dispatch_event(ApplicationEventId.APPLICATION_STOP.value, self.app_id)
        if self.need_notify:
            self.notify(result.success)

    def _update_record_after_stop(self, result: OperationResult):
        """
        การอัปเดตบันทึกการทำงานหลังจากแอปพลิเคชันหยุด
        :param result: ผลลัพธ์การทำงาน
        :return:
        """
        if self.run_record is not None:
            if result.success:
                self.run_record.update_status(AppRunRecord.STATUS_SUCCESS)
            else:
                self.run_record.update_status(AppRunRecord.STATUS_FAIL)

    def notify(self, is_success: Optional[bool] = True) -> None:
        """
        ส่งการแจ้งเตือน จะถูกเรียกเมื่อแอปพลิเคชันเริ่มหรือหยุดทำงาน และจะจับภาพหน้าจอเมื่อถูกเรียก (สำหรับกรณีล้มเหลว)
        :param is_success: สถานะความสำเร็จของงาน (True: สำเร็จ, False: ล้มเหลว, None: เริ่ม)
        :return:
        """
        if not hasattr(self.ctx, 'notify_config'): # ตรวจสอบว่ามี config การแจ้งเตือนหรือไม่
            return
        if not getattr(self.ctx.notify_config, 'enable_notify', False): # ตรวจสอบว่าเปิดใช้งานการแจ้งเตือนหรือไม่
            return
        # ถ้าเป็นการแจ้งเตือน "เริ่ม" (is_success is None) ให้ตรวจสอบว่าเปิดใช้งานการแจ้งเตือนก่อนเริ่มหรือไม่
        if not getattr(self.ctx.notify_config, 'enable_before_notify', False) and is_success is None:
            return

        app_id = getattr(self, 'app_id', None)
        app_name = getattr(self, 'op_name', None)

        # ตรวจสอบว่าเปิดใช้งานการแจ้งเตือนสำหรับ app_id นี้หรือไม่
        if not getattr(self.ctx.notify_config, app_id, False):
            return

        if is_success is True:
            status = 'สำเร็จ'
            image_source = self.notify_screenshot # ใช้ภาพที่เตรียมไว้ (ถ้ามี)
        elif is_success is False:
            status = 'ล้มเหลว'
            image_source = self.save_screenshot_bytes() # จับภาพหน้าจอปัจจุบัน
        elif is_success is None: # กรณีเริ่มทำงาน
            status = 'เริ่ม'
            image_source = None
        else: # กรณีอื่นๆ ที่ไม่คาดคิด
            return


        send_image = getattr(self.ctx.push_config, 'send_image', False) # ตรวจสอบว่า config ให้ส่งรูปภาพหรือไม่
        image = image_source if send_image else None

        message = f"งาน 「{app_name}」 ทำงาน{status}\n"

        pusher = Push(self.ctx) # สร้าง instance ของ Pusher
        _notify_executor.submit(pusher.send, message, image) # ส่งการแจ้งเตือนใน thread แยก

    @property
    def current_execution_desc(self) -> str:
        """
        คำอธิบายการทำงานปัจจุบัน สำหรับแสดงผลบน UI
        :return: สตริงคำอธิบาย
        """
        return ''

    @property
    def next_execution_desc(self) -> str:
        """
        คำอธิบายการทำงานถัดไป สำหรับแสดงผลบน UI
        :return: สตริงคำอธิบาย
        """
        return ''

    @staticmethod
    def get_preheat_executor() -> ThreadPoolExecutor:
        """
        รับ ThreadPoolExecutor สำหรับการอุ่นเครื่อง (preheat)
        :return: ThreadPoolExecutor
        """
        return _app_preheat_executor

    def init_for_application(self) -> bool:
        """
        การเริ่มต้นที่จำเป็นสำหรับแอปพลิเคชัน เช่น การโหลดโมเดล OCR
        :return: True หากการเริ่มต้นสำเร็จ
        """
        if self.need_ocr:
            self.ctx.ocr.init_model() # เริ่มต้นโมเดล OCR
        return True


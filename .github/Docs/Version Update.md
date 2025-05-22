______________

## 1\. ตัวละครใหม่ (New Character)

  - `agent.py` ใน `AgentEnum` เพิ่มตัวละครใหม่ (โปรดทราบว่าชื่อตัวละครต้องตรงกับชื่อที่ปรากฏเมื่อเรียกการสนับสนุนใน **โฮล (Hollow)**)
  - ภาพสกรีนช็อตอวาตาร์ (Avatar Screenshots)
      - หน้าจอการต่อสู้ (Battle Screen): ตำแหน่งที่ 1, ตำแหน่งที่ 2, การสนับสนุนด่วน (Quick Support), ท่าผสาน (Link Skill)
      - หากต้องการการตัดสินสถานะ (Status) จำเป็นต้องมีภาพสกรีนช็อตสถานะของแต่ละตำแหน่ง ทั้งในทีม 3 คนและทีม 2 คน
      - อวาตาร์ด้านล่างใน **โฮล (Hollow)**
      - อวาตาร์ตำแหน่งที่ 1 ในทีมที่เตรียมไว้ (Preset Team Slot 1 Avatar)
  - `call_for_support.py` ใน `reject_agent` เพิ่มตัวเลือกการปฏิเสธ (add rejection option)
  - `CallSupport-Reject.yml`  เพิ่มตัวเลือกการปฏิเสธ (add rejection option)
  - `Encounter.yml`  เพิ่มอีเวนต์ใน **โฮล (Hollow)** (add Hollow event)

### 1.1. สถานะตัวละคร (Character Status)

หลังจากเพิ่มแล้ว สามารถเพิ่มการทดสอบที่เกี่ยวข้องได้ใน [โปรเจกต์ทดสอบ (Test Project)](https://github.com/DoctorReid/zzz-od-test/tree/main/test/auto_battle/agent_state_checker)

#### 1.1.1. หลักการทำงาน (Principle)

โดยปกติแล้ว สถานะของตัวละครจะมีตำแหน่งที่แน่นอน และจะแสดงเนื้อหาเช่น แถบยาว (long bars), จุดวงกลม (circular dots) ฯลฯ บนพื้นฐานนั้น

ดังนั้น วิธีที่ง่ายที่สุดในการจดจำคือการตัดสินด้วยสี ณ ตำแหน่งที่แน่นอนนั้น

การเพิ่มสถานะตัวละครใหม่ จำเป็นต้องทำสิ่งต่อไปนี้:

  - เพิ่มคำจำกัดความของสถานะใน `AgentEnum`
  - แต่ละสถานะ จำเป็นต้องมีภาพสกรีนช็อตของทุกตำแหน่ง ทั้งในทีม 3 คนและทีม 2 คน และจากภาพสกรีนช็อตเหล่านั้น ให้เพิ่มเทมเพลต (template) ที่เกี่ยวข้องในส่วนการจัดการเทมเพลต (template management)
  - ในโปรเจกต์ทดสอบ (Test Project) ให้เพิ่มกรณีทดสอบ (test cases) ที่เกี่ยวข้อง

#### 1.1.1. ประเภทแถบยาว-1 (Long-bar Type-1)

ตัวอย่าง: **ชิงอี (Qingyi)**, **ไรท์ (Wright)**

สามารถใช้สีพื้นหลังของแถบยาว เพื่อตัดสินความยาวของแถบสถานะที่ยังไม่เต็ม และจากนั้นคำนวณย้อนกลับเพื่อหาความยาวปัจจุบันของแถบสถานะ

ในส่วนการจัดการเทมเพลต (template management) ให้เพิ่มเทมเพลต (template) ที่มีความสูงเป็น 1 โดยตำแหน่งที่บันทึกในเทมเพลตคือตำแหน่งที่ต้องใช้ในการจดจำสี

ดูโค้ดการจดจำ (recognition code) ได้ที่ `agent_state_checker.check_length_by_background_gray`

## 2\. สกินใหม่ (New Skin)

  - `agent_outfit_config.py` เพิ่มตัวเลือกสกิน (skin options) ที่เกี่ยวข้อง
  - ทำการจับภาพสกรีนช็อตสำหรับสกินใหม่ตามขั้นตอนในหัวข้อ 1. ตัวละครใหม่ (New Character)
  - `zzz_one_dragon_setting_interface.py`
      - `get_agent_outfit_group` เพิ่มตัวเลือก (add option)
      - `on_interface_shown` เพิ่มการกำหนดค่าเริ่มต้น (add initialization)
  - `zzz_context.py` `init_agent_template_id` เพิ่มการกำหนดค่าเริ่มต้น (initialization) ที่เกี่ยวข้อง

## 3\.
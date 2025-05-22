# โค้ดมาจาก whyour/qinglong/develop/sample/notify.py ขอขอบคุณผู้เขียนต้นฉบับสำหรับการมีส่วนร่วม
import base64
import copy
import hashlib
import hmac
import json
import re
import smtplib
import threading
import time
import urllib.parse

from io import BytesIO
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from typing import Optional

from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.utils.log_utils import log

import requests

class Push:

    _default_push_config = {
        'BARK_PUSH': '',                    # Bark IP หรือรหัสอุปกรณ์, เช่น: https://api.day.app/DxHcxxxxxRxxxxxxcm/
        'BARK_ARCHIVE': '',                 # Bark จะเก็บถาวรการแจ้งเตือนหรือไม่
        'BARK_GROUP': '',                   # Bark กลุ่มการแจ้งเตือน
        'BARK_SOUND': '',                   # Bark เสียงการแจ้งเตือน
        'BARK_ICON': '',                    # Bark ไอคอนการแจ้งเตือน
        'BARK_LEVEL': '',                   # Bark ความเร่งด่วนของการแจ้งเตือน
        'BARK_URL': '',                     # Bark URL สำหรับการเปลี่ยนเส้นทาง

        'CONSOLE': False,                   # แสดงผลในคอนโซล

        'DD_BOT_SECRET': '',                # DD_BOT_SECRET ของ DingTalk Bot
        'DD_BOT_TOKEN': '',                 # DD_BOT_TOKEN ของ DingTalk Bot

        'FS_KEY': '',                        # KEY ของ Feishu Bot

        'ONEBOT_URL': '',                   # ที่อยู่ Push ของ OneBot, ลงท้ายด้วย send_msg
        'ONEBOT_USER': '',                  # ผู้รับ Push ของ OneBot, หมายเลข QQ
        'ONEBOT_GROUP': '',                 # ผู้รับ Push ของ OneBot, หมายเลขกลุ่ม
        'ONEBOT_TOKEN': '',                 # access_token ของ OneBot, ไม่บังคับ

        'GOTIFY_URL': '',                   # ที่อยู่ Gotify, เช่น https://push.example.de:8080
        'GOTIFY_TOKEN': '',                 # token แอปพลิเคชันข้อความของ Gotify
        'GOTIFY_PRIORITY': 0,               # ลำดับความสำคัญของข้อความ Push, ค่าเริ่มต้นคือ 0

        'IGOT_PUSH_KEY': '',                # IGOT_PUSH_KEY ของ iGot Push

        'SERVERCHAN_PUSH_KEY': '',          # PUSH_KEY ของ Server Chan, รองรับทั้งเวอร์ชันเก่าและ Turbo

        'DEER_KEY': '',                     # PUSHDEER_KEY ของ PushDeer
        'DEER_URL': '',                     # PUSHDEER_URL ของ PushDeer

        'CHAT_URL': '',                     # Synology Chat URL
        'CHAT_TOKEN': '',                   # Synology Chat Token

        'PUSH_PLUS_TOKEN': '',              # โทเค็นผู้ใช้ PushPlus
        'PUSH_PLUS_USER': '',               # รหัสกลุ่ม PushPlus
        'PUSH_PLUS_TEMPLATE': 'html',       # เทมเพลต PushPlus, รองรับ html,txt,json,markdown,cloudMonitor,jenkins,route,pay
        'PUSH_PLUS_CHANNEL': 'wechat',      # ช่องทาง PushPlus, รองรับ wechat,webhook,cp,mail,sms
        'PUSH_PLUS_WEBHOOK': '',            # รหัส webhook PushPlus, สามารถกำหนดค่าช่องทางเพิ่มเติมได้ในบัญชีสาธารณะ PushPlus
        'PUSH_PLUS_CALLBACKURL': '',        # ที่อยู่เรียกกลับผลลัพธ์ PushPlus, จะแจ้งผลลัพธ์สุดท้ายไปยังที่อยู่นี้
        'PUSH_PLUS_TO': '',                 # โทเค็นเพื่อน PushPlus, ช่องทาง WeChat Public Account กรอกโทเค็นเพื่อน, ช่องทาง Enterprise WeChat กรอกรหัสผู้ใช้ Enterprise WeChat

        'WE_PLUS_BOT_TOKEN': '',            # โทเค็นผู้ใช้ WePlus Bot
        'WE_PLUS_BOT_RECEIVER': '',         # ผู้รับข้อความ WePlus Bot
        'WE_PLUS_BOT_VERSION': 'pro',       # เวอร์ชันการเรียกใช้ WePlus Bot

        'QMSG_KEY': '',                     # QMSG_KEY ของ Qmsg
        'QMSG_TYPE': '',                    # QMSG_TYPE ของ Qmsg

        'QYWX_ORIGIN': '',                  # ที่อยู่พร็อกซี Enterprise WeChat

        'QYWX_AM': '',                      # แอปพลิเคชัน Enterprise WeChat

        'QYWX_KEY': '',                     # Enterprise WeChat Bot

        'DISCORD_BOT_TOKEN': '',            # โทเค็น Discord Bot
        'DISCORD_USER_ID': '',              # รหัสผู้ใช้ Discord ที่รับข้อความ

        'TG_BOT_TOKEN': '',                 # TG_BOT_TOKEN ของ Telegram Bot, เช่น: 1407203283:AAG9rt-6RDaaX0HBLZQq1laNOh898iFYaRQ
        'TG_USER_ID': '',                   # TG_USER_ID ของ Telegram Bot, เช่น: 1434078534
        'TG_API_HOST': '',                  # โฮสต์ API พร็อกซี Telegram
        'TG_PROXY_AUTH': '',                # พารามิเตอร์การรับรองความถูกต้องของพร็อกซี Telegram
        'TG_PROXY_HOST': '',                # TG_PROXY_HOST ของ Telegram Bot
        'TG_PROXY_PORT': '',                # TG_PROXY_PORT ของ Telegram Bot

        'AIBOTK_KEY': '',                   # apikey ของ Aibotk จากศูนย์ส่วนตัว เอกสาร: http://wechat.aibotk.com/docs/about
        'AIBOTK_TYPE': '',                  # ประเภทการส่งของ Aibotk: room หรือ contact
        'AIBOTK_NAME': '',                  # ชื่อกลุ่มหรือชื่อเล่นเพื่อนของ Aibotk ต้องตรงกับ type

        'SMTP_SERVER': '',                  # เซิร์ฟเวอร์ SMTP สำหรับส่งอีเมล, เช่น smtp.exmail.qq.com:465
        'SMTP_SSL': 'false',                # SMTP ใช้ SSL หรือไม่, กรอก true หรือ false
        'SMTP_EMAIL': '',                   # อีเมลผู้ส่ง/ผู้รับ SMTP, การแจ้งเตือนจะถูกส่งถึงตัวเอง
        'SMTP_PASSWORD': '',                # รหัสผ่านเข้าสู่ระบบ SMTP, อาจเป็นรหัสพิเศษ ขึ้นอยู่กับผู้ให้บริการอีเมล
        'SMTP_NAME': '',                    # ชื่อผู้ส่ง/ผู้รับ SMTP, สามารถกรอกอะไรก็ได้

        'PUSHME_KEY': '',                   # PUSHME_KEY ของ PushMe
        'PUSHME_URL': '',                   # PUSHME_URL ของ PushMe

        'CHRONOCAT_QQ': '',                 # หมายเลข QQ
        'CHRONOCAT_TOKEN': '',              # โทเค็น CHRONOCAT
        'CHRONOCAT_URL': '',                # ที่อยู่ URL ของ CHRONOCAT

        'WEBHOOK_URL': '',                  # ที่อยู่ URL ของการแจ้งเตือนแบบกำหนดเอง
        'WEBHOOK_BODY': '',                 # เนื้อหาคำขอของการแจ้งเตือนแบบกำหนดเอง
        'WEBHOOK_HEADERS': '',              # ส่วนหัวคำขอของการแจ้งเตือนแบบกำหนดเอง
        'WEBHOOK_METHOD': '',               # วิธีการคำขอของการแจ้งเตือนแบบกำหนดเอง
        'WEBHOOK_CONTENT_TYPE': '',         # Content-Type ของการแจ้งเตือนแบบกำหนดเอง

        'NTFY_URL': '',                     # ที่อยู่ Ntfy, เช่น https://ntfy.sh
        'NTFY_TOPIC': '',                   # หัวข้อแอปพลิเคชันข้อความของ Ntfy
        'NTFY_PRIORITY':'3',                # ลำดับความสำคัญของข้อความ Push, ค่าเริ่มต้นคือ 3

        'WXPUSHER_APP_TOKEN': '',           # appToken ของ WxPusher เอกสารทางการ: https://wxpusher.zjiecode.com/docs/ แผงควบคุม: https://wxpusher.zjiecode.com/admin/
        'WXPUSHER_TOPIC_IDS': '',           # ID หัวข้อของ WxPusher, หลายรายการคั่นด้วยเครื่องหมายอัฒภาค; topic_ids และ uids ต้องกำหนดค่าอย่างน้อยหนึ่งอย่าง
        'WXPUSHER_UIDS': '',                # ID ผู้ใช้ของ WxPusher, หลายรายการคั่นด้วยเครื่องหมายอัฒภาค; topic_ids และ uids ต้องกำหนดค่าอย่างน้อยหนึ่งอย่าง
    }


    def __init__(self, ctx: OneDragonContext):
        self.ctx: OneDragonContext = ctx
        self.push_config = copy.deepcopy(Push._default_push_config)


    def bark(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ Bark
        """

        log.info("เริ่มบริการ Bark")

        if self.push_config.get("BARK_PUSH").startswith("http"):
            url = f'{self.push_config.get("BARK_PUSH")}'
        else:
            url = f'https://api.day.app/{self.push_config.get("BARK_PUSH")}'

        bark_params = {
            "BARK_DEVICE_KEY": "device_key",
            "BARK_ARCHIVE": "isArchive",
            "BARK_GROUP": "group",
            "BARK_SOUND": "sound",
            "BARK_ICON": "icon",
            "BARK_LEVEL": "level",
            "BARK_URL": "url",
        }
        data = {
            "title": title,
            "body": content,
        }
        for pair in filter(
            lambda pairs: pairs[0].startswith("BARK_")
            and pairs[0] != "BARK_PUSH"
            and pairs[1]
            and bark_params.get(pairs[0]),
            self.push_config.items(),
        ):
            data[bark_params.get(pair[0])] = pair[1]
        headers = {"Content-Type": "application/json;charset=utf-8"}
        response = requests.post(
            url=url, data=json.dumps(data), headers=headers, timeout=15
        ).json()

        if response["code"] == 200:
            log.info("ส่ง Bark สำเร็จ!")
        else:
            log.error("ส่ง Bark ล้มเหลว!")


    def console(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ Console
        """
        print(f"{title}\n{content}")


    def dingding_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ DingTalk Bot
        """

        log.info("เริ่มบริการ DingTalk Bot")

        timestamp = str(round(time.time() * 1000))
        secret_enc = self.push_config.get("DD_BOT_SECRET").encode("utf-8")
        string_to_sign = "{}\n{}".format(timestamp, self.push_config.get("DD_BOT_SECRET"))
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        url = f'https://oapi.dingtalk.com/robot/send?access_token={self.push_config.get("DD_BOT_TOKEN")}×tamp={timestamp}&sign={sign}'
        headers = {"Content-Type": "application/json;charset=utf-8"}
        data = {"msgtype": "text", "text": {"content": f"{title}\n{content}"}}
        response = requests.post(
            url=url, data=json.dumps(data), headers=headers, timeout=15
        ).json()

        if not response["errcode"]:
            log.info("ส่ง DingTalk Bot สำเร็จ!")
        else:
            log.error("ส่ง DingTalk Bot ล้มเหลว!")


    def feishu_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ Feishu Bot
        """

        log.info("เริ่มบริการ Feishu")

        url = f'https://open.feishu.cn/open-apis/bot/v2/hook/{self.push_config.get("FS_KEY")}'
        data = {"msg_type": "text", "content": {"text": f"{title}\n{content}"}}
        response = requests.post(url, data=json.dumps(data)).json()

        if response.get("StatusCode") == 0 or response.get("code") == 0:
            log.info("ส่ง Feishu สำเร็จ!")
        else:
            log.error(f"ส่ง Feishu ล้มเหลว! ข้อผิดพลาด:\n{response}")


    def one_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ OneBot
        """

        log.info("เริ่มบริการ OneBot")

        url = self.push_config.get("ONEBOT_URL").rstrip("/")
        user_id = self.push_config.get("ONEBOT_USER")
        group_id = self.push_config.get("ONEBOT_GROUP")
        token = self.push_config.get("ONEBOT_TOKEN")

        if not url.endswith("/send_msg"):
                url += "/send_msg"

        headers = {'Content-Type': "application/json"}
        message = [{"type": "text", "data": {"text": f"{title}\n{content}"}}]
        if image:
            image.seek(0)
            image_base64 = base64.b64encode(image.getvalue()).decode('utf-8')
            message.append({"type": "image", "data": {"file": f'base64://{image_base64}'}})
        data_private = {"message": message}
        data_group = {"message": message}

        if token != "":
            headers["Authorization"] = f"Bearer {token}"

        if user_id != "":
            data_private["message_type"] = "private"
            data_private["user_id"] = user_id
            response_private = requests.post(url, data=json.dumps(data_private), headers=headers).json()

            if response_private["status"] == "ok":
                log.info("ส่ง OneBot Private Chat สำเร็จ!")
            else:
                log.error("ส่ง OneBot Private Chat ล้มเหลว!")

        if group_id != "":
            data_group["message_type"] = "group"
            data_group["group_id"] = group_id
            response_group = requests.post(url, data=json.dumps(data_group), headers=headers).json()

            if response_group["status"] == "ok":
                log.info("ส่ง OneBot Group Chat สำเร็จ!")
            else:
                log.error("ส่ง OneBot Group Chat ล้มเหลว!")


    def gotify(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ Gotify
        """

        log.info("เริ่มบริการ Gotify")

        url = f'{self.push_config.get("GOTIFY_URL")}/message?token={self.push_config.get("GOTIFY_TOKEN")}'
        data = {
            "title": title,
            "message": content,
            "priority": self.push_config.get("GOTIFY_PRIORITY"),
        }
        response = requests.post(url, data=data).json()

        if response.get("id"):
            log.info("ส่ง Gotify สำเร็จ!")
        else:
            log.error("ส่ง Gotify ล้มเหลว!")


    def iGot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ iGot
        """

        log.info("เริ่มบริการ iGot")

        url = f'https://push.hellyw.com/{self.push_config.get("IGOT_PUSH_KEY")}'
        data = {"title": title, "content": content}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(url, data=data, headers=headers).json()

        if response["ret"] == 0:
            log.info("ส่ง iGot สำเร็จ!")
        else:
            log.error(f'ส่ง iGot ล้มเหลว! {response["errMsg"]}')


    def serverchan(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ ServerChan
        """

        log.info("เริ่มบริการ Server Chan")

        data = {"text": title, "desp": content.replace("\n", "\n\n")}

        match = re.match(r"sctp(\d+)t", self.push_config.get("SERVERCHAN_PUSH_KEY"))
        if match:
            num = match.group(1)
            url = f'https://{num}.push.ft07.com/send/{self.push_config.get("SERVERCHAN_PUSH_KEY")}.send'
        else:
            url = f'https://sctapi.ftqq.com/{self.push_config.get("SERVERCHAN_PUSH_KEY")}.send'

        response = requests.post(url, data=data).json()

        if response.get("errno") == 0 or response.get("code") == 0:
            log.info("ส่ง Server Chan สำเร็จ!")
        else:
            log.error(f'ส่ง Server Chan ล้มเหลว! รหัสข้อผิดพลาด: {response["message"]}')


    def pushdeer(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ PushDeer
        """

        log.info("เริ่มบริการ PushDeer")
        data = {
            "text": title,
            "desp": content,
            "type": "markdown",
            "pushkey": self.push_config.get("DEER_KEY"),
        }
        url = "https://api2.pushdeer.com/message/push"
        if self.push_config.get("DEER_URL"):
            url = self.push_config.get("DEER_URL")

        response = requests.post(url, data=data).json()

        if len(response.get("content").get("result")) > 0:
            log.info("ส่ง PushDeer สำเร็จ!")
        else:
            log.error(f"ส่ง PushDeer ล้มเหลว! ข้อผิดพลาด: {response}")


    def chat(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ Chat
        """

        log.info("เริ่มบริการ Chat")
        data = "payload=" + json.dumps({"text": title + "\n" + content})
        url = self.push_config.get("CHAT_URL") + self.push_config.get("CHAT_TOKEN")
        response = requests.post(url, data=data)

        if response.status_code == 200:
            log.info("ส่ง Chat สำเร็จ!")
        else:
            log.error(f"ส่ง Chat ล้มเหลว! ข้อผิดพลาด: {response}")


    def pushplus_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ PushPlus
        """

        log.info("เริ่มบริการ PUSHPLUS")

        url = "https://www.pushplus.plus/send"
        data = {
            "token": self.push_config.get("PUSH_PLUS_TOKEN"),
            "title": title,
            "content": content,
            "topic": self.push_config.get("PUSH_PLUS_USER"),
            "template": self.push_config.get("PUSH_PLUS_TEMPLATE"),
            "channel": self.push_config.get("PUSH_PLUS_CHANNEL"),
            "webhook": self.push_config.get("PUSH_PLUS_WEBHOOK"),
            "callbackUrl": self.push_config.get("PUSH_PLUS_CALLBACKURL"),
            "to": self.push_config.get("PUSH_PLUS_TO"),
        }
        body = json.dumps(data).encode(encoding="utf-8")
        headers = {"Content-Type": "application/json"}
        response = requests.post(url=url, data=body, headers=headers).json()

        code = response["code"]
        if code == 200:
            log.info("ส่งคำขอ PUSHPLUS สำเร็จ, สามารถตรวจสอบผลลัพธ์การส่งได้ด้วยหมายเลขซีเรียล:" + response["data"])
            log.info(
                "ข้อควรระวัง: การส่งคำขอสำเร็จไม่ได้หมายความว่าส่งสำเร็จ หากไม่ได้รับข้อความ โปรดตรวจสอบผลลัพธ์สุดท้ายของการส่งบนเว็บไซต์ pushplus ด้วยหมายเลขซีเรียล"
            )
        elif code == 900 or code == 903 or code == 905 or code == 999:
            log.info(response["msg"])

        else:
            url_old = "http://pushplus.hxtrip.com/send"
            headers["Accept"] = "application/json"
            response = requests.post(url=url_old, data=body, headers=headers).json()

            if response["code"] == 200:
                log.info("ส่ง PUSHPLUS(hxtrip) สำเร็จ!")

            else:
                log.error("ส่ง PUSHPLUS ล้มเหลว!")


    def weplus_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ WePlus Bot
        """

        log.info("เริ่มบริการ WePlus Bot")

        template = "txt"
        if len(content) > 800:
            template = "html"

        url = "https://www.weplusbot.com/send"
        data = {
            "token": self.push_config.get("WE_PLUS_BOT_TOKEN"),
            "title": title,
            "content": content,
            "template": template,
            "receiver": self.push_config.get("WE_PLUS_BOT_RECEIVER"),
            "version": self.push_config.get("WE_PLUS_BOT_VERSION"),
        }
        body = json.dumps(data).encode(encoding="utf-8")
        headers = {"Content-Type": "application/json"}
        response = requests.post(url=url, data=body, headers=headers).json()

        if response["code"] == 200:
            log.info("ส่ง WePlus Bot สำเร็จ!")
        else:
            log.error("ส่ง WePlus Bot ล้มเหลว!")


    def qmsg_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ Qmsg
        """

        log.info("เริ่มบริการ Qmsg")

        url = f'https://qmsg.zendee.cn/{self.push_config.get("QMSG_TYPE")}/{self.push_config.get("QMSG_KEY")}'
        payload = {"msg": f'{title}\n{content.replace("----", "-")}'.encode("utf-8")}
        response = requests.post(url=url, params=payload).json()

        if response["code"] == 0:
            log.info("ส่ง Qmsg สำเร็จ!")
        else:
            log.error(f'ส่ง Qmsg ล้มเหลว! {response["reason"]}')


    def wecom_app(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ Enterprise WeChat APP
        """
        QYWX_AM_AY = re.split(",", self.push_config.get("QYWX_AM"))
        if 4 < len(QYWX_AM_AY) > 5:
            log.info("การตั้งค่า QYWX_AM ผิดพลาด!!")
            return
        log.info("เริ่มบริการ Enterprise WeChat APP")

        corpid = QYWX_AM_AY[0]
        corpsecret = QYWX_AM_AY[1]
        touser = QYWX_AM_AY[2]
        agentid = QYWX_AM_AY[3]
        try:
            media_id = QYWX_AM_AY[4]
        except IndexError:
            media_id = ""
        if self.push_config.get("QYWX_ORIGIN"):
            origin = self.push_config.get("QYWX_ORIGIN")
        else:
            origin = "https://qyapi.weixin.qq.com"
        wx = self.WeCom(corpid, corpsecret, agentid, origin)
        # หากไม่ได้กำหนดค่า media_id จะส่งเป็นข้อความธรรมดาโดยค่าเริ่มต้น
        if not media_id:
            message = title + "\n\n" + content
            response = wx.send_text(message, touser)
        else:
            response = wx.send_mpnews(title, content, media_id, touser)

        if response == "ok":
            log.info("ส่ง Enterprise WeChat สำเร็จ!")
        else:
            log.error(f"ส่ง Enterprise WeChat ล้มเหลว! ข้อผิดพลาด:\n{response}")


    class WeCom:
        def __init__(self, corpid, corpsecret, agentid, origin):
            self.CORPID = corpid
            self.CORPSECRET = corpsecret
            self.AGENTID = agentid
            self.ORIGIN = origin

        def get_access_token(self):
            url = f"{self.ORIGIN}/cgi-bin/gettoken"
            values = {
                "corpid": self.CORPID,
                "corpsecret": self.CORPSECRET,
            }
            req = requests.post(url, params=values)
            data = json.loads(req.text)
            return data["access_token"]

        def send_text(self, message, touser="@all"):
            send_url = (
                f"{self.ORIGIN}/cgi-bin/message/send?access_token={self.get_access_token()}"
            )
            send_values = {
                "touser": touser,
                "msgtype": "text",
                "agentid": self.AGENTID,
                "text": {"content": message},
                "safe": "0",
            }
            send_msges = bytes(json.dumps(send_values), "utf-8")
            respone = requests.post(send_url, send_msges)
            respone = respone.json()
            return respone["errmsg"]

        def send_mpnews(self, title, message, media_id, touser="@all"):
            send_url = (
                f"{self.ORIGIN}/cgi-bin/message/send?access_token={self.get_access_token()}"
            )
            send_values = {
                "touser": touser,
                "msgtype": "mpnews",
                "agentid": self.AGENTID,
                "mpnews": {
                    "articles": [
                        {
                            "title": title,
                            "thumb_media_id": media_id,
                            "author": "Author",
                            "content_source_url": "",
                            "content": message.replace("\n", "<br/>"),
                            "digest": message,
                        }
                    ]
                },
            }
            send_msges = bytes(json.dumps(send_values), "utf-8")
            respone = requests.post(send_url, send_msges)
            respone = respone.json()
            return respone["errmsg"]


    def wecom_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ Enterprise WeChat Bot
        """

        log.info("เริ่มบริการ Enterprise WeChat Bot")

        origin = "https://qyapi.weixin.qq.com"
        if self.push_config.get("QYWX_ORIGIN"):
            origin = self.push_config.get("QYWX_ORIGIN")

        url = f"{origin}/cgi-bin/webhook/send?key={self.push_config.get('QYWX_KEY')}"
        headers = {"Content-Type": "application/json;charset=utf-8"}
        data = {"msgtype": "text", "text": {"content": f"{title}\n{content}"}}
        response = requests.post(
            url=url, data=json.dumps(data), headers=headers, timeout=15
        ).json()

        if response["errcode"] == 0:
            log.info("ส่ง Enterprise WeChat Bot สำเร็จ!")
        else:
            log.error("ส่ง Enterprise WeChat Bot ล้มเหลว!")


    def discord_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ Discord Bot
        """

        log.info("เริ่มบริการ Discord Bot")

        base_url = "https://discord.com/api/v9"
        headers = {
            "Authorization": f"Bot {self.push_config.get('DISCORD_BOT_TOKEN')}",
            "User-Agent": "OneDragon"
        }

        create_dm_url = f"{base_url}/users/@me/channels"
        dm_headers = headers.copy()
        dm_headers["Content-Type"] = "application/json"
        dm_payload = json.dumps({"recipient_id": self.push_config.get('DISCORD_USER_ID')})
        response = requests.post(create_dm_url, headers=dm_headers, data=dm_payload, timeout=15)
        response.raise_for_status()
        channel_id = response.json().get("id")
        if not channel_id or channel_id == "":
            log.error(f"สร้างช่อง DM ของ Discord ล้มเหลว")
            return

        message_url = f"{base_url}/channels/{channel_id}/messages"
        message_payload_dict = {"content": f"{title}\n{content}"}

        files = None
        if image:
            image.seek(0)
            files = {'file': ('image.png', image, 'image/png')}
            data = {'payload_json': json.dumps(message_payload_dict)}
            if "Content-Type" in headers:
                del headers["Content-Type"]
        else:
            headers["Content-Type"] = "application/json"
            data = json.dumps(message_payload_dict)

        response = requests.post(message_url, headers=headers, data=data, files=files, timeout=30)
        response.raise_for_status()
        log.info("ส่ง Discord Bot สำเร็จ!")


    def telegram_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ Telegram Bot
        """

        log.info("เริ่มบริการ Telegram")

        if self.push_config.get("TG_API_HOST"):
            url = f"{self.push_config.get('TG_API_HOST')}/bot{self.push_config.get('TG_BOT_TOKEN')}/sendMessage"
        else:
            url = (
                f"https://api.telegram.org/bot{self.push_config.get('TG_BOT_TOKEN')}/sendMessage"
            )
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "chat_id": str(self.push_config.get("TG_USER_ID")),
            "text": f"{title}\n{content}",
            "disable_web_page_preview": "true",
        }
        proxies = None
        if self.push_config.get("TG_PROXY_HOST") and self.push_config.get("TG_PROXY_PORT"):
            if self.push_config.get("TG_PROXY_AUTH") != "" and "@" not in self.push_config.get(
                "TG_PROXY_HOST"
            ):
                self.push_config["TG_PROXY_HOST"] = (
                    self.push_config.get("TG_PROXY_AUTH")
                    + "@"
                    + self.push_config.get("TG_PROXY_HOST")
                )
            proxyStr = "http://{}:{}".format(
                self.push_config.get("TG_PROXY_HOST"), self.push_config.get("TG_PROXY_PORT")
            )
            proxies = {"http": proxyStr, "https": proxyStr}
        response = requests.post(
            url=url, headers=headers, params=payload, proxies=proxies
        ).json()

        if response["ok"]:
            log.info("ส่ง Telegram สำเร็จ!")
        else:
            log.error("ส่ง Telegram ล้มเหลว!")


    def aibotk(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ Aibotk
        """

        log.info("เริ่มบริการ Aibotk")

        if self.push_config.get("AIBOTK_TYPE") == "room":
            url = "https://api-bot.aibotk.com/openapi/v1/chat/room"
            data = {
                "apiKey": self.push_config.get("AIBOTK_KEY"),
                "roomName": self.push_config.get("AIBOTK_NAME"),
                "message": {"type": 1, "content": f"{title}\n{content}"},
            }
        else:
            url = "https://api-bot.aibotk.com/openapi/v1/chat/contact"
            data = {
                "apiKey": self.push_config.get("AIBOTK_KEY"),
                "name": self.push_config.get("AIBOTK_NAME"),
                "message": {"type": 1, "content": f"{title}\n{content}"},
            }
        body = json.dumps(data).encode(encoding="utf-8")
        headers = {"Content-Type": "application/json"}
        response = requests.post(url=url, data=body, headers=headers).json()
        if response["code"] == 0:
            log.info("ส่ง Aibotk สำเร็จ!")
        else:
            log.error(f'ส่ง Aibotk ล้มเหลว! {response["error"]}')


    def smtp(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ SMTP Email
        """

        log.info("เริ่มบริการ SMTP Email")

        message = MIMEText(content, "plain", "utf-8")
        message["From"] = formataddr(
            (
                Header(self.push_config.get("SMTP_NAME"), "utf-8").encode(),
                self.push_config.get("SMTP_EMAIL"),
            )
        )
        message["To"] = formataddr(
            (
                Header(self.push_config.get("SMTP_NAME"), "utf-8").encode(),
                self.push_config.get("SMTP_EMAIL"),
            )
        )
        message["Subject"] = Header(title, "utf-8")

        try:
            smtp_server = (
                smtplib.SMTP_SSL(self.push_config.get("SMTP_SERVER"))
                if self.push_config.get("SMTP_SSL") == "true"
                else smtplib.SMTP(self.push_config.get("SMTP_SERVER"))
            )
            smtp_server.login(
                self.push_config.get("SMTP_EMAIL"), self.push_config.get("SMTP_PASSWORD")
            )
            smtp_server.sendmail(
                self.push_config.get("SMTP_EMAIL"),
                self.push_config.get("SMTP_EMAIL"),
                message.as_bytes(),
            )
            smtp_server.close()
            log.info("ส่ง SMTP Email สำเร็จ!")
        except Exception as e:
            log.error(f"ส่ง SMTP Email ล้มเหลว! {e}")


    def pushme(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ PushMe
        """

        log.info("เริ่มบริการ PushMe")

        url = (
            self.push_config.get("PUSHME_URL")
            if self.push_config.get("PUSHME_URL")
            else "https://push.i-i.me/"
        )
        data = {
            "push_key": self.push_config.get("PUSHME_KEY"),
            "title": title,
            "content": content,
            "date": self.push_config.get("date") if self.push_config.get("date") else "",
            "type": self.push_config.get("type") if self.push_config.get("type") else "",
        }
        response = requests.post(url, data=data)

        if response.status_code == 200 and response.text == "success":
            log.info("ส่ง PushMe สำเร็จ!")
        else:
            log.error(f"ส่ง PushMe ล้มเหลว! {response.status_code} {response.text}")


    def chronocat(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ CHRONOCAT
        """

        log.info("เริ่มบริการ CHRONOCAT")

        user_ids = re.findall(r"user_id=(\d+)", self.push_config.get("CHRONOCAT_QQ"))
        group_ids = re.findall(r"group_id=(\d+)", self.push_config.get("CHRONOCAT_QQ"))

        url = f'{self.push_config.get("CHRONOCAT_URL")}/api/message/send'
        headers = {
            "Content-Type": "application/json",
            "Authorization": f'Bearer {self.push_config.get("CHRONOCAT_TOKEN")}',
        }

        for chat_type, ids in [(1, user_ids), (2, group_ids)]:
            if not ids:
                continue
            for chat_id in ids:
                data = {
                    "peer": {"chatType": chat_type, "peerUin": chat_id},
                    "elements": [
                        {
                            "elementType": 1,
                            "textElement": {"content": f"{title}\n{content}"},
                        }
                    ],
                }
                response = requests.post(url, headers=headers, data=json.dumps(data))
                if response.status_code == 200:
                    if chat_type == 1:
                        log.info(f"ข้อความส่วนตัว QQ:{ids} ส่งสำเร็จ!")
                    else:
                        log.info(f"ข้อความกลุ่ม QQ:{ids} ส่งสำเร็จ!")
                else:
                    if chat_type == 1:
                        log.error(f"ข้อความส่วนตัว QQ:{ids} ส่งล้มเหลว!")
                    else:
                        log.error(f"ข้อความกลุ่ม QQ:{ids} ส่งล้มเหลว!")


    def ntfy(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ Ntfy
        """

        def encode_rfc2047(text: str) -> str:
            """เข้ารหัสข้อความเป็นรูปแบบที่สอดคล้องกับ RFC 2047"""
            encoded_bytes = base64.b64encode(text.encode("utf-8"))
            encoded_str = encoded_bytes.decode("utf-8")
            return f"=?utf-8?B?{encoded_str}?="

        log.info("เริ่มบริการ Ntfy")
        priority = "3"
        if not self.push_config.get("NTFY_PRIORITY"):
            log.info("NTFY_PRIORITY ของบริการ Ntfy ไม่ได้ตั้งค่า!! ตั้งค่าเริ่มต้นเป็น 3")
        else:
            priority = self.push_config.get("NTFY_PRIORITY")

        # เข้ารหัส title โดยใช้ RFC 2047
        encoded_title = encode_rfc2047(title)

        data = content.encode(encoding="utf-8")
        headers = {"Title": encoded_title, "Priority": priority}  # ใช้ title ที่เข้ารหัสแล้ว

        url = self.push_config.get("NTFY_URL") + "/" + self.push_config.get("NTFY_TOPIC")
        response = requests.post(url, data=data, headers=headers)
        if response.status_code == 200:  # ใช้ response.status_code ในการตรวจสอบ
            log.info("ส่ง Ntfy สำเร็จ!")
        else:
            log.error(f"ส่ง Ntfy ล้มเหลว! ข้อผิดพลาด: {response.text}")


    def wxpusher_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ WxPusher
        ตัวแปรสภาพแวดล้อมที่รองรับ:
        - WXPUSHER_APP_TOKEN: appToken
        - WXPUSHER_TOPIC_IDS: ID หัวข้อ, หลายรายการคั่นด้วยเครื่องหมายอัฒภาค;
        - WXPUSHER_UIDS: ID ผู้ใช้, หลายรายการคั่นด้วยเครื่องหมายอัฒภาค;
        """

        url = "https://wxpusher.zjiecode.com/api/send/message"

        # ประมวลผล topic_ids และ uids, แปลงสตริงที่คั่นด้วยเครื่องหมายอัฒภาคเป็นอาร์เรย์
        topic_ids = []
        if self.push_config.get("WXPUSHER_TOPIC_IDS"):
            topic_ids = [
                int(id.strip())
                for id in self.push_config.get("WXPUSHER_TOPIC_IDS").split(";")
                if id.strip()
            ]

        uids = []
        if self.push_config.get("WXPUSHER_UIDS"):
            uids = [
                uid.strip()
                for uid in self.push_config.get("WXPUSHER_UIDS").split(";")
                if uid.strip()
            ]

        # topic_ids และ uids ต้องมีอย่างน้อยหนึ่งอย่าง
        if not topic_ids and not uids:
            log.info("WXPUSHER_TOPIC_IDS และ WXPUSHER_UIDS ของบริการ wxpusher ต้องตั้งค่าอย่างน้อยหนึ่งอย่าง!!")
            return

        log.info("เริ่มบริการ wxpusher")

        data = {
            "appToken": self.push_config.get("WXPUSHER_APP_TOKEN"),
            "content": f"<h1>{title}</h1><br/><div style='white-space: pre-wrap;'>{content}</div>",
            "summary": title,
            "contentType": 2,
            "topicIds": topic_ids,
            "uids": uids,
            "verifyPayType": 0,
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(url=url, json=data, headers=headers).json()

        if response.get("code") == 1000:
            log.info("ส่ง wxpusher สำเร็จ!")
        else:
            log.error(f"ส่ง wxpusher ล้มเหลว! ข้อผิดพลาด: {response.get('msg')}")


    def parse_headers(self, headers) -> dict:
        if not headers:
            return {}

        parsed = {}
        lines = headers.split("\n")

        for line in lines:
            i = line.find(":")
            if i == -1:
                continue

            key = line[:i].strip().lower()
            val = line[i + 1 :].strip()
            parsed[key] = parsed.get(key, "") + ", " + val if key in parsed else val

        return parsed


    def parse_string(self, input_string, value_format_fn=None) -> dict:
        matches = {}
        pattern = r"(\w+):\s*((?:(?!\n\w+:).)*)"
        regex = re.compile(pattern)
        for match in regex.finditer(input_string):
            key, value = match.group(1).strip(), match.group(2).strip()
            try:
                value = value_format_fn(value) if value_format_fn else value
                json_value = json.loads(value)
                matches[key] = json_value
            except:
                matches[key] = value
        return matches


    def parse_body(self, body, content_type, value_format_fn=None) -> str:
        if not body or content_type == "text/plain":
            return value_format_fn(body) if value_format_fn and body else body

        parsed = self.parse_string(body, value_format_fn)

        if content_type == "application/x-www-form-urlencoded":
            data = urllib.parse.urlencode(parsed, doseq=True)
            return data

        if content_type == "application/json":
            data = json.dumps(parsed)
            return data

        return parsed


    def custom_notify(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        ส่งข้อความโดยใช้ Custom Notification
        """

        log.info("เริ่มบริการ Custom Notification")

        url = self.push_config.get("WEBHOOK_URL")
        method = self.push_config.get("WEBHOOK_METHOD")
        content_type = self.push_config.get("WEBHOOK_CONTENT_TYPE")
        body = self.push_config.get("WEBHOOK_BODY")
        headers = self.push_config.get("WEBHOOK_HEADERS")

        if "$title" not in url and "$title" not in body:
            log.info("ส่วนหัวหรือเนื้อหาคำขอต้องมี $title และ $content")
            return

        headers = self.parse_headers(headers)
        body = self.parse_body(
            body,
            content_type,
            lambda v: v.replace("$title", title.replace("\n", "\\n")).replace(
                "$content", content.replace("\n", "\\n")
            ),
        )
        formatted_url = url.replace(
            "$title", urllib.parse.quote_plus(title)
        ).replace("$content", urllib.parse.quote_plus(content))
        response = requests.request(
            method=method, url=formatted_url, headers=headers, timeout=15, data=body
        )

        if response.status_code == 200:
            log.info("ส่ง Custom Notification สำเร็จ!")
        else:
            log.error(f"ส่ง Custom Notification ล้มเหลว! {response.status_code} {response.text}")


    def add_notify_function(self) -> list:
        notify_function = []
        if self.push_config.get("BARK_PUSH"):
            notify_function.append(self.bark)
        if self.push_config.get("CONSOLE"):
            notify_function.append(self.console)
        if self.push_config.get("DD_BOT_TOKEN") and self.push_config.get("DD_BOT_SECRET"):
            notify_function.append(self.dingding_bot)
        if self.push_config.get("FS_KEY"):
            notify_function.append(self.feishu_bot)
        if self.push_config.get("ONEBOT_URL"):
            notify_function.append(self.one_bot)
        if self.push_config.get("GOTIFY_URL") and self.push_config.get("GOTIFY_TOKEN"):
            notify_function.append(self.gotify)
        if self.push_config.get("IGOT_PUSH_KEY"):
            notify_function.append(self.iGot)
        if self.push_config.get("SERVERCHAN_PUSH_KEY"):
            notify_function.append(self.serverchan)
        if self.push_config.get("DEER_KEY"):
            notify_function.append(self.pushdeer)
        if self.push_config.get("CHAT_URL") and self.push_config.get("CHAT_TOKEN"):
            notify_function.append(self.chat)
        if self.push_config.get("PUSH_PLUS_TOKEN"):
            notify_function.append(self.pushplus_bot)
        if self.push_config.get("WE_PLUS_BOT_TOKEN"):
            notify_function.append(self.weplus_bot)
        if self.push_config.get("QMSG_KEY") and self.push_config.get("QMSG_TYPE"):
            notify_function.append(self.qmsg_bot)
        if self.push_config.get("QYWX_AM"):
            notify_function.append(self.wecom_app)
        if self.push_config.get("QYWX_KEY"):
            notify_function.append(self.wecom_bot)
        if self.push_config.get("DISCORD_BOT_TOKEN") and self.push_config.get("DISCORD_USER_ID"):
            notify_function.append(self.discord_bot)
        if self.push_config.get("TG_BOT_TOKEN") and self.push_config.get("TG_USER_ID"):
            notify_function.append(self.telegram_bot)
        if (
            self.push_config.get("AIBOTK_KEY")
            and self.push_config.get("AIBOTK_TYPE")
            and self.push_config.get("AIBOTK_NAME")
        ):
            notify_function.append(self.aibotk)
        if (
            self.push_config.get("SMTP_SERVER")
            and self.push_config.get("SMTP_SSL")
            and self.push_config.get("SMTP_EMAIL")
            and self.push_config.get("SMTP_PASSWORD")
            and self.push_config.get("SMTP_NAME")
        ):
            notify_function.append(self.smtp)
        if self.push_config.get("PUSHME_KEY"):
            notify_function.append(self.pushme)
        if (
            self.push_config.get("CHRONOCAT_URL")
            and self.push_config.get("CHRONOCAT_QQ")
            and self.push_config.get("CHRONOCAT_TOKEN")
        ):
            notify_function.append(self.chronocat)
        if self.push_config.get("WEBHOOK_URL") and self.push_config.get("WEBHOOK_METHOD"):
            notify_function.append(self.custom_notify)
        if self.push_config.get("NTFY_TOPIC"):
            notify_function.append(self.ntfy)
        if self.push_config.get("WXPUSHER_APP_TOKEN") and (
            self.push_config.get("WXPUSHER_TOPIC_IDS") or self.push_config.get("WXPUSHER_UIDS")
        ):
            notify_function.append(self.wxpusher_bot)
        if not notify_function:
            log.info(f"ไม่มีช่องทางการแจ้งเตือน โปรดตรวจสอบว่าการตั้งค่าการแจ้งเตือนถูกต้องหรือไม่")
        return notify_function


    def send(self, content: str, image: Optional[BytesIO] = None, test_method: Optional[str] = None) -> None:

        for config_key in self.push_config:
            config_value = getattr(self.ctx.push_config, config_key.lower(), None)
            if config_value is None:
                continue
            if test_method and test_method not in config_key:
                continue
            self.push_config[config_key] = config_value

        title = self.ctx.push_config.custom_push_title

        notify_function = self.add_notify_function()
        ts = [
            threading.Thread(target=mode, args=(title, content, image), name=mode.__name__)
            for mode in notify_function
        ]
        [t.start() for t in ts]
        [t.join() for t in ts]


def main():
    Push.send("content")

if __name__ == "__main__":
    main()
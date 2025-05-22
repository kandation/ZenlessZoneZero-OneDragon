from typing import Tuple

import cv2
import numpy as np
from cv2.typing import MatLike


def scale_input_image_u(image: MatLike, onnx_input_width: int, onnx_input_height: int) -> Tuple[np.ndarray, int, int]:
    """
    ปรับขนาดรูปภาพตามแนวทางของ ultralytics ให้เป็นขนาดที่โมเดลใช้
    อ้างอิงจาก https://github.com/orgs/ultralytics/discussions/6994?sort=new#discussioncomment-8382661
    :param image: รูปภาพอินพุต ช่อง RBG
    :param onnx_input_width: ความกว้างของรูปภาพที่โมเดลต้องการ
    :param onnx_input_height: ความสูงของรูปภาพที่โมเดลต้องการ
    :return: รูปภาพที่ปรับขนาดแล้ว ช่อง RGB
    """
    img_height, img_width = image.shape[:2]

    # ปรับขนาดรูปภาพให้พอดีกับด้านที่สั้นกว่าของขนาดอินพุตของโมเดล
    min_scale = min(onnx_input_height / img_height, onnx_input_width / img_width)

    # ขนาดก่อนการ padding
    scale_height = int(round(img_height * min_scale))
    scale_width = int(round(img_width * min_scale))

    # ปรับขนาดไปที่ขนาดเป้าหมาย
    if onnx_input_height != img_height or onnx_input_width != img_width:  # จำเป็นต้องปรับขนาด
        input_img = np.full(shape=(onnx_input_height, onnx_input_width, 3),
                            fill_value=114, dtype=np.uint8)
        scale_img = cv2.resize(image, (scale_width, scale_height), interpolation=cv2.INTER_LINEAR)
        input_img[0:scale_height, 0:scale_width, :] = scale_img
    else:
        input_img = image

    # การประมวลผลขั้นสุดท้ายหลังการปรับขนาด
    input_img = input_img / 255.0
    input_img = input_img.transpose(2, 0, 1)
    input_tensor = input_img[np.newaxis, :, :, :].astype(np.float32)

    return input_tensor, scale_height, scale_width
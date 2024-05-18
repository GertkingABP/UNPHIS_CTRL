import cv2
import time
import numpy as np
import ModuleHandTracking as htm
import math
import wmi

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import _ctypes

cap = cv2.VideoCapture(0)

pTime = 0
vol = 0
brightness = 0

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

detector = htm.handDetector(maxHands=2, detectionCon=0.7)
c = wmi.WMI(namespace='wmi')

def set_brightness(level):
    brightness = int(level * 100)  # Преобразование в проценты
    methods = c.WmiMonitorBrightnessMethods()[0]
    methods.WmiSetBrightness(brightness, 0)

def get_system_brightness():
    return c.WmiMonitorBrightness()[0].CurrentBrightness / 100

# Определим прямоугольник для изменения громкости
control_area_height = 200
control_area_top = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) - control_area_height
control_area = (0, int(control_area_top), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) // 3), int(control_area_top + control_area_height))

# Определим прямоугольник для изменения яркости
brightness_area_height = 200
brightness_area_top = 0
brightness_area = (0, brightness_area_top, int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) // 3), brightness_area_height)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = detector.findHands(frame)
    lmlist = detector.findPosition(frame, draw=False)
    if len(lmlist) != 0:
        x1, y1 = lmlist[4][1], lmlist[4][2]
        x2, y2 = lmlist[8][1], lmlist[8][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        length = math.hypot(x2 - x1, y2 - y1)

        if control_area[0] < cx < control_area[2] and control_area[1] < cy < control_area[3] and \
            control_area[0] < x1 < control_area[2] and control_area[1] < y1 < control_area[3] and \
            control_area[0] < x2 < control_area[2] and control_area[1] < y2 < control_area[3]:
            vol = np.interp(length, [20, 170], [0, 1])  # Преобразование длины в диапазон от 0 до 1
            volume.SetMasterVolumeLevelScalar(vol, None)

            if length < 10:
                cv2.circle(frame, (cx, cy), 15, (0, 255, 0), cv2.FILLED)  # 0%

            if length > 160:
                cv2.circle(frame, (cx, cy), 15, (0, 0, 255), cv2.FILLED)  # 100%

            # Отрисовка линии между указательным и большим пальцами
            cv2.line(frame, (x1, y1), (x2, y2), (10, 80, 255), 3)

        if brightness_area[0] < cx < brightness_area[2] and brightness_area[1] < cy < brightness_area[3] and \
            brightness_area[0] < x1 < brightness_area[2] and brightness_area[1] < y1 < brightness_area[3] and \
            brightness_area[0] < x2 < brightness_area[2] and brightness_area[1] < y2 < brightness_area[3]:
            brightness = np.interp(length, [20, 170], [0, 1])  # Преобразование длины в диапазон яркости
            set_brightness(brightness)

            if length < 10:
                cv2.circle(frame, (cx, cy), 15, (0, 255, 0), cv2.FILLED)  # 0%

            if length > 160:
                cv2.circle(frame, (cx, cy), 15, (0, 0, 255), cv2.FILLED)  # 100%

            # Отрисовка линии между указательным и большим пальцами
            cv2.line(frame, (x1, y1), (x2, y2), (10, 80, 255), 3)

    # Рисуем рамки для отображения зон, где надо показывать жест
    cv2.rectangle(frame, (control_area[0], control_area[1]), (control_area[2], control_area[3]), (105, 80, 165), 2)
    cv2.rectangle(frame, (brightness_area[0], brightness_area[1]), (brightness_area[2], brightness_area[3]), (0, 255, 255), 2)

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    mirrored_frame = cv2.flip(frame, 1)
    cv2.putText(mirrored_frame, f'FPS:{int(fps)}', (18, 32), cv2.FONT_HERSHEY_TRIPLEX, 1, (20, 255, 155), 1)

    try:
        vol_percentage = round(volume.GetMasterVolumeLevelScalar() * 100)
    except _ctypes.COMError as e:
        # Обработка ошибки
        print("Ошибка при получении уровня громкости:", e)
    cv2.rectangle(mirrored_frame, (610, 327), (635, 427), (105, 80, 165), 4)  # 0-100
    cv2.rectangle(mirrored_frame, (610, 427 - vol_percentage), (635, 427), (20, 255, 155), cv2.FILLED)  # 0-100
    cv2.putText(mirrored_frame, f'Volume:{vol_percentage}%', (455, 472), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (105, 80, 165), 2)

    # Обновляем значение ползунка яркости с учетом системной яркости
    system_brightness = get_system_brightness()
    brightness_percentage = round(system_brightness * 100)  # Преобразование яркости в проценты
    cv2.rectangle(mirrored_frame, (610, 47), (635, 147), (0, 255, 255), 4)  # 0-100
    cv2.rectangle(mirrored_frame, (610, 147 - brightness_percentage), (635, 147), (20, 255, 155), cv2.FILLED)  # 0-100
    cv2.putText(mirrored_frame, f'Brightness:{brightness_percentage}%', (435, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    cv2.imshow("Hand Control", mirrored_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()




import cv2
import numpy as np
import ModuleHandTracking as htm
import time
from pynput.mouse import Button, Controller
import ctypes

wCam, hCam = 1280, 720

user32 = ctypes.windll.user32
wScr, hScr = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

frameReduction = int(wCam * 0.12)

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

mouse = Controller()
smoothening, click_smoother = 7, 0
pLocX, pLocY, cLocX, cLocY = 0, 0, 0, 0
RMB_pressed, LMB_pressed = False, False

pTime = 0
cTime = 0

detector = htm.handDetector(maxHands=1)

# Добавление переменных для отслеживания стабильности позы пальцев
stable_pose_frames = 0
required_stable_frames = 10

while True:
    # Поиск суставов руки
    ret, frame = cap.read()
    frame = detector.findHands(frame)
    lmlist = detector.findPosition(frame, draw=False)

    # Получение конца указательного, среднего и большого пальцев
    if len(lmlist) != 0:
        x0, y0 = lmlist[4][1:]
        x1, y1 = lmlist[8][1:]
        x2, y2 = lmlist[12][1:]

        # Проверка поднятых пальцев
        fingers = detector.fingersUp()
        cv2.rectangle(frame, (frameReduction, frameReduction),
                      ((wCam - frameReduction), (hCam - frameReduction)),
                      (255, 0, 255), 2)
        print(fingers)


        # Если только открыт указательный - движение курсора
        if fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0:


            # Конвертирование координат
            x3 = np.interp(x1, (frameReduction, (wCam - frameReduction)), (0, wScr))
            y3 = np.interp(y1, (frameReduction, (hCam - frameReduction)), (0, hScr))

            # Сглаживание значений
            cLocX = pLocX + (x3 - pLocX) / smoothening
            cLocY = pLocY + (y3 - pLocY) / smoothening

            # Движение мышью
            mouse.position = (wScr - cLocX, cLocY)
            cv2.circle(frame, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            pLocX, pLocY = cLocX, cLocY

            # Сглаживание кликов
            if click_smoother >= 30:
                RMB_pressed, LMB_pressed = False, False
            click_smoother += 1

        # Если только открыты указательный и средний - клик
        if fingers[1] == 1 and fingers[2] == 1:

            # Нахождение расстояния между пальцами(Index and Middle пальцы)
            lenghtIM, frame, lineIndoIM = detector.findDistance(8, 12, frame)
            # Нахождение расстояния между пальцами(Middle and Ring(безымянный) пальцы)
            lenghtMR, frame, lineIndoMR = detector.findDistance(12, 16, frame)

            # Если расстояние короткое между средним и безымянным пальцем - совершение клика ПКМ
            if RMB_pressed == False and fingers[3] == 1 and lenghtMR < 65 and lenghtIM < 65:
                cv2.circle(frame, (lineIndoIM[4], lineIndoIM[5]),
                       15, (0, 255, 255), cv2.FILLED)
                cv2.circle(frame, (lineIndoMR[4], lineIndoMR[5]),
                           15, (0, 255, 255), cv2.FILLED)
                mouse.click(Button.right, 1)
                RMB_pressed, LMB_pressed = True, False

            # Если расстояние короткое между указательным и средним пальцем - совершение клика ЛКМ
            elif LMB_pressed == False and lenghtIM < 65:
                cv2.circle(frame, (lineIndoIM[4], lineIndoIM[5]),
                       15, (0, 255, 0), cv2.FILLED)
                mouse.click(Button.left, 1)
                RMB_pressed, LMB_pressed = False, True
            click_smoother = 0

        # Скролинг мышки
        if fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0:
            cv2.circle(frame, (x0, y0), 15, (255, 0, 0), cv2.FILLED)
            if fingers[0] == 0:
                mouse.scroll(0, 1.5)
            else:
                mouse.scroll(0, -1.5)

    # Отображение кадров и картинки
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    mirrored_frame = cv2.flip(frame, 1)
    cv2.putText(mirrored_frame, f'FPS:{int(fps)}', (518, 32), cv2.FONT_HERSHEY_TRIPLEX, 1, (20, 255, 155), 1)
    cv2.imshow('Hand Virtual Mouse', mirrored_frame)
    cv2.waitKey(1)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


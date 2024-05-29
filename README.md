# `Программа UNPHIS CTRL для управления ПК жестами и голосом`
## ***1. Описание***
Приложение позвояет управлять яркостью, громкостью компьютера, воспроизводимым аудио/видео файлом, мышью и запускать некоторые базовые службы и программы(например, браузер, диспетчер задач и так далее).

## *2. Использованные технологии*
Данная система создана с использованием языка Python 3.10, IDE PyCharm Community Edition PyCharm Community Edition 2022.1.2.
### Основные библиотеки: 
+ customtkinter для интерфейса;
+ cv2, YOLO, MediaPipe, для распознавания жестов;
+ speech_recognition для распознавания речи
+ pyautogui, keyboard, pyinput для использования функций клавиатуры, мыши и системных комбинаций
+ pycaw, mss, wmi для изменения настроек звука и яркости
Все остальные библиотеки представлены в программном коде main.py.
## *3. Требования для работы программы*
Должен быть ПК на ОС Windows(минимальная версия: Windows 7), с характеристиками, не ниже следующих:
+ процессор(CPU) с 4 ядрами и частотой 2 GHz;
+ оперативная память(RAM) 8 Gb;
+ видеокарта(GPU) встроенная или дискретная
+ встроенная или подключаемая камера с микрофоном и звуковой картой

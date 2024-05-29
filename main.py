#--------------------------------------------------------ВЫЗОВЫ МОДУЛЕЙ ОТДЕЛЬНО---------------------------------------------------------#
# import ModuleHandTracking
# import ModuleHandVolumeControl
# import ModuleHandBrightnessControl
# import ModuleSoundAndBrightnessControl
# import ModuleHandMouseControl
# import ModuleYoloModel
# import TestYolo

#----------------------------------------------------------------БИБЛИОТЕКИ----------------------------------------------------------------#
import ModuleHandTracking as mht
import customtkinter
import tkinter as tk
from tkinter import Button
import os
import time
import numpy as np
import random
import math
import cv2
from PIL import Image, ImageTk
import wmi
from ctypes import cast, POINTER
import _ctypes
from pynput.mouse import Button, Controller
import ctypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ultralytics import YOLO
import pyautogui
from mss import mss
import pygetwindow
import keyboard
import speech_recognition as sr
import subprocess
import webbrowser
import sys

#--------------------------------------ИНИЦИАЛИЗАЦИЯ ПРОГРАММОЙ АУДИО ПК И МОДЕЛИ YOLOv8 И ТЕМЫ UI--------------------------------------#
customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
c = wmi.WMI(namespace='wmi')

#------Файл с классами модели Yolo------#
my_file = open("asl_gestures_classes.txt", "r")
data = my_file.read()
class_list = data.split("\n")
my_file.close()

# print(class_list)

#--------Генерация случайного цвета рамки обнаруженного жеста class list--------#
detection_colors = []
for i in range(len(class_list)):
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    detection_colors.append((b, g, r))

#----------ЗАГРУЗКА ПРЕДОБУЧЕННО МОДЕЛИ YOLOV8N----------#
model = YOLO("best40.pt", "v8")

#-------------------------------------------КЛАСС ПРИЛОЖЕНИЯ(ПОТОМ РАЗДЕЛИТЬ НА НЕСКОЛЬКО КЛАССОВ)-------------------------------------------#
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        #------Размеры окна и название------#
        self.title("Unphis Ctrl")
        self.geometry("1200x600")

        #grid layout 1x2
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)

        #--------Загрузка иконок в зависимости от темы интерфейса--------#
        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_images")
        self.logo_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "icon.png")), size=(40, 40))
        self.gestures_info_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "info_gestures.png")),
                                                       size=(300, 150))

        self.large_test_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "home_fon_text_only.png")), size=(500, 150))
        self.image_icon_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "image_icon_light.png")), size=(20, 20))
        self.home_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "home_dark.png")), dark_image=Image.open(os.path.join(image_path, "home_light.png")), size=(20, 20))
        self.settings_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "settings20_light_theme.png")), dark_image=Image.open(os.path.join(image_path, "settings20_dark_theme.png")), size=(20, 20))
        self.info_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "info20_light_theme.png")), dark_image=Image.open(os.path.join(image_path, "info20_dark_theme.png")), size=(20, 20))

        #-------Создание навигационного фрейма слева-------#
        self.navigation_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1)

        #----------label-приветствие----------#
        random_number = random.randint(0, 4)
        if random_number == 0:
            logo_text = "Добро пожаловать"
        elif random_number == 1:
            logo_text = "Приветствую :)"
        elif random_number == 2:
            logo_text = " Используется камера и микрофон"
        elif random_number == 3:
            logo_text = "Система готова"
        else:
            logo_text = "С возвращением!"

        self.navigation_frame_label = customtkinter.CTkLabel(self.navigation_frame, text=" " + logo_text, image=self.logo_image, compound="left", font=customtkinter.CTkFont(size=15, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Главная", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), image=self.home_image, anchor="w", command=self.home_button_event)
        self.home_button.grid(row=1, column=0, sticky="ew")

        self.frame_2_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Настройки", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), image=self.settings_image, anchor="w", command=self.frame_2_button_event)
        self.frame_2_button.grid(row=2, column=0, sticky="ew")

        self.frame_3_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Справка", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), image=self.info_image, anchor="w", command=self.frame_3_button_event)
        self.frame_3_button.grid(row=3, column=0, sticky="ew")

        #----------------------------------------------------------СОЗДАНИЕ ГЛАВНОГО РАЗДЕЛА----------------------------------------------------------#
        self.home_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_columnconfigure(0, weight=1)
        self.home_frame.grid_rowconfigure((0, 1), weight=1)
        self.home_frame.grid_rowconfigure(2, weight=0)

        self.home_frame_large_image_label = customtkinter.CTkLabel(self.home_frame, text="", image=self.large_test_image)
        self.home_frame_large_image_label.grid(row=0, column=0, padx=10, pady=10)

        self.video_label = customtkinter.CTkLabel(self.home_frame)
        self.video_label.grid(row=1, column=0, padx=(10, 10), pady=(10, 10), sticky="nsew")

        #---------------------------------------------------------СОЗДАНИЕ РАЗДЕЛА НАСТРОЕК---------------------------------------------------------#
        self.second_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.second_frame.grid_columnconfigure((0, 1), weight=1)  # Разделительные столбцы
        self.second_frame.grid_rowconfigure((0, 1, 4, 5), weight=1)  # Разделительные строки

        #-----------Масштаб-----------#
        self.scaling_label = customtkinter.CTkLabel(self.second_frame, text="Настройка масштаба:", anchor="w")
        self.scaling_label.grid(row=3, column=0, padx=(40, 0), pady=(0, 10), sticky="w")

        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.second_frame,
                                                               values=["Выберите масштаб", "75%", "100%", "125%", "150%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=3, column=1, padx=(0, 40), pady=(10, 20), sticky="ew")

        #-----------Тема-----------#
        self.appearance_mode_label = customtkinter.CTkLabel(self.second_frame, text="Настройка темы:", anchor="w")
        self.appearance_mode_label.grid(row=4, column=0, padx=(40, 0), pady=(0, 10), sticky="w")

        self.appearance_mode_menu = customtkinter.CTkOptionMenu(self.second_frame,
                                                                values=["Выберите тему", "Light", "Dark", "System"],
                                                                command=self.change_appearance_mode_event)
        self.appearance_mode_menu.grid(row=4, column=1, padx=(0, 40), pady=(10, 20), sticky="ew")

        #------------------------------------------------------СОЗДАНИЕ РАЗДЕЛА С ИНФОРМАЦИЕЙ------------------------------------------------------#
        self.third_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.third_frame.grid_columnconfigure(0, weight=1)
        self.third_frame.grid_columnconfigure(1, weight=1)
        self.third_frame.grid_columnconfigure(2, weight=1)

        self.appearance_mode_label = customtkinter.CTkLabel(self.third_frame, text="Как пользоваться программой",
                                                            anchor="center")
        self.appearance_mode_label.grid(row=0, column=1, padx=20, pady=(20, 20), sticky="nsew")

        self.textbox = customtkinter.CTkTextbox(self.third_frame, width=500)
        self.textbox.grid(row=1, column=1, padx=20, pady=(20, 20), sticky="nsew")
        self.textbox.insert("0.0",
                            "Программа Unphis ctrl имеет 5 режимов работы жестов:\n\n\n1) Режим мыши. Позволяет управлять курсором, нажимать ЛКМ/ПКМ, а также скролить страницы. Написан с использованием MediaPipe. Для управления водите указательным пальцем, соединив внизу остальные, для нажатия кнопок увеличивайте расстояние между указательным и средним, средним и безымянным, скролинг осуществляется с помощью большого пальца, если он влево, то скрол в одну сторону, вправо, соответственно, в другую сторону." +
                            "\n\n2) Режим модели Yolo. В этом режиме вы можете делать скриншот экрана, переключать/сворачивать заранее выбранное окно, вызывать диспетчер задач, нажимать пробел жестом. Используются статические жесты ASL(американского языка жестов), нейронная сеть написана с помощью предобученной на жесты модели YOLOv8n. Соответственно, жест С - сделать скришот, G - сворачивать/менять размеры текущего окна, R - вызвать диспетчер задач, X - пробел, Y - сменить окно(последние 2 жеста лучше использовать вместе)." +
                            "\n\n3) Режим плеера. Данный модуль позволит вам управлять воспроизводимыми видео или аудио(пауза/воспроизведение, беззвучный режим устройства, следующий и предыдущий трек, а также настройка уровня громкости компьютера). Жесты анализируются с помощью MediaPipe. Для настройки громкости поместите руку в специальную рамку, чтобы кисть полностью находилась внутри, и, меняя расстояние между указательным и большим пальцами, выставляйте необходимый уровень громкости. Для включения беззвучного режима и остальных жестов нужно поместить руку в левую рамку, для режима без звука - поднять все пальцы, кроме безымянного и большого(жест шокер), для паузы/воспроизведения трека поднимите только мизинец и держите к верху, а все остальные пальцы в кулак, для выбора следующего следующего/предыдущего трека используются жесты L и W(они есть в жестах ASL), L - только указательный и большой пальцы прямые, W - вытянуты вверх прямо только указательный, средний и безымянный пальцы." +
                            "\n\n4)Режим яркости. Работает, как и регулировка громкости, рамка расположена в том же месте." +
                            "\n\n5)Режим без жестов. Видеопоток не анализируется никакими библиотеками, режим для отключения жестов, если они вам не нужны." +
                            "\n\n\nЧтобы переключаться между режимами, вы можете зайти в настройки для выбора нужного режима(в этом же разделе есть выбор темы и масштаба окна). Также режимы переключаются через клавиши 1-5. Ещё один способ - с помощью голосовых команд через кнопку, расположенную в главном разделе, нужно произносить для того, чтобы выбрать: 1 режим - \"мышь\", 2 режим - \"сеть\", 3 режим - \"плеер\", 4 режим - \"яркость\", 5 режим - \"без жестов\"." +
                            "\n\nКнопка голоса также содержит собственные функции: запуск браузера - \"интернет\", открыть проводник - \"проводник\", ножницы, блокнот, калькулятор, paint вызываются одноимённо. Чтобы выйти из программы голосом, можно сказать \"выключить\". Чтобы выполнить аудиокоманду, нажмите на кнопку, скажите команду, затем она при распознании выполнится, в противном случае ничего не произойдёт, поэтому говорите чётко и не ниже среднего по громкости речи. Кнопка работает в любом режиме жестов, но требует подключения к интернету, поскольку использует модель языка от Google." +
                            "\n\n\nНиже представлены иллюстрации жестов из ASL и остальные.")

        # Центрируем текстовый блок
        self.textbox.grid_configure(sticky="nsew")

        self.third_frame_large_image_label = customtkinter.CTkLabel(self.third_frame, text="",
                                                                    image=self.gestures_info_image)
        self.third_frame_large_image_label.grid(row=2, column=1, padx=20, pady=20, sticky="nsew")

        # Настройка строк и столбцов для растягивания
        #self.third_frame.grid_rowconfigure((0, 1, 2), weight=1)
        self.third_frame.grid_columnconfigure((0, 1, 2), weight=1)

        #-----Выбор главного раздела при старте программы-----#
        self.select_frame_by_name("Главная")

        self.create_voice_control_button()

        #----------Захват видео с камеры----------#
        self.cap = cv2.VideoCapture(0)
        self.frame_count = 0

        #----------Инициализация детектора MediaPipe----------#
        self.detector = mht.handDetector()

        #---------Режим по умолчанию---------#
        self.mode = 3

        #-----Запуск метода анализа видеопотока на жесты-----#
        self.show_video_stream()

        #---------Создаем и добавляем радиокнопки---------#
        self.add_radio_buttons()

        #---------Обработчик событий нажатия клавиатуры---------#
        self.start_keyboard_listener()

    #---------------------------------------МЕТОДЫ ДЛЯ ИНТЕРФЕЙСА---------------------------------------#

    #-------------------------------РАЗДЕЛ РАДИОКНОПОК ДЛЯ СМЕНЫ РЕЖИМОВ-------------------------------#
    def add_radio_buttons(self):
        self.radio_frame = customtkinter.CTkFrame(master=self.second_frame, fg_color="transparent")
        self.radio_frame.grid(row=1, column=0, columnspan=2, padx=40, pady=(10, 10), sticky="nsew")

        self.label_radio_group = customtkinter.CTkLabel(master=self.radio_frame, text="Режим работы жестов")
        self.label_radio_group.pack(side="top", pady=(0, 10))

        # Используем IntVar для хранения выбранной радиокнопки
        self.radio_var = tk.IntVar(value=self.mode)

        self.radio_button_1 = customtkinter.CTkRadioButton(master=self.radio_frame, variable=self.radio_var, value=1,
                                                           text="Режим мыши")
        self.radio_button_1.pack(anchor="w", padx=10, pady=(0, 10))  # Увеличение расстояния по вертикали

        self.radio_button_2 = customtkinter.CTkRadioButton(master=self.radio_frame, variable=self.radio_var, value=2,
                                                           text="Режим модели Yolo")
        self.radio_button_2.pack(anchor="w", padx=10, pady=(0, 10))  # Увеличение расстояния по вертикали

        self.radio_button_3 = customtkinter.CTkRadioButton(master=self.radio_frame, variable=self.radio_var, value=3,
                                                           text="Режим плеера MP")
        self.radio_button_3.pack(anchor="w", padx=10, pady=(0, 10))  # Увеличение расстояния по вертикали

        self.radio_button_4 = customtkinter.CTkRadioButton(master=self.radio_frame, variable=self.radio_var, value=4,
                                                           text="Режим для яркости")
        self.radio_button_4.pack(anchor="w", padx=10, pady=(0, 10))  # Увеличение расстояния по вертикали

        self.radio_button_5 = customtkinter.CTkRadioButton(master=self.radio_frame, variable=self.radio_var, value=5,
                                                           text="Режим без жестов")
        self.radio_button_5.pack(anchor="w", padx=10, pady=(0, 10))  # Увеличение расстояния по вертикали

        # Привязываем обработчик событий к радиокнопкам
        self.radio_var.trace_add("write", self.on_radio_button_change)

    #-------Переключение режимов по клавишам-------#
    def handle_keyboard_event(self, event):
        key = event.char
        if key.isdigit():
            mode = int(key)
            if mode in [1, 2, 3, 4, 5]:
                self.mode = mode
                self.radio_var.set(mode)
                print("Установлен режим", self.mode)

    def start_keyboard_listener(self):
        # Привязываем обработчик событий клавиатуры к корневому окну
        self.bind('<Key>', self.handle_keyboard_event)

    def select_frame_by_name(self, name):
        if name == "Главная":
            self.home_button.configure(text_color=("navy", "dodger blue"))
            self.frame_2_button.configure(text_color=("gray60", "gray40"))
            self.frame_3_button.configure(text_color=("gray60", "gray40"))
        elif name == "Настройки":
            self.home_button.configure(text_color=("gray60", "gray40"))
            self.frame_2_button.configure(text_color=("navy", "dodger blue"))
            self.frame_3_button.configure(text_color=("gray60", "gray40"))
        elif name == "Справка":
            self.home_button.configure(text_color=("gray60", "gray40"))
            self.frame_2_button.configure(text_color=("gray60", "gray40"))
            self.frame_3_button.configure(text_color=("navy", "dodger blue"))

        #-----------Показать выбранный раздел-----------#
        if name == "Главная":
            self.home_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.home_frame.grid_forget()
        if name == "Настройки":
            self.second_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.second_frame.grid_forget()
        if name == "Справка":
            self.third_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.third_frame.grid_forget()

    def home_button_event(self):
        self.selected_frame_name = "Главная"
        self.select_frame_by_name(self.selected_frame_name)

    def frame_2_button_event(self):
        self.selected_frame_name = "Настройки"
        self.select_frame_by_name(self.selected_frame_name)

    def frame_3_button_event(self):
        self.selected_frame_name = "Справка"
        self.select_frame_by_name(self.selected_frame_name)

    def change_appearance_mode_event(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        if new_scaling != "Выберите масштаб":
            new_scaling_float = int(new_scaling.replace("%", "")) / 100
            customtkinter.set_widget_scaling(new_scaling_float)

    def on_radio_button_change(self, *args):
        selected_value = self.radio_var.get()
        self.mode = selected_value
        if selected_value == 1:
            print("Установлен режим мыши")
        elif selected_value == 2:
            print("Установлен режим модели Yolo")
        elif selected_value == 3:
            print("Установлен режим плеера MP")
        elif selected_value == 4:
            print("Установлен режим настройки яркости")
        elif selected_value == 5:
            print("Установлен режим без жестов")

    #------Создание кнопки для голосового управления------#
    def create_voice_control_button(self):
        self.voice_control_button = customtkinter.CTkButton(self.home_frame, corner_radius=10, width=20, height=10,
                                                            border_spacing=20, text="Голос", fg_color="#00008B",
                                                            text_color=("gray10", "gray90"),
                                                            hover_color=("gray70", "gray30"), anchor="center",
                                                            command=self.start_voice_control)
        self.voice_control_button.grid(row=2, column=0, sticky="nsew")

    #------Запуск распознавания речи по кнопке------#
    def start_voice_control(self):
        self.recognize_speech()

#-------------------------------------------------ФУНКЦИИ ДЛЯ ГОЛОСА-------------------------------------------------#
    def voice_command_mode_switch(self, command):
        # Список команд для переключения режимов
        mode_commands = {
            "мышь": 1,
            "сеть": 2,
            "плеер": 3,
            "яркость": 4,
            "без жестов": 5
        }

        # Список дополнительных команд
        additional_commands = {
            "проводник": lambda: subprocess.Popen("explorer"),
            "интернет": lambda: webbrowser.open("https://www.google.com"),
            "блокнот": lambda: subprocess.Popen(["notepad"]),
            "калькулятор": lambda: subprocess.Popen(["calc"]),
            "paint": lambda: subprocess.Popen(["mspaint"]),
            "ножницы": lambda: subprocess.Popen(["snippingtool"]),
            "выключить": self.quit_program
        }

        if command in mode_commands:
            new_mode = mode_commands[command]
            self.mode = new_mode
            self.radio_var.set(new_mode)
            print(f"Установлен режим {command}")

        elif command in additional_commands:
            additional_commands[command]()
            print(f"Выполнена команда: {command}")
        else:
            print("Не удалось распознать команду для смены режима или выполнения действия")

    def quit_program(self):
        print("Программа будет закрыта.")
        self.destroy()
        sys.exit()

    def recognize_speech(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Скажите что-нибудь...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
        try:
            print("Распознавание...")
            text = recognizer.recognize_google(audio, language="ru-RU")
            print(f"Вы сказали: {text}")
            # После распознавания команды вызываем метод для переключения режима по голосу
            self.voice_command_mode_switch(text.lower())
        except sr.UnknownValueError:
            print("Извините, не удалось распознать речь")
        except sr.RequestError as e:
            print(f"Ошибка сервиса распознавания: {e}")

    def check_keyword(self, text, possible_keywords):
        for keyword in possible_keywords:
            if keyword in text:
                return keyword
        return None

#-------------------------------------МЕТОД ДЛЯ ВЫВОДА С КАМЕРЫ И ДЕЙСТВИЙ ЖЕСТОВ-------------------------------------#
    def show_video_stream(self):
        self.ret, self.frame = self.cap.read()
        self.mirrored_frame = cv2.flip(self.frame, 1)

        #---------------------ФУНКЦИИ ДЛЯ ЖЕСТОВ(В ТОМ ЧИСЛЕ И ДЛЯ YOLO)---------------------#

        def set_brightness(level):
            brightness = int(level * 100)  # Преобразование в проценты
            methods = c.WmiMonitorBrightnessMethods()[0]
            methods.WmiSetBrightness(brightness, 0)

        def get_system_brightness():
            return c.WmiMonitorBrightness()[0].CurrentBrightness / 100

        def enter():
            cv2.putText(self.mirrored_frame, "ENTER", (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 5)  # ENTER
            pyautogui.press('enter')
            time.sleep(1.5)

        def space():
            cv2.putText(self.mirrored_frame, "SPACE", (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 5)  # SPACE
            pyautogui.press('space')
            time.sleep(0.2)

        def backspace():
            cv2.putText(self.mirrored_frame, "Backspace", (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0),
                        5)  # BACKSPACE
            pyautogui.hotkey('backspace')
            time.sleep(0.2)

        # -----Диспетчер задач-----#
        def os_tasks():
            cv2.putText(self.mirrored_frame, "TASKS OF OS", (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0),
                        5)  # TASKS
            pyautogui.hotkey('ctrl', 'shift', 'esc')
            time.sleep(1.5)

        # ----Переключить окно-----#
        def windowSwitch():
            cv2.putText(self.mirrored_frame, "WINDOW SWITCH", (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0),
                        5)  # SWITCH WINDOW
            pyautogui.hotkey('ctrl', 'alt', 'tab')
            time.sleep(1.5)

        # ----Показать сделанный жестом скриншот-----#
        def showScr(imgName):
            img1 = Image.open(imgName)
            img1.show()

        # ----Сделать скриншот-----#
        def screenshot():
            cv2.putText(self.mirrored_frame, "MAKING SCREENSHOT", (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0),
                        5)  # SCREENSHOT
            filename = mss().shot()
            showScr("monitor-1.png")
            print(filename)
            time.sleep(1.5)

        #----Окно на минимум/максимум-----#
        def toggleWindow():
            active_window = pygetwindow.getActiveWindow()

            if active_window.isMaximized:
                active_window.minimize()
                cv2.putText(self.mirrored_frame, "MINIMIZE WINDOW", (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0),
                            5)
            else:
                active_window.maximize()
                cv2.putText(self.mirrored_frame, "MAXIMIZE WINDOW", (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0),
                            5)
            time.sleep(1.5)

        # -----Следующий трек-----#
        def next_track():
            active_window = pygetwindow.getActiveWindow()
            active_window.activate()
            cv2.putText(self.mirrored_frame, "NEXT TRACK", (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0),
                        5)  # BACKSPACE
            keyboard.send("next track")
            time.sleep(3)

        # -----Предыдущий трек-----#
        def previous_track():
            active_window = pygetwindow.getActiveWindow()
            active_window.activate()
            cv2.putText(self.mirrored_frame, "PREVIOUS TRACK", (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0),
                        5)  # BACKSPACE
            keyboard.send("previous track")
            time.sleep(3)

        # -----Воспроизведение/пауза трека-----#
        def play_pause_track():
            active_window = pygetwindow.getActiveWindow()
            active_window.activate()
            cv2.putText(self.mirrored_frame, "PLAY/PAUSE TRACK", (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 5)
            keyboard.send("play/pause")
            time.sleep(1.5)

        # -----Режим без звука/вкл/выкл-----#
        def muteUnmute():
            cv2.putText(self.mirrored_frame, "Mute/Unmute", (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0),
                        5)  # MUTE/UNMUTE
            pyautogui.press('volumemute')
            time.sleep(1.5)

        if self.ret:

            #-------------------------ЕСЛИ ВЫБРАН РЕЖИМ МЕДИА MP, ТО НА ВИДЕОПОТОКЕ ТАК-------------------------#

            #------РЕЖИМ БЕЗ АНАЛИЗА ЖЕСТОВ, НО ГОЛОС ДОСТУПЕН------#
            if self.mode == 5:
                cv2.putText(self.mirrored_frame, '------No gestures mode------', (25, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (55, 155, 255), 3)

            #-------------------------------ЕСЛИ РЕЖИМ ЯРКОСТИ-------------------------------#
            if self.mode == 4:
                # Определим прямоугольник для изменения яркости
                brightness_area_height = 400
                brightness_area_top = 80
                brightness_area_width = 250  # Ширина зоны яркости
                brightness_area = (
                int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) - brightness_area_width, brightness_area_top,
                int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), brightness_area_height)

                #-----Обнаружение руки-----#
                img_with_hands = self.detector.findHands(self.mirrored_frame)
                lmlist, _ = self.detector.findPosition(self.mirrored_frame, draw=False)

                if len(lmlist) != 0:
                    x1, y1 = lmlist[4][1], lmlist[4][2]
                    x2, y2 = lmlist[8][1], lmlist[8][2]
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    length = math.hypot(x2 - x1, y2 - y1)

                    #-----------------------------ДЛЯ ПРАВОЙ РАМКИ ЯРКОСТИ-----------------------------#
                    if brightness_area[0] < cx < brightness_area[2] and brightness_area[1] < cy < brightness_area[3] and \
                            brightness_area[0] < x1 < brightness_area[2] and brightness_area[1] < y1 < brightness_area[
                        3] and \
                            brightness_area[0] < x2 < brightness_area[2] and brightness_area[1] < y2 < brightness_area[
                        3]:
                        brightness = np.interp(length, [20, 170], [0, 1])  # Преобразование длины в диапазон яркости
                        set_brightness(brightness)

                        if length < 10:
                            cv2.circle(self.mirrored_frame, (cx, cy), 15, (0, 255, 0), cv2.FILLED)  # 0%

                        if length > 160:
                            cv2.circle(self.mirrored_frame, (cx, cy), 15, (0, 0, 255), cv2.FILLED)  # 100%

                        # ------Отрисовка линии между указательным и большим пальцами------#
                        cv2.line(self.mirrored_frame, (x1, y1), (x2, y2), (10, 80, 255), 3)

                cv2.rectangle(self.mirrored_frame, (brightness_area[0], brightness_area[1]),
                              (brightness_area[2], brightness_area[3]),
                              (0, 255, 255), 2)
                system_brightness = get_system_brightness()
                brightness_percentage = round(system_brightness * 100)  # Преобразование яркости в проценты
                cv2.rectangle(self.mirrored_frame, (610, 140), (635, 340), (0, 255, 255), 4)  # 0-100
                cv2.rectangle(self.mirrored_frame, (610, 340 - brightness_percentage*2), (635, 340), (255, 255, 255),
                              cv2.FILLED)  # 0-100
                cv2.putText(self.mirrored_frame, f'Brightness:{brightness_percentage}%', (425, 390),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 255, 255), 2)
                cv2.putText(self.mirrored_frame, '------Brightness mode------', (30, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (55, 155, 255), 3)

            #-------------------------------ЕСЛИ РЕЖИМ ПЛЕЕРА-------------------------------#
            if self.mode == 3:
                # Определяем прямоугольник для рамки gestures_area
                gesture_area_height = 320
                gesture_area_top = 60
                gesture_area_width = 250
                gesture_area_left = 0  # Отступ слева
                gesture_area_top = (int(self.cap.get(
                    cv2.CAP_PROP_FRAME_HEIGHT)) - gesture_area_height) // 2  # Центрирование по вертикали
                gesture_area_right = gesture_area_left + gesture_area_width  # Определяем правую границу
                gesture_area_bottom = gesture_area_top + gesture_area_height  # Определяем нижнюю границу
                gesture_area = (gesture_area_left, gesture_area_top, gesture_area_right, gesture_area_bottom)

                #---------Определим прямоугольник для изменения громкости---------#
                control_area_height = 400
                control_area_top = 80
                control_area_width = 250  # Ширина зоны громкости
                volume_control_area = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) - control_area_width, int(control_area_top),
                                       int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), control_area_height)

                pyautogui.FAILSAFE = False

                working1, working2, working3, working4, working5, working6 = False, False, False, False, False, False

                while not working1:
                    g1 = 1
                    working1 = True

                while not working2:
                    g2 = 2
                    working2 = True

                while not working3:
                    g3 = 3
                    working3 = True

                while not working4:
                    g4 = 4
                    working4 = True

                #-----Словарь медиакоманд-----#
                media_functions_dict = {
                    '1': previous_track,
                    '2': next_track,
                    '3': play_pause_track,
                    '4': muteUnmute
                }

                #-----Обнаружение руки-----#
                img_with_hands = self.detector.findHands(self.mirrored_frame)
                lmlist, _ = self.detector.findPosition(self.mirrored_frame, draw=False)

                if len(lmlist) != 0:
                    x1, y1 = lmlist[4][1], lmlist[4][2]
                    x2, y2 = lmlist[8][1], lmlist[8][2]
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    length = math.hypot(x2 - x1, y2 - y1)

                    #-----------------------------ДЛЯ ЛЕВОЙ РАМКИ РЕЖИМА ПЛЕЕРА-----------------------------#
                    if gesture_area[0] < cx < gesture_area[2] and gesture_area[1] < cy < gesture_area[3]:
                        handLandmarks = self.detector.findHandLandMarks(image=self.mirrored_frame, draw=False)

                        #------Анализ точек пальцев правой и левой рук для флагов пальцев жестов------#
                        if len(handLandmarks) != 0:

                            right_thumb = True if (
                                    handLandmarks[4][3] == "Right" and handLandmarks[4][1] > handLandmarks[3][1]) else False
                            right_index = True if (
                                    handLandmarks[4][3] == "Right" and handLandmarks[8][2] < handLandmarks[6][2]) else False
                            right_middle = True if (
                                    handLandmarks[4][3] == "Right" and handLandmarks[12][2] < handLandmarks[10][
                                2]) else False
                            right_ring = True if (
                                    handLandmarks[4][3] == "Right" and handLandmarks[16][2] < handLandmarks[14][
                                2]) else False
                            right_little = True if (
                                    handLandmarks[4][3] == "Right" and handLandmarks[20][2] < handLandmarks[18][
                                2]) else False

                            left_thumb = True if (
                                    handLandmarks[4][3] == "Left" and handLandmarks[8][2] < handLandmarks[6][2]) else False
                            left_index = True if (
                                    handLandmarks[4][3] == "Left" and handLandmarks[8][2] < handLandmarks[6][2]) else False
                            left_middle = True if (
                                    handLandmarks[4][3] == "Left" and handLandmarks[12][2] < handLandmarks[10][
                                2]) else False
                            left_ring = True if (
                                    handLandmarks[4][3] == "Left" and handLandmarks[16][2] < handLandmarks[14][
                                2]) else False
                            left_little = True if (
                                    handLandmarks[4][3] == "Left" and handLandmarks[20][2] < handLandmarks[18][
                                2]) else False

                            #------Сами вызовы функций из словаря действий------#
                            gesture_detected = False

                            #----Предыдущий трек через жест W, где вытянуты указательный, средний и безымянный пальцы----#
                            if (left_index and left_middle and left_ring and not left_little and not left_thumb) or (right_index and right_middle and right_ring and not right_little and not right_thumb):
                                if not gesture_detected:
                                    media_functions_dict[str(g1)]()
                                    gesture_detected = True
                                    print("Выполнено действие для жеста W")

                            #----Нажатие пробела через жест L, где вытянуты только большой и указательный пальцы----#
                            elif (left_thumb and left_index and not left_little and not left_ring and not left_middle) or (right_thumb and right_index and not right_little and not right_ring and not right_middle):
                                if not gesture_detected:
                                    media_functions_dict[str(g2)]()
                                    gesture_detected = True
                                    print("Выполнено действие для жеста L")

                            #----Нажатие паузы/воспроизведения через жест мизинца вверх, где все остальные пальцы согнуты----#
                            elif (not left_thumb and not left_index and left_little and not left_ring and not left_middle) or (not right_thumb and not right_index and right_little and not right_ring and not right_middle):
                                if not gesture_detected:
                                    media_functions_dict[str(g3)]()
                                    gesture_detected = True
                                    print("Выполнено действие для жеста мизинца вверх")

                            #----Беззвучный режим через жест, где прямые указательный, средний и мизинец пальцы----#
                            elif (not right_thumb and right_index and right_little and right_middle and not right_ring) or (not left_thumb and left_index and left_little and left_middle and not left_ring):
                                if not gesture_detected:
                                    media_functions_dict[str(g4)]()
                                    gesture_detected = True
                                    print("Выполнено действие для жеста, где прямые указательный, средний и мизинец пальцы")

                    #-----------------------------ДЛЯ ПРАВОЙ РАМКИ ЗВУКА РЕЖИМА МЕДИА MP-----------------------------#
                    if volume_control_area[0] < cx < volume_control_area[2] and volume_control_area[1] < cy < volume_control_area[3] and \
                            volume_control_area[0] < x1 < volume_control_area[2] and volume_control_area[1] < y1 < volume_control_area[3] and \
                            volume_control_area[0] < x2 < volume_control_area[2] and volume_control_area[1] < y2 < volume_control_area[3]:
                        vol = np.interp(length, [20, 170], [0, 1])  # Преобразование длины в диапазон от 0 до 1
                        volume.SetMasterVolumeLevelScalar(vol, None)

                        if length < 10:
                            cv2.circle(self.mirrored_frame, (cx, cy), 15, (0, 255, 0), cv2.FILLED)  # 0%

                        if length > 160:
                            cv2.circle(self.mirrored_frame, (cx, cy), 15, (0, 0, 255), cv2.FILLED)  # 100%

                        #------Отрисовка линии между указательным и большим пальцами------#
                        cv2.line(self.mirrored_frame, (x1, y1), (x2, y2), (10, 80, 255), 3)

                #------Рамки для отображения зон, где надо показывать жест------#
                cv2.rectangle(self.mirrored_frame, (int(gesture_area[0]), int(gesture_area[1])),
                              (int(gesture_area[2]), int(gesture_area[3])),
                              (255, 0, 0), 2)
                cv2.rectangle(self.mirrored_frame, (volume_control_area[0], volume_control_area[1]), (volume_control_area[2], volume_control_area[3]),
                              (112, 112, 112),
                              2)

                #------Установка начального значения vol_percentage------#
                vol_percentage = 0
                try:
                    vol_percentage = round(volume.GetMasterVolumeLevelScalar() * 100)
                except _ctypes.COMError as e:
                    #------Обработка ошибки------#
                    print("Ошибка при получении уровня громкости:", e)

                #----------Обновление значений ползунков яркости и громкости с учетом системных значений----------#
                cv2.rectangle(self.mirrored_frame, (610, 140), (635, 340), (112, 112, 112), 4)  # 0-100
                cv2.rectangle(self.mirrored_frame, (610, 340 - vol_percentage*2), (635, 340), (255, 255, 255), cv2.FILLED)  # 0-100
                cv2.putText(self.mirrored_frame, f'Volume:{vol_percentage}%', (435, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                            (112, 112, 112), 2)

                cv2.putText(self.mirrored_frame, 'Media gestures', (25, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                            (255, 255, 255), 2)

                cv2.putText(self.mirrored_frame, '------Mediaplayer mode------', (27, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (55, 155, 255), 3)

            #--------------------------------------РЕЖИМ РАБОТЫ НЕЙРОННОЙ СЕТИ--------------------------------------#
            if self.mode == 2:

                # ---------------ПРЕДСКАЗАНИЕ ЖЕСТОВ---------------#
                detect_params = model.predict(source=[self.mirrored_frame], conf=0.45, save=False)

                # -----Convert tensor array to numpy-----#
                DP = detect_params[0].numpy()

                if len(DP) != 0:
                    #for i in range(len(detect_params[0])):
                    boxes = detect_params[0].boxes
                    #box = boxes[i]  # Берем все по циклу
                    box = boxes[0]  # Берем только первый обнаруженный жест
                    clsID = box.cls.numpy()[0]
                    conf = box.conf.numpy()[0]
                    bb = box.xyxy.numpy()[0]

                    cv2.rectangle(
                        self.mirrored_frame,
                        (int(bb[0]), int(bb[1])),
                        (int(bb[2]), int(bb[3])),
                        detection_colors[int(clsID)],
                        3,
                    )

                    #----------ВЫВОД ИМЕНИ КЛАССА И ПРОЦЕНТА ОБНАРУЖЕННОГО ЖЕСТА В ПОТОКЕ----------#
                    font = cv2.FONT_HERSHEY_COMPLEX
                    class_name = class_list[int(clsID)]
                    confidence = round(conf, 3)
                    cv2.putText(
                        self.mirrored_frame,
                        f"{class_name} {str(round(conf*100, 3))}%",
                        (int(bb[0]), int(bb[1]) - 10),
                        font,
                        1,
                        (255, 0, 0),
                        2,
                    )

                    print(f"\n\n-------> Detected gesture {class_name} with {confidence * 100}% confidence")

                    if class_name == "C":
                        screenshot()
                    elif class_name == "G":
                        toggleWindow()
                    elif class_name == "R":
                        os_tasks()
                    elif  class_name == "X":
                        space()
                    elif class_name == "Y":
                        windowSwitch()

                cv2.putText(self.mirrored_frame, '-------NN Yolo mode-------', (30, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (55, 155, 255), 3)

            #---------------------------------------------РЕЖИМ РАБОТЫ МЫШИ---------------------------------------------#
            if self.mode == 1:
                wCam, hCam = 640, 480
                user32 = ctypes.windll.user32
                wScr, hScr = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
                frameReduction = int(wCam * 0.06)
                mouse = Controller()
                smoothening, click_smoother = 7, 0
                pLocX, pLocY, cLocX, cLocY = 0, 0, 0, 0
                RMB_pressed, LMB_pressed = False, False

                #------Добавление переменных для отслеживания стабильности позы пальцев------#
                stable_pose_frames = 0
                required_stable_frames = 10

                #------Отражаем изображение------#
                frame1 = cv2.flip(self.frame, 1)
                frame1 = self.detector.findHands(frame1)
                lmlist1, _ = self.detector.findPosition(frame1, draw=True)

                #------Получение конца указательного, среднего и большого пальцев------#
                if len(lmlist1) != 0:
                    x0, y0 = lmlist1[4][1:]
                    x1, y1 = lmlist1[8][1:]
                    x2, y2 = lmlist1[12][1:]

                    #------Проверка поднятых пальцев------#
                    fingers = self.detector.fingersUp()
                    cv2.rectangle(self.mirrored_frame, (frameReduction, frameReduction),
                                  ((wCam - frameReduction), (hCam - frameReduction)),
                                  (255, 0, 0), 2)
                    print(fingers)

                    #------Если только открыт указательный - движение курсора------#
                    if fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0:

                        #------Конвертирование координат------#
                        x3 = np.interp(x1, (frameReduction, (wCam - frameReduction)), (0, wScr))
                        y3 = np.interp(y1, (frameReduction, (hCam - frameReduction)), (0, hScr))

                        #------Увеличение диапазона движения мыши------#
                        x3 = x3 * 9
                        y3 = y3 * 9

                        #------Сглаживание значений------#
                        cLocX = pLocX + (x3 - pLocX) / smoothening
                        cLocY = pLocY + (y3 - pLocY) / smoothening

                        #------Ограничение координат курсора в пределах экрана------#
                        cLocX = min(max(cLocX, 0), wScr)
                        cLocY = min(max(cLocY, 0), hScr)

                        #------Движение мышью------#
                        mouse.position = (cLocX, cLocY)
                        cv2.circle(self.mirrored_frame, (x1, y1), 15, (255, 0, 0), cv2.FILLED)
                        pLocX, pLocY = cLocX, cLocY

                        #------Сглаживание кликов------#
                        if click_smoother >= 30:
                            RMB_pressed, LMB_pressed = False, False
                        click_smoother += 1

                    #------Если только открыты указательный и средний - клик------#
                    if fingers[1] == 1 and fingers[2] == 1:

                        #------Нахождение расстояния между пальцами(Index and Middle пальцы)------#
                        lenghtIM, self.mirrored_frame, lineIndoIM = self.detector.findDistance(8, 12, self.mirrored_frame)

                        #------Нахождение расстояния между пальцами(Middle and Ring(безымянный) пальцы)------#
                        lenghtMR, self.mirrored_frame, lineIndoMR = self.detector.findDistance(12, 16, self.mirrored_frame)

                        #------Если расстояние короткое между средним и безымянным пальцем - совершение клика ПКМ------#
                        if RMB_pressed == False and fingers[3] == 1 and lenghtMR < 65 and lenghtIM < 65:
                            cv2.circle(self.mirrored_frame, (lineIndoIM[4], lineIndoIM[5]),
                                       15, (0, 255, 255), cv2.FILLED)
                            cv2.circle(self.mirrored_frame, (lineIndoMR[4], lineIndoMR[5]),
                                       15, (0, 255, 255), cv2.FILLED)
                            mouse.click(Button.right, 1)
                            RMB_pressed, LMB_pressed = True, False

                        #------Если расстояние короткое между указательным и средним пальцем - совершение клика ЛКМ------#
                        elif LMB_pressed == False and lenghtIM < 65:
                            cv2.circle(self.mirrored_frame, (lineIndoIM[4], lineIndoIM[5]),
                                       15, (0, 255, 0), cv2.FILLED)
                            mouse.click(Button.left, 1)
                            RMB_pressed, LMB_pressed = False, True
                        click_smoother = 0

                    #------Скролинг мышки------#
                    if fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0:
                        cv2.circle(self.mirrored_frame, (x0, y0), 15, (255, 0, 255), cv2.FILLED)
                        if fingers[0] == 0:
                            mouse.scroll(0, 1.5)
                        else:
                            mouse.scroll(0, -1.5)

                cv2.putText(self.mirrored_frame, '-------Mouse mode-------', (30, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (55, 155, 255), 3)

            #---------------------ПРЕОБРАЗОВАНИЕ ВИДЕОПОТОКА И ЦИКЛИЧЕСКИЙ ВЫЗОВ МЕТОДЫ SHOW_VIDEO_STREAM---------------------#
            self.frame_rgb = cv2.cvtColor(self.mirrored_frame, cv2.COLOR_BGR2RGB)
            self.pil_image = Image.fromarray(self.frame_rgb)
            self.resized_image = self.pil_image.resize((640, 480), Image.ANTIALIAS)
            self.video_frame = ImageTk.PhotoImage(self.resized_image)
            self.video_label.configure(image=self.video_frame)
            self.video_label.after(30, self.show_video_stream)

        else:
            print("Не удалось получить кадр с камеры")
            exit(0)

#---------------------------------------------ВЫЗОВ КЛАССА ВСЕГО ПРИЛОЖЕНИЯ---------------------------------------------#
if __name__ == "__main__":
    app = App()
    app.mainloop()

import os
import threading
"""CSB Speech APP"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.icon_definitions import md_icons
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.anchorlayout import MDAnchorLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.screen import MDScreen
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.slider import MDSlider
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.scrollview import MDScrollView, ScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem

from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix

from kivy.animation import Animation

from kivy.core.audio import SoundLoader
from kivy.uix.boxlayout import BoxLayout

from DB_main import save_session, load_session, User, create_folder

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base

current_dir = os.getcwd()
engine = create_engine('sqlite:///kivydatabase.db')
Base = declarative_base()
# если сессия уже существует то загружаем ее и присваниваем переменные пути для этого пользователя
user_id = load_session()
if user_id:
    FOLDER_PATH = os.path.join(current_dir, f'user_{user_id}')
else:
    FOLDER_PATH = 'temporary folder'
# ======================================================================================================================


# ======================================================================================================================
class LoginScreen(MDScreen):
    """Интерфейс входа в приложение"""
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.md_bg_color = (0.5, 0.5, 0.6, 0.3)

        layout = MDBoxLayout(orientation='vertical', size_hint=(0.5, 0.5), spacing=5)

        anchor_layout = MDAnchorLayout(anchor_x='center', anchor_y='center')
        label = MDLabel(text='[color=ff3333]КСБ[/color] [color=3333ff]Speech[/color]',
                        font_size=90,
                        bold=True,
                        size_hint=(1, 1.8),
                        size=(100, 100),
                        markup=True,
                        halign='center')

        self.username_input = MDTextField(hint_text='Имя пользователя',
                                          required=True,
                                          error='Это поле обязательно для заполнения',
                                          multiline=False,
                                          padding=[2, 25],
                                          size_hint_y=None,
                                          height=80,
                                          font_size=24)

        self.password_input = MDTextField(hint_text='Пароль', password=True,
                                          required=True,
                                          error='Это поле обязательно для заполнения',
                                          multiline=False,
                                          padding=[2, 25],
                                          size_hint_y=None,
                                          height=80,
                                          font_size=24)

        # биндим нажатие enter на переход с логина на пароль
        self.username_input.bind(on_text_validate=self.on_user_enter)
        # биндим нажатие enter на нажатие Войти после ввода пароля
        self.password_input.bind(on_text_validate=self.login)

        login_button = MDRaisedButton(text='Войти', size_hint_y=None)
        login_button.bind(on_press=self.login)

        # layout.add_widget(label)
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        layout.add_widget(login_button)

        anchor_layout.add_widget(layout)
        self.add_widget(label)

        self.add_widget(anchor_layout)

    # устанавливаем фокус на поле для пароля
    def on_user_enter(self, instance):
        self.password_input.focus = True

    def login(self, instance):
        username = self.username_input.text
        password = self.password_input.text

        Session = sessionmaker(bind=engine)
        session = Session()
        user = session.query(User).filter_by(username=username, password=password).first()
        session.close()

        if user:
            # И переключаемся на экран с именем 'main'
            user_id = user.id

            save_session(user_id)
            self.manager.current = 'main'

        else:

            ok_button = MDFlatButton(text='OK')

            popup = MDDialog(title='Ошибка',
                             text='Неверное имя пользователя или пароль',
                             buttons=[ok_button],
                             )
            ok_button.bind(on_press=popup.dismiss)
            popup.open()
# ======================================================================================================================


# ======================================================================================================================
class FileListWidget(MDBoxLayout):
    def __init__(self, **kwargs):
        super(FileListWidget, self).__init__(**kwargs)
        self.files = None
        self.orientation = 'vertical'
        # Список для хранения выбранных файлов
        self.selected_files = []
        self.checkboxes = []

        # создаем макет для главного флажка и загаловка и кнопки выбора
        header_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=40)

        # создаем главный флажок и добавляем его в header_layout
        main_checkbox = MDCheckbox(size_hint=(None, 1), width=80)

        main_checkbox.bind(active=self.on_main_checkbox_active)
        text = MDLabel(text='Пользовательские файлы')

        header_layout.add_widget(main_checkbox)
        header_layout.add_widget(text)

        # Создание вертикального BoxLayout для хранения элементов списка
        self.layout = MDBoxLayout(orientation='vertical', size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter('height'))

        # Создание ScrollView и добавление layout в него
        scrollview = ScrollView()
        scrollview.add_widget(self.layout)

        self.add_widget(header_layout)
        self.add_widget(scrollview)
        self.update_filelist()

    def update_filelist(self):
        # Очистка списка файлов
        self.layout.clear_widgets()

        # Получение списка файлов
        self.files = os.listdir(f'{current_dir}/user_{user_id}')
        print(self.files)

        # Счетчик для нумерации файлов
        index = 1

        # Создание горизонтальных BoxLayout для каждого файла
        for file in self.files:
            file_layout = MDBoxLayout(orientation='horizontal', size_hint=(0.999, None), height=30)

            # Создание метки с номером файла и добавление ее в file_layout
            index_label = MDLabel(text=str(index), size_hint_x=None, width=30)
            file_layout.add_widget(index_label)

            # Создание флажка и добавление его в file_layout
            checkbox = MDCheckbox(size_hint_x=None, width=20)

            checkbox.bind(active=self.on_checkbox_active)
            checkbox.file = file
            file_layout.add_widget(checkbox)
            # добавляем ссылку на флажок в список
            self.checkboxes.append(checkbox)

            # Создание кнопки и добавление ее в file_layout
            button = MDFlatButton(text=file)
            button.bind(on_press=self.on_file_select)
            button.checkbox = checkbox  # сохранение ссылки на флажок
            file_layout.add_widget(button)

            # Добавление file_layout в layout
            self.layout.add_widget(file_layout)

            # Увеличение счетчика на 1
            index += 1

    def on_main_checkbox_active(self, checkbox, value):
        # Обработка изменения состояния главного флажка
        if value:
            # выбираем все файлы
            self.select_all_files()
        else:
            # снимаем выбор со всех файлов
            self.deselect_all_files()

    def select_all_files(self):
        for checkbox in self.checkboxes:
            checkbox.active = True

    def deselect_all_files(self):
        for checkbox in self.checkboxes:
            checkbox.active = False

    def on_file_select(self, button):
        # Обработка выбора файла
        button.checkbox.active = not button.checkbox.active   # меняем состояние флажка нажатием на файл

    def on_checkbox_active(self, checkbox, value):
        # Обработка изменения состояния флажка
        if value:
            self.selected_files.append(checkbox.file)
            print(f'список файлов - {self.selected_files}')
        else:
            self.selected_files.remove(checkbox.file)
            print(f'список файлов - {self.selected_files}')
# ======================================================================================================================


# ======================================================================================================================
class PaybackControls(MDBoxLayout):
    """Виджет с кнопками управления воспроизведением сверху"""
    def __init__(self, file_list, repeat_input, text_to_speech, **kwargs):
        super(PaybackControls, self).__init__(**kwargs)
        self.file_list = file_list
        self.text_to_speech = text_to_speech
        self.repeat_input = repeat_input

        self.sound = None
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = 32
        self.spacing = 8
        self.playing = False
        self.play_event = threading.Event()

        # создаем кнопки для запуска и остановки воспроизведения
        self.run_button = MDIconButton(icon="play", size_hint=(None, None), size=(25, 25))

        self.stop_button = MDIconButton(icon="stop", size_hint=(None, None), size=(25, 25))

        # кнопка настроек воспроизведения
        self.settings_button = MDIconButton(icon="settings", size_hint=(None, None), size=(25, 25))

        # кнопка загрузки файла
        self.upload_button = MDIconButton(icon="upload", size_hint=(None, None), size=(25, 25))

        # создаем кнопкe удаления
        self.delete_button = MDIconButton(icon="delete", size_hint=(None, None), size=(25, 25))

        # кнопка обновить список файлов
        self.refresh_button = MDIconButton(icon="refresh", size_hint=(None, None), size=(25, 25))

        # назначем функции на нажатие кнопок
        self.delete_button.bind(on_press=lambda x: self.on_delete_button_press())
        self.run_button.bind(on_press=lambda x: self.on_run_button_press())
        self.stop_button.bind(on_press=lambda x: self.stop_file())
        self.refresh_button.bind(on_press=lambda x: self.refresh_files())

        self.add_widget(self.run_button)
        self.add_widget(self.stop_button)
        self.add_widget(self.upload_button)
        self.add_widget(self.delete_button)
        self.add_widget(self.refresh_button)
        self.add_widget(self.settings_button)

    def on_delete_button_press(self):
        if self.file_list.selected_files:
            print('удаление..')

            # создаем всплывающее окно с двумя кнопками
            box = MDBoxLayout(orientation='horizontal', size_hint=(None, None), height=25, spacing=105)

            yes_button = MDFlatButton(text='Да')
            no_button = MDFlatButton(text='Отмена')

            dialog = MDDialog(title='Вы уверены?', buttons=[yes_button, no_button])

            # обрабатываем нажатие на кнопки
            yes_button.bind(on_press=lambda *args: self.delete_all_files(dialog))
            no_button.bind(on_press=dialog.dismiss)

            dialog.open()

        else:
            anim = Animation(size_hint=(0.99, 0.99), duration=0.05) + Animation(size_hint=(1, 1), duration=0.05)
            self.file_list.update_filelist()
            anim.start(self.file_list)

    def delete_all_files(self, popup):
        # выполняем действие для удаления всех файлов
        for file in self.file_list.selected_files:
            print('удаляю', file)
            os.remove(f'user_{user_id}/{file}')
        popup.dismiss()
        self.file_list.update_filelist()

    def refresh_files(self):
        anim = Animation(size_hint=(0.90, 0.90), duration=0.09) + Animation(size_hint=(1, 1), duration=0.09)
        self.file_list.update_filelist()
        anim.start(self.file_list)

    def on_run_button_press(self):
        print('run_file')
        if not self.playing:
            # включаем индикатор
            self.text_to_speech.icon.theme_text_color = "Custom"
            self.text_to_speech.icon.text_color = (0, 1, 0, 0.9)

            # запускаем поток для управления состоянием воспроизведения
            self.playing = True
            threading.Thread(target=self.run_file,
                             args=(self.file_list.selected_files,)).start()

    def run_file(self, selection: list):
        """запуск воспроизведения файла"""
        # можно поменять способ воспроизведения или перенаправить

        repeat_count = int(self.repeat_input.text_input.text)

        for i in range(repeat_count):
            print(f'количество повторений: {repeat_count-i}')
            for file in selection:
                if not self.playing:
                    print(1228)
                    break
                self.sound = SoundLoader.load(f'{FOLDER_PATH}/{file}')
                # сбрасываем событие перед воспроизведением звука
                self.play_event.clear()
                # устанавливаем обработчик события on_stop
                self.sound.bind(on_stop=lambda x: self.play_event.set())
                self.sound.play()
                # ожидаем окончания воспроизведения звука
                self.play_event.wait()

            # и автоматически выключаем индикатор
            self.text_to_speech.icon.theme_text_color = "Custom"
            self.text_to_speech.icon.text_color = (0.5, 0.5, 0.5, 1)
        self.playing = False

    def stop_file(self):
        """остановка воспроизведения файла"""
        self.playing = False
        # выключаем индикатор
        self.text_to_speech.icon.theme_text_color = "Custom"
        self.text_to_speech.icon.text_color = (0.5, 0.5, 0.5, 1)
        if hasattr(self, 'sound') and self.sound:
            self.sound.stop()
            # устанавливаем событие для немедленного завершения ожидания в методе run_file
            self.play_event.set()
# ======================================================================================================================


# ======================================================================================================================
class LogoTextInput(MDTextField):
    """добавляет логотип КСБ в TextInput - TextToSpeech"""
    def __init__(self, **kwargs):
        super(LogoTextInput, self).__init__(**kwargs)

        # Создание полупрозрачного логотипа
        with self.canvas.after:
            PushMatrix()
            Color(1, 1, 1, 0.25)
            self.logo = Rectangle(source='ICONS/logo.png', size=self.size, pos=self.pos)
            PopMatrix()

        # Обновление размера и позиции логотипа при изменении размера или позиции TextInput
        self.bind(size=self.update_logo, pos=self.update_logo)

    def update_logo(self, *args):
        # Обновление размера и позиции логотипа
        self.logo.size = (self.width * 0.5, self.height * 0.4)
        self.logo.pos = (self.right - self.logo.size[0], self.y)



class TextToSpeech(BoxLayout):
    """виджет для озвучки введенного текса"""
    def __init__(self, repeat_input=None, payback_controls=None, **kwargs):
        super(TextToSpeech, self).__init__(**kwargs)
        self.payback_controls = payback_controls
        self.repeat_input = repeat_input
        self.orientation = 'vertical'
        self.size_hint = (1, 0.6)
        self.voice = None

        # создаем поле для ввода текста
        self.text_input = LogoTextInput(hint_text='Введите текст для озвучки\n'
                                                  'ТОЛЬКО КИРИЛЛИЦА.\n'
                                                  'БЕЗ ЦИФР.\n'
                                                  '"+" - можно ставить перед буквой на которую нужно ударение.\n'
                                                  'Максимум 140 символов.',
                                        background_color=(1, 1, 1, 1),
                                        foreground_color=(0, 0, 0, 1),
                                        input_filter=self.text_filter,
                                        size_hint=(1, 0.5))

        # создаем кнопку для озвучивания текса
        speak_button_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=35)

        # индикатор озвучки
        self.icon = MDIcon(icon="check", size_hint=(None, None),
                           height=35,
                           width=35,
                           text_color=(0.5, 0.5, 0.5, 1))

        speak_button = MDFlatButton(text='Озвучить', size_hint=(1, None), height=35)
        speak_button.bind(on_press=lambda x: self.on_speak_status())

        test_button = MDFlatButton(text='Прослушать', size_hint=(1, None), height=35)

        speak_button_layout.add_widget(self.icon)
        speak_button_layout.add_widget(speak_button)
        speak_button_layout.add_widget(test_button)

        self.add_widget(self.text_input)
        self.add_widget(speak_button_layout)

    def on_voice_select(self, voice_name):
        """Обработчик события выбора голоса"""
        self.voice = voice_name

    def speak_text(self):
        """озвучка текста"""
        print('озвучка..')
        text = self.text_input.text
        if text:
            # ВКЛ индикатор
            self.icon.theme_text_color = "Custom"
            self.icon.text_color = (0, 1, 0, 0.9)

            repeat_count = int(self.repeat_input.text_input.text)
            for _ in range(repeat_count):
                print(f'выбранный голос {self.voice}')
                # TTS(text, voice_id=self.voice, save_to=f'{FOLDER_PATH}')
                # self.icon.theme_text_color = "Custom"
                # self.icon.text_color = (0, 1, 0, 0.9)
                pass
        else:
            # индикатор ВЫКЛ
            self.icon.theme_text_color = "Custom"
            self.icon.text_color = (0.5, 0.5, 0.5, 1)

    def on_speak_status(self):
        """статус кнопки "озвучить" """
        self.icon.theme_text_color = "Custom"
        self.icon.text_color = (0, 1, 0, 0.9)
        threading.Thread(target=self.speak_text).start()

    def text_filter(self, value, is_undo):
        # Разрешаем ввод только символов, удовлетворяющих условиям фильтрации
        filtered_value = ''.join(
            [c if c not in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' else '' for c in value])
        # Ограничиваем длину текста 140 символами
        filtered_value = filtered_value[:140]
        return filtered_value

# ======================================================================================================================


# ======================================================================================================================
class RepeatInput(BoxLayout):
    """виджет окна количетва повторений"""
    def __init__(self, **kwargs):
        super(RepeatInput, self).__init__(orientation='vertical', **kwargs)
        self.size_hint = (None, 0.7)
        self.width = 50

        self.text_input = MDTextField(text='1',
                                      halign='center',
                                      font_size=20,
                                      input_filter='int')

        # Связываем изменение размера TextInput с функцией обновления размера шрифта
        self.text_input.bind(size=self.update_padding)

        self.plus_button = MDRaisedButton(text='+', )
        self.minus_button = MDRaisedButton(text='-', )

        # меняем значение text_input нажатием на кнопки + -
        self.plus_button.bind(on_press=self.on_plus_button_press)
        self.minus_button.bind(on_press=self.on_minus_button_press)

        self.add_widget(self.plus_button)
        self.add_widget(self.text_input)
        self.add_widget(self.minus_button)

    def update_padding(self, instance, value):
        # Обновляем верхний и нижний отступы в соответствии с текущей высотой TextInput
        padding = (instance.height - instance.line_height) / 2
        instance.padding = [instance.padding[0], padding, instance.padding[2], padding]

    def on_plus_button_press(self, instance):
        try:
            value = int(self.text_input.text)
            self.text_input.text = str(value + 1)
        except ValueError:
            # Анимация ошибки
            anim = Animation(background_color=(1, 0.1, 0.1, 0.5),
                             duration=0.15) + \
                   Animation(background_color=(1, 1, 1, 1),
                             duration=0.2)
            anim.start(self.text_input)
            print('Неверное значение в поле ввода')
            self.text_input.text = '1'

    def on_minus_button_press(self, instance):
        try:
            value = int(self.text_input.text)
            self.text_input.text = str(max(1, value - 1))
        except ValueError:
            # Анимация ошибки
            anim = Animation(background_color=(1, 0.1, 0.1, 0.5),
                             duration=0.15) + \
                   Animation(background_color=(1, 1, 1, 1),
                             duration=0.2)
            anim.start(self.text_input)
            print('Неверное значение в поле ввода')
            self.text_input.text = '1'
# ======================================================================================================================


# ======================================================================================================================
class CheckOneLineListItem(OneLineListItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.checkbox = MDCheckbox()

    def on_release(self):
        # здесь мы добавляем чекбокс динамически при нажатии на элемент списка
        self.add_widget(self.checkbox)
        # затем вызываем функцию menu_callback как раньше
        self.parent.parent.parent.parent.parent.menu_callback(self.text.split()[0])


class ZoneSelector(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, None)
        self.height = 35

        self.selected_zones = []
        self.numbers = [str(i) for i in range(1, 7)]

        self.zone_list_btn = MDRaisedButton(text="Зоны:", size_hint=(1, None), height=35)
        self.zone_list_btn.bind(on_release=lambda x: self.dropdown.open())

        # Создаем ScrollView для отображения списка зон
        scrollview = ScrollView(size_hint=(1, None), height=200)

        # Создаем вертикальный BoxLayout для хранения элементов списка
        self.layout = MDBoxLayout(orientation="vertical", size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter("height"))

        # Добавляем элементы списка в layout
        for number in self.numbers:
            item = CheckOneLineListItem(text=f"{number} зона")
            item.bind(on_release=lambda item=item: self.menu_callback(item.text.split()[0]))
            item.checkbox.bind(active=lambda cbox, item=item: self.menu_callback(item.text.split()[0]))
            self.layout.add_widget(item)

        # Добавляем layout в ScrollView
        scrollview.add_widget(self.layout)

        # Создаем MDDialog для отображения списка зон
        self.dropdown = MDDialog(title="Выберите зоны", type="custom", content_cls=scrollview)

        self.add_widget(self.zone_list_btn)

    def menu_callback(self, zone):
        """добавляем активные зоны в список и удаляем не активные"""
        if zone not in self.selected_zones:
            print(f"{zone} зона активна")
            self.selected_zones.append(zone)
            print(self.selected_zones)
        else:
            print(f"{zone} зона неактивна")
            self.selected_zones.remove(zone)
            print(self.selected_zones)

# ======================================================================================================================


# ======================================================================================================================
class VoiceSelector(MDBoxLayout):
    """виджет для выбора голоса кнопкой над полем ввода текста"""
    def __init__(self, text_to_speech, zone_selector, **kwargs):
        super(VoiceSelector, self).__init__(**kwargs)
        self.checkbox_zone_selector = zone_selector
        self.text_to_speech = text_to_speech
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = 35

        self.voice_list_btn = MDRaisedButton(text='Голос:', size_hint=(1, None), height=35)
        self.voice_list_btn.bind(on_release=lambda x: self.dropdown.open())

        voices = ['M-1', 'M-2', 'Ж-1', 'Ж-2', 'Ж-3', 'Ж-4']

        # Создаем выпадающий список для выбора голоса
        menu_items = [{"viewclass": "OneLineListItem",
                       "text": voice,
                       "on_release": lambda x=voice: self.set_voice(x)
                       } for voice in voices]

        self.dropdown = MDDropdownMenu(caller=self.voice_list_btn, items=menu_items, width_mult=4)



        # Создаем диалоговое коно содержащее список с зонами
        self.checkbox_dropdown = self.checkbox_zone_selector
        self.checkbox_list_btn = MDRaisedButton(text='Зоны:', size_hint=(1, None), height=35)
        self.checkbox_list_btn.bind(on_release=lambda x: self.checkbox_dropdown.dropdown.open())


        self.add_widget(self.voice_list_btn)
        self.add_widget(self.checkbox_list_btn)

    def set_voice(self, voice_name):
        """установка выбранного голоса"""
        print('call set voice')
        if self.text_to_speech.on_voice_select:
            self.text_to_speech.on_voice_select(voice_name)
        self.voice_list_btn.text = f'Голос: {voice_name}'
        self.dropdown.dismiss()
# ======================================================================================================================


# ======================================================================================================================
class MainScreen(MDScreen):
    """Основной интерфейс приложения"""
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        with self.canvas.before:
            Color(0.6, 0.6, 0.7, 0.3)  # Задайте нужный цвет здесь
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        """ВИДЖЕТЫ"""
        # добавляем виджет RepeatInput()
        repeat_input = RepeatInput()

        # добавляем виджет FileList
        file_list = FileListWidget()

        # добавляем виджет выбора зон проигрывания ZoneSelector()
        zone_selector = ZoneSelector()

        # Добавляем виджет TextToSpeech
        text_to_speech = TextToSpeech(repeat_input, file_list)

        # Добавляем виджет VoiceSelector()
        voice_selector = VoiceSelector(text_to_speech, zone_selector)

        # добавляем верхнее меню с кнопками управления файлами
        tool_layout = PaybackControls(file_list, repeat_input, text_to_speech)

        # непонятные вещи как они работают хз(добавляет )
        text_to_speech.button_layout = tool_layout


        """МАКЕТЫ"""
        # поле для ввода и выбор голоса
        layout = MDBoxLayout(orientation='vertical')
        layout.add_widget(voice_selector)
        layout.add_widget(text_to_speech)  # содоержит кнопку "Озвучить"

        # макет в котором будут находиться поля для воода текста и поле для воода количества повторений
        bottom_layout = MDBoxLayout()
        bottom_layout.add_widget(repeat_input)
        bottom_layout.add_widget(layout)

        # основной макет в который добавляется file list и окна для ввода с кнопками
        root_layout = MDBoxLayout(orientation='vertical')
        root_layout.add_widget(tool_layout)
        root_layout.add_widget(file_list)
        root_layout.add_widget(bottom_layout)

        self.add_widget(root_layout)

    def _update_rect(self, instance, value):
        # обновляем цвет фона
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class SpeechApp(MDApp):
    """менеджер экранов приложения"""
    def build(self):

        login_screen = LoginScreen(name='login')
        main_screen = MainScreen(name='main')

        sm = ScreenManager()
        sm.add_widget(login_screen)
        sm.add_widget(main_screen)

        # Если сессия найдена, то автоматически переключаемся на экран с именем 'main'
        if user_id:
            print(f'FOLDER_PATH={FOLDER_PATH}')
            print(f'user_id={user_id}')
            sm.current = 'main'

        return sm


if __name__ == '__main__':
    SpeechApp().run()



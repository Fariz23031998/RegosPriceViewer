from kivy.config import Config
Config.set('graphics', 'fullscreen', 'auto')
Config.set('graphics', 'borderless', '1')
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
import pandas as pd
from item_infos import ItemToCsv
import json
import pyautogui

with open('settings.json', 'r', encoding='utf-8') as settings_file:
    settings = json.load(settings_file)

item_to_csv = ItemToCsv()
screen_width = Window.width
screen_height = Window.height


class PriceCheckerApp(App):
    def build(self):
        pyautogui.moveTo(screen_width-30, screen_height-30)
        pyautogui.click()
        self.result_name = Label(
            text='СКАНИРУЙТЕ ШТРИХКОД',
            font_size=f'{settings["name_font_size"]}sp',
            color=list(self.format_rgba_color(settings["name_font_color"])),
            size_hint_x=None,
            width=screen_width,  # Setting the size of the label
            text_size=(screen_width*0.8, None),  # Setting the width at which text should wrap
            halign='center',  # Horizontal alignment
            valign='top'  # Vertical alignment
        )


        self.result_price = Label(
            text='',
            font_size=f'{settings["price_font_size"]}sp',
            color=list(self.format_rgba_color(settings["price_font_color"]))
        )
        self.background_color = settings['background_color']

        if not self.update_csv(None):
            self.read_csv()

        function_layout = BoxLayout(orientation='horizontal', size_hint=(None, None), width=500, height=30)

        self.barcode_input = TextInput(
            hint_text='Сканируйте штрихкод',
            multiline=False,
            background_normal='',
            background_active='',
            background_color=self.format_rgba_color(self.background_color),
            foreground_color=self.format_rgba_color(settings['name_font_color'])
        )

        Clock.schedule_interval(self.barcode_focus, 1)

        function_layout.add_widget(self.barcode_input)

        show_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.5))
        show_layout.add_widget(self.result_name)
        show_layout.add_widget(self.result_price)

        show_anchor_layout = AnchorLayout(anchor_x='center', anchor_y='center')
        show_anchor_layout.add_widget(show_layout)

        layout = BoxLayout(orientation='vertical', spacing=10)
        with layout.canvas.before:
            # Set the background color to blue (RGBA)
            r = self.background_color[0]
            g = self.background_color[1]
            b = self.background_color[2]
            a = self.background_color[3]

            Color(r, g, b, a)
            Rectangle(size=(screen_width, screen_height))

        layout.add_widget(show_anchor_layout)
        layout.add_widget(function_layout)

        Window.bind(on_key_down=self.on_key_down)

        Clock.schedule_interval(self.update_csv, settings["sync_time"])

        return layout

    def check_price(self, instance):
        self.cancel_event()
        barcode = self.barcode_input.text
        item_id = self.get_item_id_from_barcode(barcode)
        if item_id == "failed":
            pass
        elif item_id == "succeed":
            self.result_name.text = 'Данные Обновились'
            self.result_price.text = ''
        elif item_id:
            item_info = self.get_item_info_by_id(item_id)
            if item_info:
                self.result_name.text = f"{item_info[2]} ({item_info[7]})"

                item_price = self.get_item_price(item_id)
                if item_price:
                    formatted_price = str(self.format_number_with_spaces(item_price[2]))
                    self.result_price.text = formatted_price
                else:
                    self.result_price.text = "Цена не указано!"
            else:
                self.result_name.text = 'Товар не найдено!'
                self.result_price.text = ""
        else:
            self.result_name.text = 'Товар не найдено!'
            self.result_price.text = ""

        self.barcode_input.text = ''
        self.reset_screen = Clock.schedule_once(self.update_screen, settings['update_screen_time'])

    def get_item_id_from_barcode(self, barcode):
        if barcode == "quit":
            self.stop()
        elif barcode == "update":
            if self.update_csv(None):
                return "succeed"
            else:
                return "failed"
        else:
            filtered_df = self.barcode_df[self.barcode_df['BRCD_VALUE'].astype(str) == barcode]
            if not filtered_df.empty:
                return filtered_df['BRCD_ITEM'].values[0]
            return None

    def get_item_info_by_id(self, item_id):
        filtered_df = self.items_df[self.items_df['ITM_ID'] == item_id]
        if not filtered_df.empty:
            return list(filtered_df.values[0])
        else:
            return False

    def get_item_price(self, item_id):
        filtered_df = self.prices_df[self.prices_df['PRC_ITEM'] == item_id]
        if not filtered_df.empty:
            return list(filtered_df.values[0])
        else:
            return False

    def on_key_down(self, window, key, scancode, codepoint, modifier):
        # Check which key was pressed
        if key == 13:  # Escape key
            self.check_price(instance="")

    def update_screen(self, dt):
        self.result_name.text = 'СКАНИРУЙТЕ ШТРИХКОД'
        self.result_price.text = ''

    def update_csv(self, dt):
        if item_to_csv.connect_server():
            item_to_csv.get_items_info()
            self.read_csv()
            return True
        else:
            self.cancel_event()
            self.result_name.text = 'Не получается подключится к базу данных...'
            self.result_price.text = ''
            self.reset_screen = Clock.schedule_once(self.update_screen, 50)
            return False

    def barcode_focus(self, dt):
        self.barcode_input.focus = True

    def format_number_with_spaces(self, number):
        rounded_number = round(number)
        return f"{rounded_number:,}".replace(",", " ")

    def format_rgba_color(self, rgba):
        formatted_color = []
        for i in range(0, 3):
            if rgba[i] != 0:
                formatted_color.append(rgba[i] / 255)
            else:
                formatted_color.append(rgba[i])

        formatted_color.append(rgba[3])
        return formatted_color[0], formatted_color[1], formatted_color[2], formatted_color[3]

    def cancel_event(self):
        try:
            Clock.unschedule(self.reset_screen)
        except AttributeError:
            pass

    def read_csv(self):
        try:
            self.barcode_df = pd.read_csv('barcodes.csv')
            self.items_df = pd.read_csv('items_info.csv')
            self.prices_df = pd.read_csv('prices.csv')
        except FileNotFoundError:
            self.result_name.text = 'Не найдено .csv файл. Проверьте соединение с База данных.'
            Clock.schedule_once(self.stop, 50)


if __name__ == '__main__':
    PriceCheckerApp().run()


from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.storage.jsonstore import JsonStore
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import Screen
from kivymd.uix.button import MDRaisedButton
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.properties import ListProperty
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
import random
import logging

# Set up logging
logging.basicConfig(filename='app.log', level=logging.ERROR)

class ThemeManager:
    themes = {
        'Default': {
            'background': get_color_from_hex('#FFFFFF'),
            'primary': get_color_from_hex('#3498DB'),
            'secondary': get_color_from_hex('#E74C3C'),
            'text': get_color_from_hex('#2C3E50'),
        },
        'Dark': {
            'background': get_color_from_hex('#2C3E50'),
            'primary': get_color_from_hex('#3498DB'),
            'secondary': get_color_from_hex('#E74C3C'),
            'text': get_color_from_hex('#ECF0F1'),
        },
        'High Contrast': {
            'background': get_color_from_hex('#000000'),
            'primary': get_color_from_hex('#FFFFFF'),
            'secondary': get_color_from_hex('#FFFF00'),
            'text': get_color_from_hex('#FFFFFF'),
        }
    }

    def __init__(self):
        self.store = JsonStore('theme_preference.json')
        self.current_theme = self.load_theme_preference()
        self._cached_theme = None

    def get_theme(self):
        if self._cached_theme is None or self._cached_theme['name'] != self.current_theme:
            self._cached_theme = {
                'name': self.current_theme,
                'colors': self.themes.get(self.current_theme, self.themes['Default'])
            }
        return self._cached_theme['colors']

    def set_theme(self, theme_name):
        if theme_name in self.themes:
            self.current_theme = theme_name
            self._cached_theme = None  # Invalidate cache
            self.save_theme_preference()

    def load_theme_preference(self):
        try:
            if self.store.exists('theme'):
                return self.store.get('theme')['name']
        except Exception as e:
            logging.error(f"Error reading theme preference: {e}")
        return 'Default'

    def save_theme_preference(self):
        try:
            self.store.put('theme', name=self.current_theme)
        except Exception as e:
            logging.error(f"Error writing theme preference: {e}")

theme_manager = ThemeManager()

class Diamond(Widget):
    color = ListProperty([1, 1, 1, 1])  # Default to white

    def __init__(self, **kwargs):
        super(Diamond, self).__init__(**kwargs)
        self.size = (30, 30)
        self.color = [random.random() for _ in range(3)] + [1]
        self.bind(pos=self.update_diamond, size=self.update_diamond)
    
    def draw_diamond(self):
        points = self.get_points()
        with self.canvas:
            Color(*self.color)
            Line(points=points, close=True, width=2)
    
    def get_points(self):
        return [self.center_x, self.top, self.right, self.center_y,
                self.center_x, self.y, self.x, self.center_y]
    
    def update_diamond(self, *args):
        self.canvas.clear()
        self.draw_diamond()

class Coin(Widget):
    def __init__(self, **kwargs):
        super(Coin, self).__init__(**kwargs)
        self.size = (20, 20)
        with self.canvas:
            Color(1, 0.84, 0)  # Gold color
            self.coin = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self.update_coin)
    
    def update_coin(self, *args):
        self.coin.pos = self.pos
    
    def fall(self):
        anim = Animation(y=0, duration=random.uniform(1, 3))
        anim.start(self)

class ThemedBoxLayout(BoxLayout):
    def apply_theme(self, theme):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*theme['background'])
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        for child in self.children:
            if isinstance(child, Label):
                child.color = theme['text']
            elif isinstance(child, Button):
                child.background_color = theme['primary']
                child.color = theme['text']
            elif isinstance(child, TextInput):
                child.background_color = theme['secondary']
                child.foreground_color = theme['text']
            elif hasattr(child, 'apply_theme'):
                child.apply_theme(theme)

    def update_rect(self, *args):
        if hasattr(self, 'rect'):
            self.rect.pos = self.pos
            self.rect.size = self.size

class SetupScreen(Screen):
    def __init__(self, **kwargs):
        super(SetupScreen, self).__init__(**kwargs)
        self.layout = ThemedBoxLayout(orientation='vertical', spacing=10, padding=20)
        self.num_numbers = TextInput(text='5', input_filter='int', multiline=False)
        self.max_size = TextInput(text='100', input_filter='int', multiline=False)
        start_button = Button(text='Start Game', on_press=self.start_game)
        self.layout.add_widget(Label(text='Number of slots:'))
        self.layout.add_widget(self.num_numbers)
        self.layout.add_widget(Label(text='Max number:'))
        self.layout.add_widget(self.max_size)
        self.layout.add_widget(start_button)
        self.add_widget(self.layout)

    def start_game(self, instance):
        num_numbers = max(1, min(10, int(self.num_numbers.text)))
        max_size = max(10, min(1000, int(self.max_size.text)))
        game_screen = self.manager.get_screen('game')
        game_screen.setup_game(num_numbers, max_size)
        self.manager.current = 'game'

    def apply_theme(self):
        self.layout.apply_theme(theme_manager.get_theme())

class NumberSlot(ThemedBoxLayout):
    number_text = StringProperty("♦")
    is_rotating = BooleanProperty(False)
    max_number = NumericProperty(0)

    def __init__(self, max_number, **kwargs):
        super(NumberSlot, self).__init__(orientation='vertical', **kwargs)
        self.max_number = max_number

    def start_rotation(self):
        self.is_rotating = True
        Clock.schedule_interval(self.update_number, 0.1)

    def update_number(self, dt):
        if self.is_rotating:
            self.number_text = str(random.randint(0, self.max_number))
        return self.is_rotating

    def stop_rotation(self, instance=None):
        self.is_rotating = False
        Clock.unschedule(self.update_number)
        self.number_text = "♦"  # Show diamond when stopped

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.layout = ThemedBoxLayout(orientation='vertical', padding=10, spacing=10)
        self.diamonds_layout = BoxLayout(size_hint_y=0.2)
        self.slots_layout = ThemedBoxLayout(orientation='horizontal', spacing=10)
        self.stop_bar = Button(text='STOP ALL SLOTS', size_hint_y=0.15, on_press=self.stop_all)
        self.control_layout = ThemedBoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10)
        
        self.start_rotating_button = Button(text='Start Rotating', on_press=self.start_rotating)
        self.theme_button = Button(text='Change Theme', on_press=self.open_theme_screen)
        self.control_layout.add_widget(self.start_rotating_button)
        self.control_layout.add_widget(self.theme_button)
        
        self.layout.add_widget(self.diamonds_layout)
        self.layout.add_widget(self.slots_layout)
        self.layout.add_widget(self.stop_bar)
        self.layout.add_widget(self.control_layout)
        self.add_widget(self.layout)
        
        # Add diamonds
        for _ in range(9):
            self.diamonds_layout.add_widget(Diamond())
        
        # Add coins
        Clock.schedule_interval(self.add_coin, 1)

    def setup_game(self, num_numbers, max_size):
        self.slots_layout.clear_widgets()
        for i in range(num_numbers):
            slot = NumberSlot(max_number=max_size)
            self.slots_layout.add_widget(slot)
        self.apply_theme()

    def start_rotating(self, instance):
        for slot in self.slots_layout.children:
            slot.start_rotation()
        self.start_rotating_button.disabled = True
        self.stop_bar.disabled = False

    def stop_all(self, instance):
        for slot in self.slots_layout.children:
            slot.stop_rotation()
        self.start_rotating_button.disabled = False
        self.stop_bar.disabled = True

    def open_theme_screen(self, instance):
        self.manager.current = 'theme'

    def apply_theme(self):
        theme = theme_manager.get_theme()
        self.layout.apply_theme(theme)
        self.slots_layout.apply_theme(theme)
        self.control_layout.apply_theme(theme)

    def add_coin(self, dt):
        coin = Coin(pos=(random.randint(0, Window.width - 20), Window.height))
        self.add_widget(coin)
        coin.fall()

class ThemeScreen(Screen):
    def __init__(self, **kwargs):
        super(ThemeScreen, self).__init__(**kwargs)
        self.layout = ThemedBoxLayout(orientation='vertical', spacing=10, padding=20)
        self.layout.add_widget(Label(text='Select a Theme', font_size=24, size_hint_y=0.2))
        
        for theme_name in theme_manager.themes.keys():
            btn = Button(text=theme_name, size_hint_y=None, height=50)
            btn.bind(on_press=self.set_theme)
            self.layout.add_widget(btn)
        
        back_btn = Button(text='Back to Game', size_hint_y=None, height=50)
        back_btn.bind(on_press=self.go_back)
        self.layout.add_widget(back_btn)
        
        self.add_widget(self.layout)

    def set_theme(self, instance):
        theme_manager.set_theme(instance.text)
        for screen in self.manager.screens:
            screen.apply_theme()

    def go_back(self, instance):
        self.manager.current = 'game'

    def apply_theme(self):
        self.layout.apply_theme(theme_manager.get_theme())

class LuckyNumberApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.root = ScreenManager()
        sm = self.root

        sm.add_widget(SetupScreen(name='setup'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(ThemeScreen(name='theme'))

        for screen in sm.screens:
            screen.apply_theme()

        return sm

    def on_start(self):
        try:
            Clock.schedule_once(self.apply_theme_to_all_screens, 0)
        except Exception as e:
            logging.error(f"Error on app start: {e}")

    def apply_theme_to_all_screens(self, dt):
        for screen in self.root.screens:
            screen.apply_theme()

if __name__ == '__main__':
    LuckyNumberApp().run()

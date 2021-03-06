import sys
from math import pi, cos
from time import perf_counter

import numpy as np
import pygame
from pygame.draw import polygon

from Engine.apps import MicroApp
from Engine.camera import Camera
from settings import *
from .Levels.testlevel import TestLevel


def dev_message():
    print('Включение оверлея разработчика F3')


class LoadingScreen(MicroApp):
    """
    Приложение загрузочного экрана
    """

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, lifetime=6):
        super(LoadingScreen, self).__init__(screen, clock)
        self.end_time = perf_counter() + lifetime
        # Фоновый цвет
        self.background_color = (100, 100, 254)
        # Цвета, которыми будут переливаться буквы
        self.colors = [(212, 6, 6), (238, 156, 0), (227, 255, 0), (6, 191, 0), (0, 26, 152)]

        # Музыка на загрузочном экране
        self.bgmusic = pygame.mixer.Sound('Resources/Music/lodingscreen.ogg')

        # Цыганская магия, которая рисует черный прямоугольник с вырезанными прозраычными буквами
        # Точнее создает трафарет
        # Лучше не вникать (реально)
        # Инициализация шрифта
        self.font = pygame.font.SysFont('maturascriptcapitals', SCREEN_HEIGHT // 5)
        # Рисование просто букв цвета temp_color на поверхности
        temp_color = (0, 0, 255)
        self.temp = self.font.render('Need For Otl 10', False, temp_color)
        # Центрирование поверхности на экране
        self.rect = self.temp.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        # Сама поверхность для трафорента текста
        self.text_surface = pygame.Surface(self.rect.size).convert_alpha()
        # Заливаем её цветом, который будем превращать в прозрачный
        self.text_surface.fill((1, 1, 1))
        # Рисуем текст на ней
        self.text_surface.blit(self.temp, (0, 0))
        # Меняем temp_color на прозрачную зону
        self.text_surface.set_colorkey(temp_color)

        # Поверхность на которой будет рисоваться анимированные буквы
        # Потом ее рисуем на экране
        # Нужно, чтобы можно было легко реализовать цыганскую магию
        self.camera_surface = pygame.Surface(self.rect.size).convert_alpha()

        # Технические перемнные
        # Сдвиг переливов (мб при больших значениях упадет точность, но это займет много времени)
        self.position = 0
        # Скорость движения полос
        self.speed = 70
        # Высота полос (она же высота текста)
        self.height_of_strip = self.text_surface.get_height()
        # Кол-во полос на тексте (должно быть кратно кол-ву цветов в self.colors, иначе не будет циклического перехода)
        self.num_strips = 5 * len(self.colors)
        # Длина полос (тоже вычисляется через цыганскую магию)
        # Лучше не трогать
        self.len_of_strip = (self.camera_surface.get_width() + self.height_of_strip * cos(pi / 4)) / (
                self.num_strips - 1)

    def run_once(self):
        self.bgmusic.play()

    def prepare_text(self):
        """
        Рисует буквы с переливающимся цветом
        :return:
        """

        # Рисуем полоски (параллелограммы)
        for strip in range(self.num_strips):
            x_coord = (strip * self.len_of_strip + self.position) % (
                    self.len_of_strip * self.num_strips) - self.len_of_strip
            coords = (
                (x_coord, 0),
                (x_coord - self.height_of_strip * cos(pi / 4), self.height_of_strip),
                (x_coord + self.len_of_strip - self.height_of_strip * cos(pi / 4), self.height_of_strip),
                (x_coord + self.len_of_strip, 0)
            )
            polygon(self.camera_surface, self.colors[strip % len(self.colors)], coords)

        # Вырезаем буквы
        self.camera_surface.blit(self.text_surface, (0, 0))

        # Делаем прозрачным то, что нужно
        # удалив это строчку, можно накинуть 20 фпс
        self.camera_surface.set_colorkey((1, 1, 1))

    def atexit(self):
        """
        Тормозим фоновую музыку
        :return: None
        """
        self.bgmusic.stop()

    def step(self, dt):
        """
        Двигаем полоски
        :param dt: квант времени
        :return:
        """
        self.position += self.speed * dt

    def draw(self):
        """
        Рисуем всё на экране
        :return:
        """
        self.screen.fill(self.background_color)
        self.prepare_text()
        self.screen.blit(self.camera_surface, self.rect.topleft)

        pygame.display.update()


class Game(MicroApp):
    def __init__(self, screen, clock):
        super(Game, self).__init__(screen, clock, lifetime=float('inf'))
        self.FPS = 0
        self.scene = TestLevel(Game)
        self.camera = Camera(self.screen, distance=16)
        self.camera.start()
        self.DEVMODE = DEVMODE
        if DEVMODE:
            dev_message()

    def draw(self):
        self.camera.view(self.scene)

        if self.DEVMODE:
            self.camera.devview(self.scene)

        self.camera.show(self.DEVMODE)
        pygame.display.update()

    def step(self, dt):
        self.scene.player.keyboard_handler(pressed_keys=pygame.key.get_pressed())
        self.scene.step(dt)

    def on_iteration(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed(3)[0]:
                self.camera.position += np.array(event.rel) * [-1, 1] / self.camera.scale_factor
            if event.type == pygame.MOUSEWHEEL:
                self.camera.distance -= event.y
            if event.type == pygame.KEYDOWN:
                if pygame.key.get_pressed()[pygame.K_r]:
                    self.camera.position = 0, 0
                    self.camera.distance = 14
                if pygame.key.get_pressed()[pygame.K_F3]:
                    self.DEVMODE = not self.DEVMODE

        self.run_tasks()
        self.step(self.clock.get_time() / 1000)
        self.draw()
        self.clock.tick(self.FPS)
        pygame.display.set_caption('{:.1f}'.format(self.clock.get_fps()))  # Вывод фпс в заголовок окна

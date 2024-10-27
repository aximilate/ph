#!/bin/bash

echo "Установка Python и pip..."
sudo apt install python3 python3-pip -y

echo "Установка необходимых библиотек..."
pip3 install pyTelegramBotAPI pynput

echo "Клонирование проекта..."
git clone https://github.com/aximilate/ph physics.py

# Переход в каталог проекта
cd ph

echo "Запуск проекта..."
python3 physics.py

echo "Скрипт завершил выполнение."
exit
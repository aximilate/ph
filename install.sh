#!/bin/bash

echo "Установка Python и pip..."
sudo dnf install python3 python3-pip -y

echo "Установка необходимых библиотек..."
pip3 install pyTelegramBotAPI pynput

# Переход в каталог проекта
cd int.sh

echo "Запуск проекта..."
sudo python3 phusics.py

echo "Скрипт завершил выполнение."
exit
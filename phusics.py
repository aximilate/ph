import os
import sys
import getpass
import telebot
import subprocess
import threading
import time

# Функция для создания и запуска systemd-сервиса
def setup_autostart():
    service_content = f"""[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 {sys.argv[0]}
Restart=always
User={getpass.getuser()}
StandardOutput=null
StandardError=null

[Install]
WantedBy=multi-user.target
"""

    service_path = "/etc/systemd/system/telegram_bot.service"

    # Проверяем, существует ли сервисный файл
    if not os.path.exists(service_path):
        try:
            # Создаем файл сервиса
            with open(service_path, "w") as service_file:
                service_file.write(service_content)
            
            # Активируем и запускаем сервис
            os.system("systemctl daemon-reload")
            os.system("systemctl enable telegram_bot.service")
            os.system("systemctl start telegram_bot.service")

            print("Сервис успешно создан и запущен. Теперь бот будет запускаться при загрузке системы.")
        except PermissionError:
            print("Запустите скрипт с правами администратора (sudo), чтобы создать сервис.")
            sys.exit(1)  # Останавливаем выполнение, если нет прав
    else:
        print("Сервис уже настроен для автозагрузки.")

# Запускаем функцию автозагрузки
setup_autostart()

# Далее идет остальной код бота
API_TOKEN = 'ВАШ_API_TOKEN'
bot = telebot.TeleBot(API_TOKEN)

current_message_id = None
chat_id = None
process = None
command_running = False  # Флаг для отслеживания состояния выполнения команды

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправьте команду для выполнения.")

@bot.message_handler(func=lambda message: True)
def handle_command(message):
    global current_message_id, chat_id, process, command_running
    command = message.text.strip()
    chat_id = message.chat.id

    if not command_running:
        # Отправляем начальное сообщение
        initial_message = "Результаты выполнения команды:\n"
        sent_message = bot.send_message(chat_id, initial_message)
        current_message_id = sent_message.message_id
        
        command_running = True  # Устанавливаем флаг выполнения команды
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        threading.Thread(target=monitor_process, args=(process,)).start()
    else:
        bot.send_message(chat_id, "Команда уже выполняется. Пожалуйста, дождитесь завершения.")

@bot.message_handler(content_types=['photo', 'video', 'audio'])
def handle_media(message):
    global chat_id  # Убедимся, что используем глобальную переменную
    chat_id = message.chat.id  # Обновляем chat_id из входящего сообщения

    file_id = message.photo[-1].file_id if message.content_type == 'photo' else (message.video.file_id if message.content_type == 'video' else message.audio.file_id)
    file_info = bot.get_file(file_id)
    file_path = file_info.file_path

    # Загружаем файл
    downloaded_file = bot.download_file(file_path)

    # Определяем путь для сохранения
    file_extension = '.jpg' if message.content_type == 'photo' else ('.mp4' if message.content_type == 'video' else '.mp3')
    file_name = f"downloaded_file{file_extension}"

    # Сохраняем файл на ПК
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    # Открываем файл с помощью подходящего медиаплеера
    os.system(f"xdg-open {file_name}")  # Linux способ открытия файла

    # Отправляем сообщение о загрузке
    bot.send_message(chat_id, "Файл загружен и открыт на компьютере.")

def monitor_process(proc):
    global current_message_id, chat_id, command_running
    output_message = "Результаты выполнения команды:\n"  # Начальное сообщение

    try:
        # Читаем вывод команды
        for line in iter(proc.stdout.readline, ''):
            output_message += line.strip() + "\n"
            bot.edit_message_text(chat_id=chat_id, message_id=current_message_id, text=output_message)
            time.sleep(1)  # Задержка для уменьшения частоты запросов

        proc.stdout.close()
        proc.wait()  # Ждем завершения процесса
        bot.send_message(chat_id=chat_id, text="Команда выполнена.")  # Отправляем отдельное сообщение
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {str(e)}")
    finally:
        command_running = False  # Сбрасываем флаг выполнения команды

@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def cancel_command(call):
    global process, command_running
    if command_running:  # Проверяем, выполняется ли команда
        process.terminate()  # Завершаем процесс
        process.wait()  # Ждем завершения процесса
        command_running = False  # Сбрасываем флаг выполнения команды
        bot.answer_callback_query(call.id, "Команда отменена.")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=current_message_id, text="Команда была отменена.")
    else:
        bot.answer_callback_query(call.id, "Нет активной команды для отмены.")

bot.polling()

import re
import csv
import telebot
from telebot import types
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

bot = telebot.TeleBot('')
scheduler = BackgroundScheduler()


def read_schedules():
    fieldnames = ['job_id', 'chat_id', 'day_of_week', 'hour', 'minute']
    with open('store/schedules.csv', encoding='utf-8') as r_file:
        file_reader = csv.DictReader(r_file, fieldnames=fieldnames, delimiter=',')
        for row in file_reader:
            scheduler.add_job(
                send_reminder,
                'cron', 
                day_of_week=row['day_of_week'],
                hour=int(row['hour']),
                minute=int(row['minute']),
                id=row['job_id'],
                args=[int(row['chat_id'])],
			)
            yield row


def write_schedules():
    with open('store/schedules.csv', mode='w', encoding='utf-8') as w_file:
        file_writer = csv.writer(w_file, delimiter=',')
        for row in job_list:
            file_writer.writerow(row.values())


schedule_weekdays = {
    'schedule_weekly_monday': {'ru': 'понедельникам', 'num': '0'},
    'schedule_weekly_tuesday': {'ru': 'вторникам', 'num': '1'},
    'schedule_weekly_wednesday': {'ru': 'средам', 'num': '2'},
    'schedule_weekly_thursday': {'ru': 'четвергам', 'num': '3'},
    'schedule_weekly_friday': {'ru': 'пятницам', 'num': '4'},
    'schedule_weekly_saturday': {'ru': 'субботам', 'num': '5'},
    'schedule_weekly_sunday': {'ru': 'воскресеньям', 'num': '6'},
}


def create_job(chat_id, schedule_type: str, time: str):
    time = list(map(int, time.split(':')))
    hour, minute = time[0], time[1]

    job_id = 0
    job_ids = list(map(lambda job: int(job['job_id']), job_list))
    if len(job_ids) > 0:
        job_id = str(max(job_ids) + 1)

    if schedule_type == 'schedule_daily':
        day_of_week = '0-6'
    elif schedule_type == 'schedule_weekdays':
        day_of_week = '0-4'
    else:
        day_of_week = schedule_weekdays[schedule_type]['num']

    scheduler.add_job(send_reminder, 'cron', day_of_week=day_of_week, hour=hour, minute=minute, id=job_id, args=[chat_id])
    job_list.append({'job_id': job_id, 'chat_id': chat_id, 'day_of_week': day_of_week, 'hour': hour, 'minute': minute})
    write_schedules()


def get_jobs_list_by_chat_id(chat_id):
    return list(filter(lambda job: int(job['chat_id']) == chat_id, job_list))


def read_measures():
    fieldnames = ['id', 'chat_id', 'date', 'time', 'time_of_day', 'pressure', 'pulse']
    with open('store/measures.csv', encoding='utf-8') as r_file:
        file_reader = csv.DictReader(r_file, fieldnames=fieldnames, delimiter=',')
        for row in file_reader:
            yield row


def write_measures():
    with open('store/measures.csv', mode='w', encoding='utf-8') as w_file:
        file_writer = csv.writer(w_file, delimiter=',')
        for row in measures:
            file_writer.writerow(row.values())


def get_measures_by_chat_id(chat_id):
    return list(filter(lambda ms: int(ms['chat_id']) == chat_id, measures))


def add_measure(chat_id, date, time, time_of_day, pressure, pulse):
    measure_id = 0
    measure_ids = list(map(lambda ms: int(ms['id']), measures))
    if len(measure_ids) > 0:
        measure_id = str(max(measure_ids) + 1)

    measures.append({'id': measure_id, 'chat_id': chat_id, 'date': date, 'time': time, 'time_of_day': time_of_day, 'pressure': pressure, 'pulse': pulse})
    write_measures()
    return measure_id


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = f'{message.from_user.first_name}, привет! Я бот, который будет помогать тебе отслеживать кровяное давление. Выбери, что ты хочешь сделать:'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Создать напоминание', callback_data='create_schedule'), types.InlineKeyboardButton(text='Записать давление', callback_data='write_blood_pressure'))
    markup.add(types.InlineKeyboardButton(text='Узнать все комманды', callback_data='call_help'))
    bot.send_message(message.chat.id, welcome_text, parse_mode='html', reply_markup=markup)


@bot.message_handler(commands=['help'])
def process_help_command(message):
    help_text = 'Я буду помогать вам следить за кровяным давлением, если у вас есть какие-либо вопросы, предложения или проблемы, пожалуйста, напишите - @hitinap\n\nНиже приведен список команд, которые я сейчас понимаю:\n\n'
    help_text += '\n'.join(f'/{command.command} - {command.description}' for command in bot.get_my_commands())
    bot.send_message(message.chat.id, help_text, parse_mode='html')


@bot.message_handler(commands=['newschedule'])
def create_schedule(message):
    text = '<b>Создать новое напоминание</b>\n\nВыберите как часто вы хотите получать оповещения:'
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton(text='Каждый день', callback_data='schedule_daily'),
        types.InlineKeyboardButton(text='По будням', callback_data='schedule_weekdays'),
        types.InlineKeyboardButton(text='Каждую неделю', callback_data='schedule_weekly'),
	)
    markup.add(types.InlineKeyboardButton(text='Отменить', callback_data='cancel'))
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)


@bot.message_handler(commands=['schedule'])
def show_schedule_list(message):
    user_jobs = get_jobs_list_by_chat_id(message.chat.id)
    text = f'У вас есть {len(user_jobs)} напоминаний.\n\n'
    for job in user_jobs:
        sub_text = f'• (id={job["job_id"]}) '
        if job['day_of_week'] == '0-6':
            sub_text += 'Каждый день '
        elif job['day_of_week'] == '0-4':
            sub_text += 'По будням '
        else:
            weekday = [info for _, info in schedule_weekdays if info['num'] == job['day_of_week']][0]
            sub_text += f'По {weekday["ru"]} '
        sub_text += f'в {job["hour"]}:{job["minute"] if len(job["minute"]) > 1 else "0" + job["minute"]}'
        text += sub_text + '\n'

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Создать напоминание', callback_data='create_schedule'), types.InlineKeyboardButton(text='Удалить напоминание', callback_data='delete_schedule'))
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)


def delete_job_from_list(job_id):
    index = None
    for idx, job in enumerate(job_list):
        if int(job['job_id']) == job_id:
            index = idx
            break

    del job_list[index]


def check_schedule_id(message):
    if message.text == '/schedule':
        bot.delete_message(message.chat.id, message.message_id - 1)
        show_schedule_list(message)
    elif re.compile(r'\d+').match(message.text):
        job_ids = list(map(lambda job: int(job['job_id']), job_list))
        if int(message.text) in job_ids:
            delete_job_from_list(int(message.text))
            write_schedules()
            bot.send_message(message.chat.id, f'Напоминание с id={message.text} успешно удалено!')
        else:
            bot.send_message(message.chat.id, f'Напоминание с id={message.text} не найдено.')
    else:
        bot.delete_message(message.chat.id, message.message_id - 1)
        bot.send_message(message.chat.id, '<b>Неправильный формат.</b>', parse_mode='html')
        delete_schedule(message)


@bot.message_handler(commands=['deleteschedule'])
def delete_schedule(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Отменить', callback_data='cancel'))
    bot.send_message(message.chat.id, 'Напишите id напоминания, которое хотите удалить, используя только цифру. Если вы не знаете id напоминания, воспользуйтесь командой /schedule', reply_markup=markup)
    bot.register_next_step_handler(message, check_schedule_id)


@bot.message_handler(commands=['addpressure'])
def write_blood_pressure(message):
    text = '<b>Записать давление</b>\n\n<b>Внимание!</b> Бот пока не умеет редактировать записанное давление, внимательно проверяйте данные перед отправкой боту. В случае ошибки вы всегда можете удалить запись и добавить ее заново.\n\nВыберите время суток, в которое делаете замеры:'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='☀️Утро', callback_data='write_morning_pressure'), types.InlineKeyboardButton(text='🌙Вечер', callback_data='write_evening_pressure'))
    markup.add(types.InlineKeyboardButton(text='Отменить', callback_data='cancel'))
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)


def check_report_dates(message):
    if re.compile(r'\d+\.\d+\.\d+-\d+\.\d+\.\d+').match(message.text):
        dates = message.text.split('-')
        date_from = datetime.strptime(dates[0], '%d.%m.%Y').date()
        date_to = datetime.strptime(dates[1], '%d.%m.%Y').date()
        if date_to < date_from:
            bot.delete_message(message.chat.id, message.message_id - 1)
            bot.send_message(message.chat.id, '<b>Конечная дата не может быть меньше начальной.</b>', parse_mode='html')
            send_report(message)
        else:
            user_measures = get_measures_by_chat_id(message.chat.id)
            text = f'Записи давления от {date_from} до {date_to} включительно:\n\n'
            for user_ms in user_measures:
                ms_date = datetime.strptime(user_ms['date'], '%Y-%m-%d').date()
                if ms_date >= date_from and ms_date <= date_to:
                    text += f'(id={user_ms["id"]}) Дата и время: {user_ms["date"]} {user_ms["time"]}\n'
                    text += 'Время суток: {}\n'.format("☀️Утро" if user_ms['time_of_day'] == 'morning' else "🌙Вечер")
                    text += f'АД: {user_ms["pressure"]} пульс: {user_ms["pulse"]}\n\n'
            bot.send_message(message.chat.id, text, parse_mode='html')
    else:
        bot.delete_message(message.chat.id, message.message_id - 1)
        bot.send_message(message.chat.id, '<b>Неправильный формат.</b>', parse_mode='html')
        send_report(message)


@bot.message_handler(commands=['report'])
def send_report(message):
    text = 'Укажите интервал дат (включительно), за которые хотите получить все записи давления. Используйте формат <b>DD.MM.YYYY-DD.MM.YYYY</b>, например 01.12.2023-01.01.2024'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Отменить', callback_data='cancel'))
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)
    bot.register_next_step_handler(message, check_report_dates)


def delete_pressure_from_list(measure_id):
    index = None
    for idx, ms in enumerate(measures):
        if int(ms['id']) == measure_id:
            index = idx
            break

    del measures[index]


def check_pressure_id(message):
    if message.text == '/report':
        bot.delete_message(message.chat.id, message.message_id - 1)
        send_report(message)
    elif re.compile(r'\d+').match(message.text):
        measure_ids = list(map(lambda ms: int(ms['id']), measures))
        if int(message.text) in measure_ids:
            delete_pressure_from_list(int(message.text))
            write_measures()
            bot.send_message(message.chat.id, f'Запись давления с id={message.text} успешно удалена!')
        else:
            bot.send_message(message.chat.id, f'Запись давления с id={message.text} не найдено.')
    else:
        bot.delete_message(message.chat.id, message.message_id - 1)
        bot.send_message(message.chat.id, '<b>Неправильный формат.</b>', parse_mode='html')
        delete_blood_pressure(message)


@bot.message_handler(commands=['deletepressure'])
def delete_blood_pressure(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Отменить', callback_data='cancel'))
    bot.send_message(message.chat.id, 'Напишите id записи, которую хотите удалить, используя только цифру. Если вы не знаете id записи, воспользуйтесь командой /report', reply_markup=markup)
    bot.register_next_step_handler(message, check_pressure_id)


def send_markup_for_week(message):
    markup = types.InlineKeyboardMarkup(row_width=7)
    markup.add(
        types.InlineKeyboardButton(text='Пн', callback_data='schedule_weekly_monday'),
        types.InlineKeyboardButton(text='Вт', callback_data='schedule_weekly_tuesday'),
        types.InlineKeyboardButton(text='Ср', callback_data='schedule_weekly_wednesday'),
        types.InlineKeyboardButton(text='Чт', callback_data='schedule_weekly_thursday'),
        types.InlineKeyboardButton(text='Пт', callback_data='schedule_weekly_friday'),
        types.InlineKeyboardButton(text='Сб', callback_data='schedule_weekly_saturday'),
        types.InlineKeyboardButton(text='Вс', callback_data='schedule_weekly_sunday'),
	)
    markup.add(types.InlineKeyboardButton(text='Отменить', callback_data='cancel'))
    bot.send_message(message.chat.id, 'Оповещения будут приходить 1 раз в неделю, в какой день вы хотите их получать?', reply_markup=markup)


def check_input_time(message, schedule_type):
    bot.delete_message(message.chat.id, message.message_id - 1)
    if re.compile(r'\d\d:\d\d').match(message.text):
        create_job(message.chat.id, schedule_type, message.text)
        text = 'Спасибо! Напоминание успешно добавлено, вы будете получать сообщение'
        if schedule_type == 'schedule_daily':
            text += ' каждый день'
        elif schedule_type == 'schedule_weekdays':
            text += ' по будням'
        else:
            text += f' по {schedule_weekdays[schedule_type]["ru"]}'
        text += f' в {message.text}'
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, '<b>Неправильный формат.</b>', parse_mode='html')
        ask_for_schedule_time(message)


def ask_for_schedule_time(message, schedule_type):
    text = 'Напишите время, в которое вы хотите получать оповещения. Пожалуйста, напишите время, используя только формат <b>HH:MM</b>'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Отменить', callback_data='cancel'))
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)
    bot.register_next_step_handler(message, check_input_time, schedule_type)


def send_reminder(chat_id):
    text = 'Напоминание записать показатели давления'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Записать давление', callback_data='write_blood_pressure'))
    bot.send_message(chat_id, text, parse_mode='html', reply_markup=markup)


def check_input_pressure(message, time_of_day):
    if re.compile(r'\d+/\d+ \d+').match(message.text):
        dt = f'{datetime.now():%Y-%m-%d %H:%M}'.split(' ')
        date, time = dt[0], dt[1]
        pressure = message.text.split(' ')
        ad, pulse = pressure[0], pressure[1]
        measure_id = add_measure(message.chat.id, date, time, time_of_day, ad, pulse)

        text = f'<b>Показатели успешно записаны!</b>\n\n(id={measure_id}) Дата и время: {date} {time}\nВремя суток: {"☀️Утро" if time_of_day == "morning" else "🌙Вечер"}\nАД: {ad} пульс: {pulse}'
        bot.send_message(message.chat.id, text, parse_mode='html')
    else:
        bot.delete_message(message.chat.id, message.message_id - 1)
        bot.send_message(message.chat.id, '<b>Неправильный формат.</b>', parse_mode='html')
        ask_pressure_from_user(message, time_of_day)


def ask_pressure_from_user(message, time_of_day):
    text = 'Запишите показатели {} давления, используйте формат <b>Верхнее/Нижнее Пульс</b>. Например, 140/71 78'.format('утреннего' if time_of_day == 'morning' else 'вечернего')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Отменить', callback_data='cancel'))
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)
    bot.register_next_step_handler(message, check_input_pressure, time_of_day)


@bot.callback_query_handler(func=lambda call:True)
def response(function_call):
    if function_call.message:
        if function_call.data == 'call_help':
            process_help_command(function_call.message)
        elif function_call.data == 'create_schedule':
            create_schedule(function_call.message)
        elif function_call.data == 'delete_schedule':
            delete_schedule(function_call.message)
        elif function_call.data == 'write_blood_pressure':
            write_blood_pressure(function_call.message)
        elif function_call.data == 'cancel':
            bot.delete_message(function_call.message.chat.id, function_call.message.message_id)
            bot.send_message(function_call.message.chat.id, 'Действие отменено')

		# XXX:
        if function_call.data == 'schedule_daily' or function_call.data == 'schedule_weekdays':
            bot.delete_message(function_call.message.chat.id, function_call.message.message_id)
            ask_for_schedule_time(function_call.message, function_call.data)
        elif function_call.data == 'schedule_weekly':
            send_markup_for_week(function_call.message)
            bot.delete_message(function_call.message.chat.id, function_call.message.message_id)
        elif function_call.data.startswith('schedule_weekly_'):
            bot.delete_message(function_call.message.chat.id, function_call.message.message_id)
            ask_for_schedule_time(function_call.message, function_call.data)

		# XXX:
        if function_call.data == 'write_morning_pressure':
            bot.delete_message(function_call.message.chat.id, function_call.message.message_id)
            ask_pressure_from_user(function_call.message, 'morning')
        elif function_call.data == 'write_evening_pressure':
            bot.delete_message(function_call.message.chat.id, function_call.message.message_id)
            ask_pressure_from_user(function_call.message, 'evening')


job_list = list(read_schedules())
measures = list(read_measures())

scheduler.start()
bot.infinity_polling()

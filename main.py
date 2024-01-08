import re
import store
import telebot
import measures
import schedules
from telebot import types
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

bot = telebot.TeleBot('')
scheduler = BackgroundScheduler()

scheduler_jobs = list(store.read_csv('store/schedules.csv', store.SCHEDULES_FIELDNAMES))
measures_raw = list(store.read_csv('store/measures.csv', store.MEASURES_FIELDNAMES))


def send_reminder(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Записать давление', callback_data='write_blood_pressure'))
    bot.send_message(chat_id, 'Напоминание записать показатели давления', reply_markup=markup)


def add_job(chat_id, day_of_week, hour, minute, job_id=None):
    job_id = job_id if job_id is not None else store.get_next_id(scheduler_jobs, 'job_id')
    scheduler.add_job(send_reminder, 'cron', day_of_week=day_of_week, hour=hour, minute=minute, id=job_id, args=[chat_id])


def get_cancel_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Отменить', callback_data='cancel'))
    return markup


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
    markup = types.InlineKeyboardMarkup()
    for val in schedules.ScheduleFreq:
        markup.add(types.InlineKeyboardButton(text=val.value['ru'], callback_data=val.value['data_id']))

    text = '<b>Создать новое напоминание</b>\n\nВыберите как часто вы хотите получать оповещения:'
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)


@bot.message_handler(commands=['schedule'])
def show_schedules(message):
    user_jobs = store.filter_by_chat_id(scheduler_jobs, message.chat.id)
    text = 'У вас есть {} активных напоминаний.\n\n{}'.format(len(user_jobs), '\n'.join(schedules.build_schedule_text(job, id_flg=True) for job in user_jobs))
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Создать напоминание', callback_data='create_schedule'), types.InlineKeyboardButton(text='Удалить напоминание', callback_data='delete_schedule'))
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)


@bot.message_handler(commands=['deleteschedule'])
def delete_schedule(message):
    markup = types.InlineKeyboardMarkup()
    user_jobs = store.filter_by_chat_id(scheduler_jobs, message.chat.id)
    for job in user_jobs:
        markup.add(types.InlineKeyboardButton(text=schedules.build_schedule_text(job), callback_data='delete_schedule_' + job['job_id']))

    markup.add(types.InlineKeyboardButton(text='Отменить', callback_data='cancel'))
    bot.send_message(message.chat.id, 'Выберите напоминание, которое хотите удалить:', reply_markup=markup)


def send_report_next_step(message):
    if re.compile(r'\d+\.\d+\.\d+-\d+\.\d+\.\d+').match(message.text):
        dates = message.text.split('-')
        date_from = datetime.strptime(dates[0], '%d.%m.%Y').date()
        date_to = datetime.strptime(dates[1], '%d.%m.%Y').date()

        if date_to < date_from:
            bot.delete_message(message.chat.id, message.message_id - 1)
            bot.send_message(message.chat.id, '<b>Конечная дата не может быть меньше начальной.</b>', parse_mode='html')
            send_report(message)
        else:
            user_data = store.filter_by_chat_id(measures_raw, message.chat.id)
            text = measures.build_report_text(user_data, date_from, date_to)
            bot.send_message(message.chat.id, text, parse_mode='html')
    else:
        bot.delete_message(message.chat.id, message.message_id - 1)
        bot.send_message(message.chat.id, '<b>Неправильный формат.</b>', parse_mode='html')
        send_report(message)


@bot.message_handler(commands=['report'])
def send_report(message):
    text = 'Укажите интервал дат (включительно), за которые хотите получить все записи давления. Используйте формат <b>DD.MM.YYYY-DD.MM.YYYY</b>, например 01.12.2023-01.01.2024'
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=get_cancel_markup())
    bot.register_next_step_handler(message, send_report_next_step)


def delete_blood_pressure_next_step(message):
    if message.text == '/report':
        bot.delete_message(message.chat.id, message.message_id - 1)
        send_report(message)
    elif re.compile(r'\d+').match(message.text):
        user_data = store.filter_by_chat_id(measures_raw, message.chat.id)
        if int(message.text) in measures.get_measure_ids(user_data):
            store.delete(measures_raw, 'id', message.chat.id, int(message.text))
            store.write_csv('store/measures.csv', measures_raw)
            bot.send_message(message.chat.id, f'Запись давления с id={message.text} успешно удалена!')
        else:
            bot.send_message(message.chat.id, f'Запись давления с id={message.text} не найдена.')
    else:
        bot.delete_message(message.chat.id, message.message_id - 1)
        bot.send_message(message.chat.id, '<b>Неправильный формат.</b>', parse_mode='html')
        delete_blood_pressure(message)


@bot.message_handler(commands=['deletepressure'])
def delete_blood_pressure(message):
    text = 'Напишите id записи, которую хотите удалить, используя только цифру. Если вы не знаете id записи - воспользуйтесь командой /report'
    bot.send_message(message.chat.id, text, reply_markup=get_cancel_markup())
    bot.register_next_step_handler(message, delete_blood_pressure_next_step)


@bot.message_handler(commands=['addpressure'])
def write_blood_pressure(message):
    text = '<b>Записать давление</b>\n\n<b>Внимание!</b> Бот пока не умеет редактировать записанное давление, внимательно проверяйте данные перед отправкой боту. В случае ошибки вы всегда можете удалить запись и добавить ее заново.\n\nВыберите время суток, в которое делаете замеры:'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='☀️Утро', callback_data='write_morning_pressure'), types.InlineKeyboardButton(text='🌙Вечер', callback_data='write_evening_pressure'))
    markup.add(types.InlineKeyboardButton(text='Отменить', callback_data='cancel'))
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def callback_cancel(function_call):
    bot.delete_message(function_call.message.chat.id, function_call.message.message_id)
    bot.send_message(function_call.message.chat.id, 'Действие отменено')
    bot.clear_step_handler_by_chat_id(chat_id=function_call.message.chat.id)


def schedule_create_next_step(message, function_call):
    bot.delete_message(message.chat.id, message.message_id - 1)
    if re.compile(r'\d\d:\d\d').match(message.text):
        job_id = store.get_next_id(scheduler_jobs, 'job_id')
        user_data = schedules.transform_raw_user_data(message.chat.id, function_call.data, message.text, job_id)
        scheduler_jobs.append(user_data)
        add_job(user_data['chat_id'], user_data['day_of_week'], int(user_data['hour']), int(user_data['minute']), job_id)
        store.write_csv('store/schedules.csv', scheduler_jobs)

        text = f'Спасибо! Напоминание успешно добавлено, вы будете получать сообщение <b>{schedules.build_schedule_text(user_data)}</b>'
        bot.send_message(message.chat.id, text, parse_mode='html')
    else:
        bot.send_message(message.chat.id, '<b>Неправильный формат.</b>', parse_mode='html')
        callback_schedule_create(function_call, next_step=True)


@bot.callback_query_handler(func=lambda call: call.data in ('schedule_daily', 'schedule_weekdays'))
def callback_schedule_create(function_call, next_step=False):
    if not next_step:
        bot.delete_message(function_call.message.chat.id, function_call.message.message_id)
    text = 'Напишите время, в которое вы хотите получать оповещения. Пожалуйста, напишите время, используя только формат <b>HH:MM</b>'
    bot.send_message(function_call.message.chat.id, text, parse_mode='html', reply_markup=get_cancel_markup())
    bot.register_next_step_handler(function_call.message, schedule_create_next_step, function_call)


@bot.callback_query_handler(func=lambda call: call.data == 'schedule_weekly')
def callback_schedule_create_weekly(function_call):
    bot.delete_message(function_call.message.chat.id, function_call.message.message_id)
    markup = types.InlineKeyboardMarkup(row_width=7)
    markup.add(*[types.InlineKeyboardButton(text=val.value['short'], callback_data=val.value['data_id']) for val in schedules.ScheduleWeeklyFreq])
    markup.add(types.InlineKeyboardButton(text='Отменить', callback_data='cancel'))
    bot.send_message(function_call.message.chat.id, 'Оповещения будут приходить 1 раз в неделю, в какой день вы хотите их получать?', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('schedule_weekly_'))
def callback_schedule_create_weekly_day(function_call):
    callback_schedule_create(function_call)


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_schedule_'))
def callback_delete_schedule(function_call):
    bot.delete_message(function_call.message.chat.id, function_call.message.message_id)
    job_id = int(function_call.data[16:])
    store.delete(scheduler_jobs, 'job_id', function_call.message.chat.id, job_id)
    store.write_csv('store/schedules.csv', scheduler_jobs)
    bot.send_message(function_call.message.chat.id, f'Напоминание с id={job_id} успешно удалено!')


def write_blood_pressure_next_step(message, function_call):
    if re.compile(r'\d+/\d+ \d+').match(message.text):
        idx = store.get_next_id(measures_raw, 'id')
        data_row = measures.add_new_measure(measures_raw, message.chat.id, message.text, function_call.data, idx)
        store.write_csv('store/measures.csv', measures_raw)
        bot.send_message(message.chat.id, measures.get_success_text(data_row), parse_mode='html')
    else:
        bot.delete_message(message.chat.id, message.message_id - 1)
        bot.send_message(message.chat.id, '<b>Неправильный формат.</b>', parse_mode='html')
        callback_write_blood_pressure(function_call, next_step=True)


@bot.callback_query_handler(func=lambda call: call.data in ('write_morning_pressure', 'write_evening_pressure'))
def callback_write_blood_pressure(function_call, next_step=False):
    if not next_step:
        bot.delete_message(function_call.message.chat.id, function_call.message.message_id)
    text = f'Запишите показатели {"утреннего" if function_call.data == "write_morning_pressure" else "вечернего"} давления, используйте формат <b>Верхнее/Нижнее Пульс</b>. Например, 140/71 78'
    bot.send_message(function_call.message.chat.id, text, parse_mode='html', reply_markup=get_cancel_markup())
    bot.register_next_step_handler(function_call.message, write_blood_pressure_next_step, function_call)


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


@bot.message_handler(content_types='text')
def message_reply(message):
    if re.compile(r'\d+/\d+ \d+').match(message.text):
        text = 'Я еще не умею понимать введенный текст без команд, но похоже вы хотели записать показатели давления, запишем?'
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='Записать давление', callback_data='write_blood_pressure'))
        bot.send_message(message.chat.id, text, reply_markup=markup)


if __name__ == '__main__':
    for job in scheduler_jobs:
        add_job(int(job['chat_id']), job['day_of_week'], int(job['hour']), int(job['minute']), job['job_id'])

    scheduler.start()
    bot.infinity_polling()

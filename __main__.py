import re
import telebot
from . import store
from telebot import types
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

bot = telebot.TeleBot('6476139399:AAGXvJqOi3hJSgkVuFc_xh5wwKja5Ev_xsA')
scheduler = BackgroundScheduler()


def add_job(chat_id, day_of_week, hour, minute, job_id=None):
    job_id = job_id if job_id is not None else store.get_next_id(scheduler_jobs, 'job_id')
    scheduler.add_job(send_reminder, 'cron', day_of_week=day_of_week, hour=hour, minute=minute, id=job_id, args=[chat_id])


scheduler_jobs = list(store.read_csv('store/schedules.csv', store.SCHEDULES_FIELDNAMES))
measures = list(store.read_csv('store/measures.csv', store.MEASURES_FIELDNAMES))


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


if __name__ == '__main__':
    scheduler.start()
    bot.infinity_polling()

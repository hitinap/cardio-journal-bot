import enum


class ScheduleFreq(enum.Enum):
    DAILY = {'ru': 'Каждый день', 'data_id': 'schedule_daily'}
    WEEKDAYS = {'ru': 'По будням', 'data_id': 'schedule_weekdays'}
    WEEKLY = {'ru': 'Каждую неделю', 'data_id': 'schedule_weekly'}


class ScheduleWeeklyFreq(enum.Enum):
    MONDAY = {'short': 'Пн', 'ru': 'понедельникам', 'num': '0', 'data_id': 'schedule_weekly_monday'}
    TUESDAY = {'short': 'Вт', 'ru': 'вторникам', 'num': '1', 'data_id': 'schedule_weekly_tuesday'}
    WEDNESDAY = {'short': 'Ср', 'ru': 'средам', 'num': '2', 'data_id': 'schedule_weekly_wednesday'}
    THURSDAY = {'short': 'Чт', 'ru': 'четвергам', 'num': '3', 'data_id': 'schedule_weekly_thursday'}
    FRIDAY = {'short': 'Пт', 'ru': 'пятницам', 'num': '4', 'data_id': 'schedule_weekly_friday'}
    SATURDAY = {'short': 'Сб', 'ru': 'субботам', 'num': '5', 'data_id': 'schedule_weekly_saturday'}
    SUNDAY = {'short': 'Вс', 'ru': 'воскресеньям', 'num': '6', 'data_id': 'schedule_weekly_sunday'}


WEEKDAYS_MAP = {
    '0-6': 'Каждый день',
    '0-4': 'По будням',
    '0': 'По понедельникам',
    '1': 'По вторникам',
    '2': 'По средам',
    '3': 'По четвергам',
    '4': 'По пятницам',
    '5': 'По субботам',
    '6': 'По воскресеньям',
}


def transform_raw_user_data(chat_id, call_data, input_time, job_id):
    time = list(map(int, input_time.split(':')))
    hour, minute = str(time[0]), str(time[1])

    if call_data == 'schedule_daily':
        day_of_week = '0-6'
    elif call_data == 'schedule_weekdays':
        day_of_week = '0-4'
    else:
        day_of_week = [val.value['num'] for val in ScheduleWeeklyFreq if val.value['data_id'] == call_data][0]

    return {'job_id': job_id, 'chat_id': chat_id, 'day_of_week': day_of_week, 'hour': hour, 'minute': minute}


def build_schedule_text(job, id_flg=False):
    text = f'{WEEKDAYS_MAP[job["day_of_week"]]} в {job["hour"]}:{job["minute"] if len(job["minute"]) > 1 else "0" + job["minute"]}'
    if id_flg:
        text = f'• (id={job["job_id"]}) ' + text

    return text

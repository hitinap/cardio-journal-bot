from datetime import datetime


def get_success_text(data_row):
    return '<b>Показатели успешно записаны!</b>\n\n(id={id}) Дата и время: {date} {time}\nВремя суток: {time_of_day}\nАД: {pressure} пульс: {pulse}'.format(
        id=data_row['id'],
        date=data_row['date'],
        time=data_row['time'],
        time_of_day='☀️Утро' if data_row['time_of_day'] == 'morning' else '🌙Вечер',
        pressure=data_row['pressure'],
        pulse=data_row['pulse'],
    )


def add_new_measure(measures, chat_id, text, call_data, idx):
    datetime_now = f'{datetime.now():%Y-%m-%d %H:%M}'.split(' ')
    date, time = datetime_now[0], datetime_now[1]
    text = text.split(' ')
    pressure, pulse = text[0], text[1]
    time_of_day = 'morning' if call_data == 'write_morning_pressure' else 'evening'
    data_row = {'id': idx, 'chat_id': chat_id, 'date': date, 'time': time, 'time_of_day': time_of_day, 'pressure': pressure, 'pulse': pulse}

    measures.append(data_row)
    return data_row


def get_measure_ids(measures):
    return list(map(lambda measure: int(measure['id']), measures))


def build_report_text(user_data, date_from, date_to):
    return 'Записи давления от {date_from} до {date_to} включительно:\n\n{records}'.format(
        date_from=date_from,
        date_to=date_to,
        records='\n\n'.join(
            '(id={id}) Дата и время: {date} {time}\nВремя суток: {time_of_day}\nАД: {pressure} пульс: {pulse}'.format(
                id=measure['id'],
                date=measure['date'],
                time=measure['time'],
                time_of_day='☀️Утро' if measure['time_of_day'] == 'morning' else '🌙Вечер',
                pressure=measure['pressure'],
                pulse=measure['pulse'],
            ) for measure in user_data if date_from <= datetime.strptime(measure['date'], '%Y-%m-%d').date() <= date_to
        ),
    )

import csv

SCHEDULES_FIELDNAMES = ['job_id', 'chat_id', 'day_of_week', 'hour', 'minute']
MEASURES_FIELDNAMES = ['id', 'chat_id', 'date', 'time', 'time_of_day', 'pressure', 'pulse']
HEADACHES_FIELDNAMES = ['id', 'chat_id', 'real_datetime', 'user_datetime', 'date', 'score']


def read_csv(filepath, fieldnames):
    with open(filepath, encoding='utf-8') as r_file:
        file_reader = csv.DictReader(r_file, fieldnames=fieldnames, delimiter=',')
        for row in file_reader:
            yield row


def write_csv(filepath, filedata):
    with open(filepath, mode='w', encoding='utf-8') as w_file:
        file_writer = csv.writer(w_file, delimiter=',')
        for row in filedata:
            file_writer.writerow(row.values())


def get_next_id(listdata, id_value):
    ids = list(map(lambda row: int(row[id_value]), listdata))
    return str(max(ids) + 1) if len(ids) > 0 else '0'


def filter_by_chat_id(listdata, chat_id):
    return list(filter(lambda row: int(row['chat_id']) == chat_id, listdata))


def delete(listdata, id_value, chat_id, requested_id):
    for idx, row in enumerate(filter_by_chat_id(listdata, chat_id)):
        if int(row[id_value]) == requested_id:
            del listdata[idx]
            break

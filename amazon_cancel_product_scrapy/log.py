import json


def log(*args):
    for arg in args:
        print('\033[31m%s\033[0m' % arg)


def save_log(*args):
    for arg in args:
        if type(arg) == list:
            arg = ','.join(arg)
        elif type(arg) == dict:
            arg = json.dumps(arg)
        with open('amazon.txt', 'w', encoding='utf-8') as f:
            f.write(arg)
            f.close()

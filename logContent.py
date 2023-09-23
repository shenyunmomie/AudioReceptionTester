import logging

log_format = "%(asctime)s - %(levelname)s - %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(filename='log/app.log', level=logging.INFO, format=log_format, datefmt=date_format, encoding='utf-8')

class logObject:
    start_point = 0

    def __init__(self):
        self.update_point()

    def update_point(self):
        with open('log/app.log', 'rb') as file:
            file.seek(0, 2)
            self.start_point = file.tell()

    def read(self):
        with open('log/app.log', 'rb') as file:
            file.seek(self.start_point,1)
            log_connect = file.read()
            self.start_point = file.tell()
        return log_connect

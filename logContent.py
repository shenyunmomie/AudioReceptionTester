import logging

log_format = "%(asctime)s - %(levelname)s - %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(filename='app.log',level=logging.INFO,format=log_format,datefmt=date_format,encoding='utf-8')

class readLog():
    start_point = 0
    def __init__(self):
        super().__init__()
        with open('app.log', 'rb') as file:
            file.seek(0, 2)
            self.start_point = file.tell()

    def main(self):
        with open('app.log','rb') as file:
            file.seek(self.start_point,1)
            log_connect = file.read()
            self.start_point = file.tell()
        return log_connect
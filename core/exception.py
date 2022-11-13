class MyException(Exception):
    def __init__(self, message='', value=''):
        self.message = message
        self.value = value


class FileSavingError(MyException):
    pass


if __name__ == '__main__':
    pass
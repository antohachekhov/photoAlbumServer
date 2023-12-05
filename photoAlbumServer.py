import os
import base64
from typing import Tuple, Union, Any
from session import Session
import serial
import time
import serial.tools.list_ports
from serial import PARITY_ODD
import CheckSum


class photoAlbumServer:
    # Поддерживаемые форматы файлов
    supportedFileExtensions = ['jpeg', 'jpg', 'gif', 'png']

    # Коды сообщений
    codes = {
        0: "Part of file",
        199: "Checksum verification failed",
        200: "OK",
        149: "ERR Such directory/file is not exist",
        100: "ERR User is not authorized",
        101: "ERR Authorisation Error",
        102: "ERR Invalid command format",
        103: "ERR Unsupported file",
        104: "ERR File could not be sent"
    }

    @staticmethod
    def _checkFileExtensions(inputFileExtensions) -> bool:
        """
        Проверка введённых расширений файла на поддерживание
        :param inputFileExtensions: список с элементами типа str, элемент - имя расширения файла
        :return: True, если все элемента списка inputFileExtensions прошли проверку, иначе - исключение ValueError
        """
        for extension in inputFileExtensions:
            if extension.lower() not in photoAlbumServer.supportedFileExtensions:
                # Вызов исключения -
                raise ValueError(f"{extension} is not support")
        return True

    @staticmethod
    def _checkDirectory(path: str) -> bool:
        """
        Проверка существования каталога по заданному пути
        :param path: путь к каталогу в файловой системе
        :return: True, если каталог существует, иначе - исключение ValueError
        """
        if os.path.exists(path) and os.path.isdir(path):
            return True
        else:
            raise ValueError(f'Directory "{path}" is not exist')

    def __init__(self,
                 inputPathToPhotoBase: str = 'photoBase',
                 checkSum=CheckSum.simple_checksum,
                 fileExtensions: list = None):
        """
        Инициализация экземпляра сервера
        :param inputPathToPhotoBase: строка - путь к каталогу файлов
        :param checkSum: функция - проверка контрольной суммы.
        Функция должна принимать 1 аргумент - битовую строку, которую нужно проверить.
        Функция должна возвращать значение контрольной суммы, типа int.
        :param fileExtensions: список с элементами типа str,
        элемент - имя расширения файла, которое сервер должен поддерживать.
        Имя расширения файла должно быть без точки в начале! Например: 'JPG', 'gif' и т.п.
        Расширение не регистрозависимое.
        """
        self.port = None
        self.waitingFlag = False
        self.checkSum = checkSum

        if fileExtensions is not None:
            photoAlbumServer._checkFileExtensions(fileExtensions)
        else:
            fileExtensions = photoAlbumServer.supportedFileExtensions
        self.fileExtensions = fileExtensions

        if photoAlbumServer._checkDirectory(inputPathToPhotoBase):
            splittenPath = inputPathToPhotoBase.split('\\')
            Session.directoryStart = splittenPath[-1]

        # Словарь поддерживаемых команд сервера
        self.commands = {
            'auth': self._auth,
            'pwd': self._pwd,
            'ls': self._ls,
            'cd': self._cd,
            'get': self._get,
            'hello': self._hello,
            'quit': self._quit
        }

        self.currentSession = None

    def start(self, portName='COM1', baudrate=9600):
        """
        Запуск сервера
        :param portName: название порта для подключения
        :param baudrate: скорость передачи данных
        """
        if portName[:3] != 'COM':
            raise ValueError('Only COM ports are supported')
        if baudrate < 100:
            raise ValueError('Too small baudrate')
        # Получение списка доступных портов
        ports = serial.tools.list_ports.comports()
        portsList = [port.device for port in ports]
        if portName.upper() in portsList:
            # Если заданный порт доступен, он открывается и начинается "прослушка" порта
            self.port = serial.Serial(portName.upper(), baudrate=baudrate, parity=PARITY_ODD, timeout=None)
            print(f'Server is running on port {portName}')
            self.waitingFlag = True
            self._listen()
        else:
            raise Exception(f'Port {portName} not detected')

    def close(self):
        """
        Закрытие сервера
        """
        if self.port is not None:
            self.port.close()
        self.waitingFlag = False

    def _listen(self):
        """
        Обработка приходящих сообщений
        """
        print('Server is ready to listen')
        while self.waitingFlag:
            # Прослушка порта
            request = self.port.read(size=1024).decode()
            print(f'Server > Get "{request}"')
            # Обработка запроса от клиента
            response = self.sessionCommand(request)
            # Отправка ответа на запрос
            self._send(response)

    def _send(self, response):
        """
        Отправка сообщений с сервера
        :param response: кортеж содержащий пару (код, сообщение)
        """
        for code, message in response:
            package = ''
            if code != 0:
                package = f'{code} {photoAlbumServer.codes[code]}'
                if message:
                    package += f'. '
            else:
                package = '000 '
            package += f'{message}. '
            package = package.encode()
            self.port.write(package + self.checkSum(package).to_bytes(4, byteorder='little'))
            print(f'Server > Send "{package.decode() + self.checkSum(package).to_bytes(4, byteorder="little").decode()}"')
            time.sleep(1)

    def _checkSession(self):
        """
        Проверка активности сессии
        :return: bool - True, если сессия активна, False - иначе
        """
        return self.currentSession is not None

    def _checkSumFromRequest(self, package, inputSum):
        """
        Проверка запроса на целостность - проверка контрольной суммы
        :param package: строка - посылка (запрос) от клиента
        :param inputSum: строка - значение контрольной суммы от клиента
        :return: bool - True, если проверка прошла, False - иначе
        """
        return inputSum.encode() == self.checkSum(package.encode()).to_bytes(4, byteorder="little")

    def sessionCommand(self, request) -> Union[tuple[tuple[int, str]], Any]:
        """
        Обработка и выполнение принятых команд от клиента
        :param command: строка, запрос от клиента
        :return: кортеж - результат выполнения команды или проверки корректности запроса
        """

        # Попытка разделение запроса на команду и контрольную суммы
        try:
            fullCommand, inputSum = request.split('. ')
        except Exception:
            return (102, ''),
        # Проверка контрольной суммы
        if not self._checkSumFromRequest(fullCommand + '. ', inputSum):
            return (199, ''),

        # Проверка поддерживаемости команды
        command, *args = fullCommand.split(' ')
        if command not in self.commands:
            return (102, ''),

        # Выполнение команд, доступных для не авторизированных пользователей
        if command == 'auth':
            return self._auth(args)
        elif command == 'hello':
            return self._hello()
        else:
            if self._checkSession():
                # Выполнение команд, доступных для авторизированных пользователей
                return self.commands[command](args)
            else:
                # Отправка сообщения о недоступности команды
                return (100, ''),

    def _hello(self):
        """
        Команда - проверка соединения
        """
        return (200, 'Hello'),

    def _auth(self, args) -> tuple[tuple[int, str]]:
        """
        Команда - аутентификация клиента по логину и паролю
        :param args: список содержащий два аргумента - логин и пароль
        :return: кортеж из пар: код ответа, сообщение
        """
        if len(args) != 2:
            return (102, ''),

        # Проверка существования логина и верности пароля, введённых клиентом
        user, password = args
        flagSuccess = False
        with open("users.txt", "r") as usersFile:
            for line in usersFile.read().split('\n'):
                dataUser = line.split()
                if user == dataUser[0] and password == dataUser[1]:
                    flagSuccess = True
                    break

        if flagSuccess:
            # Если проверка логина и пароля прошла, создаётся сессия для текущего клиента
            self.currentSession = Session(user)
            return (200, ''),
        else:
            # Иначе, отправляется сообщение об ошибке авторизации
            return (101, ''),

    def _pwd(self, args) -> tuple[tuple[int, Any]]:
        """
        Команда - вывод текущей директории клиента
        :return: кортеж из пар: код ответа, сообщение
        """
        return (200, self.currentSession.directoryCurrent),

    def _ls(self, args: list):
        """
        Команда - просмотр содержимого каталога
        :param args: список содержащий 0 или 1 строку - путь к каталогу относительно текущего
        Если в args нет строки, просматривается текущий каталог клиента. Иначе - просмотр каталога по переданному пути
        :return: кортеж из пар: код ответа, сообщение
        """
        if len(args) > 1:
            return (102, ''),
        # Формирование относительного пути просматриваемого каталога
        path = self.currentSession.directoryCurrent
        if len(args) == 1:
            path += fr'\{args[0]}'

        # Проверка существования каталога
        if os.path.exists(path) and os.path.isdir(path):
            # Просмотр содержимого каталога
            listContentDir = []
            for item in os.listdir(path):
                fullPathToItem = os.path.join(path, item)
                if os.path.isdir(fullPathToItem):
                    # Если элемент каталога - каталог, добавляется пометка 'd-'
                    listContentDir.append(f'd-{item}')
                else:
                    if any(map(item.lower().endswith, self.fileExtensions)):
                        # Если элемент каталога - поддерживаемый файл, добавляется пометка 'f-'
                        listContentDir.append(f'f-{item}')
            # Формирование строки со списком каталога
            listOfDir = ' '.join(listContentDir)
            # Возвращаются два ответа: 1 - успешность выполнения, размер списка каталога,
            # 2 - команда 0, строка со списком каталога
            return (200, f'{len(listOfDir)} bytes'), (0, listOfDir)
        else:
            return (149, ''),

    def _cd(self, args):
        """
        Команда - переход в каталог по указанному пути
        :param args: список содержащий 1 строку - путь к каталогу, относительно текущего
        :return: кортеж из пар: код ответа, сообщение
        """
        if len(args) != 1:
            return (102, ''),

        if args[0] == '~':
            # Переход к стартовой директории
            self.currentSession.directoryCurrent = Session.directoryStart
            return (200, ''),

        # Проверка существования указанного пути относительно текущего
        if os.path.exists(self.currentSession.directoryCurrent + '/' + args[0]):
            self.currentSession.directoryCurrent = os.path.relpath(self.currentSession.directoryCurrent + '/' + args[0])
            return (200, ''),
        else:
            return (149, ''),

    def _get(self, args):
        """
        Команда - получение файла из текущего каталога
        :param args: список содержащий 1 строку - название файла в текущем каталоге
        :return: кортеж из пар: код ответа, сообщение
        """
        if len(args) != 1:
            return (102, ''),
        pathToFile = self.currentSession.directoryCurrent + '/' + args[0]

        # Проверка существования пути к файлу и является ли файл по указанному пути файлов
        if os.path.exists(pathToFile) and os.path.isfile(pathToFile):
            # Проверка поддерживаемости файла
            if pathToFile.split('.')[-1] in self.fileExtensions:
                # Кодировка файла
                resultEncoding, msg = self._encodePhoto(pathToFile)
                if resultEncoding:
                    # Если кодировка прошла успешно
                    return (200, f'File follows - {len(msg)} bytes'), (0, msg.decode())
                else:
                    return (104, ''),
            else:
                return (103, ''),
        else:
            return (149, ''),

    @staticmethod
    def _encodePhoto(path: str) -> tuple[bool, bytes]:
        """
        Кодирование фото в байты по протоколу base64
        :param path: строка - путь к фото
        :return: кортеж:
                    1. (bool=True, bytes) - если файл был открыт и зашифрован, bytes - зашифрованный файл
                    2. (bool=False, bytes=b'') - если произошла ошибка при открытии или шифровании файла
        """
        flagOpened = True
        encodedImage = b''
        try:
            imageFile = open(path, "rb")
            encodedImage = base64.b64encode(imageFile.read())
        except OSError:
            print(f"Could not open file {path}")
            flagOpened = False
        return flagOpened, encodedImage

    def _quit(self, args):
        """
        Команда - завершение сессии
        :param args: пустой список
        :return: кортеж из пар: код ответа, сообщение
        """
        #if len(args):
        #    return 102, ''
        self.currentSession = None
        return (200, 'Goodbye!'),

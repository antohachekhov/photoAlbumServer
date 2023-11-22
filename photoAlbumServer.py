import os
import base64
from typing import Tuple, Union


class photoAlbumServer:
    # Поддерживаемые форматы файлов
    supportedFileExtensions = ['jpeg', 'jpg', 'gif', 'png']

    # Коды сообщений
    codes = {
        0: "Part of file",
        200: "OK",
        149: "ERR Such album is not exist"
    }

    @staticmethod
    def _checkFileExtensions(inputFileExtensions) -> bool:
        """
        Проверка введённых расширений файла на поддержку
        :param inputFileExtensions: список с элементами типа str, элемент - имя расширения файла
        :return: True, если все элемента списка inputFileExtensions прошли проверку, иначе - исключение ValueError
        """
        for extension in inputFileExtensions:
            if extension not in photoAlbumServer.supportedFileExtensions:
                raise ValueError(f"{extension} is not support")
        return True

    def __init__(self, inputPathToPhotoBase: str = './photoBase', *args):
        self.port = None

        if len(args):
            if photoAlbumServer._checkFileExtensions(args):
                self.fileExtensions = list(map(str.lower, args))
        else:
            self.fileExtensions = ['jpeg', 'jpg']

        self.pathToPhotoBase = inputPathToPhotoBase

    def start(self):
        """
        Запуск сервера
        """
        pass

    def close(self):
        """
        Закрытие сервера
        """
        pass

    def _listen(self):
        """
        Обработка приходящих сообщений
        """
        while True:
            pass

    def _findPhoto(self, path: str) -> list:
        """
        Поиск альбома в базе по заданному пути
        :param path: строка - путь
        :return: список, в котором элементы - пути к найденным файлам
        """
        if not os.path.exists(path):
            raise ValueError(f"No such album {path}")
        foundFiles = list()
        for root, dirs, files in os.walk(self.pathToPhotoBase + '/' + path):
            for file in files:
                if any(map(file.lower().endswith, self.fileExtensions)):
                    foundFiles.append(root + '/' + str(file))
        return foundFiles

    @staticmethod
    def _encodePhoto(path: str) -> tuple[bool, Union[bytes, str]]:
        """
        Кодирование фото в байты по протоколу base64
        :param path: строка - путь к фото
        :return: список:
                    1. (bool=True, bytes) - если файл был открыт и зашифрован, bytes - зашифрованный файл
                    2. (bool=False, str='') - если произошла ошибка при открытии или шифровании файла
        """
        flagOpened = True
        encodedImage = ''
        try:
            imageFile = open(path, "rb")
            encodedImage = base64.b64encode(imageFile.read())
        except OSError:
            print(f"Could not open file {path}")
            flagOpened = False
        return flagOpened, encodedImage

    def _send(self, code: int, message: str = ''):
        """
        Отправка сообщений с сервера
        :param code: код сообщения
        :param message: дополнительное сообщение
        """
        if code != 0:
            if message:
                print(f'{code} {self.codes[code]} {message}')
                # send(f'{code} {photoAlbumServer.codes[code]} {message}')
            else:
                print(f'{code} {self.codes[code]}')
                # send(f'{code} {photoAlbumServer.codes[code]}')
        else:
            print(message)
            # send(message)

    def _sendAlbum(self, path: str):
        """
        Отправка альбома с сервера
        :param path: строка - путь к альбому
        """
        try:
            pathsOfPhotos = self._findPhoto(path)
        except ValueError:
            self._send(149)
        else:
            countPhotosInAlbum = len(pathsOfPhotos)
            countPhotosToSend = 0
            albumBytes = list()
            if countPhotosInAlbum > 0:
                for pathPhoto in pathsOfPhotos:
                    flag, photoBytes = self._encodePhoto(pathPhoto)
                    if flag:
                        countPhotosToSend += 1
                        albumBytes.append(photoBytes)
            else:
                self._send(149)
            self._send(200,
                       f'Album follow ({countPhotosToSend} photos, {countPhotosInAlbum - countPhotosToSend} missed)')
            for photoBytes in albumBytes:
                self._send(0, photoBytes.decode())

    def test(self, path: str):
        self._sendAlbum(path)

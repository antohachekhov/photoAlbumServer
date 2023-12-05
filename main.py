from photoAlbumServer import photoAlbumServer
import serial.tools.list_ports

defaultSettings = {
    'pathToPhotoBase': 'photoBase',
    'portName': 'COM1',
    'baudrate': 9600
}

if __name__ == "__main__":
    print('======= ПРОГРАММА-СЕРВЕР ПО РАБОТЕ С ФОТОГРАФИЯМИ =======')
    print('--- Настройки сервера по умолчанию ---')
    for setting in defaultSettings:
        print(f'{setting}: {defaultSettings[setting]}')
    flag = input('Применить настройки по умолчанию? да/нет: ')
    if flag.lower() == 'нет':
        defaultSettings['pathToPhotoBase'] = input('Введите путь к корневой папке фотобазы: ')
        ports = serial.tools.list_ports.comports()
        portsList = [port.device for port in ports]
        print('Доступные следующие COM-порты:', *portsList)
        defaultSettings['portName'] = input('Введите название COM-порта: ')
        defaultSettings['baudrate'] = int(input('Введите скорость передачи данных в бит/сек: '))

    s = photoAlbumServer(inputPathToPhotoBase=defaultSettings['pathToPhotoBase'])
    s.start(portName=defaultSettings['portName'], baudrate=defaultSettings['baudrate'])

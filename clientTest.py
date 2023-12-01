import serial
import serial.tools.list_ports
from serial import PARITY_ODD
import CheckSum

portName = 'COM2'
baudrate = 9600

indexOfBytesInAnswer = {
    'get': 5,
    'ls': 2
}


def client():
    port = serial.Serial(portName, baudrate=baudrate, parity=PARITY_ODD, timeout=1)
    flag = True
    while flag:
        print('Клиент > Введите команду')
        command = input('input > ')
        command += '. '
        if command == 'exit':
            flag = False
        else:
            checkSum = CheckSum.simple_checksum(command.encode())
            request = command + checkSum.to_bytes(4, byteorder="little").decode()
            print(f'Клиент > Отправляем {request}')
            port.write(request.encode())
            if command[:-2].split(' ')[0] in ['get', 'ls']:
                answer = port.read(size=1024).decode()
                if answer.split()[0] == '200':
                    print(f'Клиент > Получено: {answer}')
                    print(f'Проверка контрольный суммы: {answer[-4:].encode() == CheckSum.simple_checksum(answer[:-4].encode()).to_bytes(4, byteorder="little")}')
                    size = int(answer.split(' ')[indexOfBytesInAnswer[command[:-2].split()[0]]])
                    answer = port.read(size=size + 6).decode()
            else:
                answer = port.read(size=1024).decode()
            print(
                f'Проверка контрольный суммы: {answer[-4:].encode() == CheckSum.simple_checksum(answer[:-4].encode()).to_bytes(4, byteorder="little")}')
            print(f'Клиент > Получено: {answer}')

from photoAlbumServer import photoAlbumServer
import os
import threading
import serial
import serial.tools.list_ports
from clientTest import client

if __name__ == "__main__":
    s = photoAlbumServer()
    thr1 = threading.Thread(target=s.start)
    thr1.start()
    print('Север создан')

    thr2 = threading.Thread(target=client)
    thr2.start()
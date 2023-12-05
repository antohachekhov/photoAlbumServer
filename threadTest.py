from photoAlbumServer import photoAlbumServer
import threading
from clientTest import client

s = photoAlbumServer()
thr1 = threading.Thread(target=s.start)
thr1.start()
print('Север создан')

thr2 = threading.Thread(target=client)
thr2.start()

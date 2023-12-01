# Сервер для просмотра фотографий #

## Содержание ##
[Настройки сервера](#Настройки-сервера)

* [Путь к фотобазе](#Путь-к-фотобазе)

* [Поддерживаемые файлы](#Поддерживаемые-файлы)

* [COM-порт](#COM-порт)

[Запросы для сервера](#Запросы-для-сервера)

* [Структура запроса](#Структура-запроса)

* [Контрольная сумма](#Контрольная-сумма)

[Ответы от сервера](#Ответы-от-сервера)

* [Структура ответа](#Структура-ответа)

* [Список кодов ответов](#Список-кодов-ответов)

## Настройки сервера ##

---
### Путь к фотобазе ###
Для указания каталога с фотобазой, нужно при инициализации объекта класса `photoAlbumServer` аргументу `inputPathToPhotoBase` передать строку - путь к корневому каталогу фотобазы. Путь может быть абсолютным или относительным. В случае относительного, путь указывается относительно пути, в котором запускается сервер.

Например:

```python
server = photoAlbumServer(inputPathToPhotoBase='./photoBase')
```

По умолчанию используется путь `./photoBase`
### Поддерживаемые файлы ###

Чтобы определить какие типы файлов поддерживаются сервером, нужно при инициализации объекта класса `photoAlbumServer` аргументу `fileExtensions` передать список, состоящий из строк с расширениями файлов. Расширения файлов не регистрозависимые!

Например:

```python
server = photoAlbumServer(fileExtensions=['JPEG', 'gif', 'png'])
```

По умолчанию поддерживаются типы `jpeg, jpg, gif, png`
### COM-порт ###
Сервер принимает и отправляет сообщения через COM-порт. По умолчанию используется порт `COM1` со скоростью `9600` бит/сек.

Для указания собственных параметров установки соединения, нужно при вызове метода `start` указать значения аргументов `portName` и `baudrate`

Например:

```python
server.start(portName='COM1', baudrate=9600)
```

## Запросы для сервера ###

---

### Структура запроса ###


Сервер принимает запросы в виде байтовой последовательности, которая затем декодируется в строку с кодировкой `UTF-8`.

Любой запрос должен иметь две составные части: тело запроса и значение контрольной суммы. Тело запроса должно заканчиваться символами разделения `.ㅤ` (точка с пробелом).

Структуры запроса в зависимости от количества передаваемых аргументов:
* если запрос не содержит аргументов
`КОМАНДА. КОНТРОЛЬНАЯ_СУММА`. 
Например: `pwd. 590A`


* если запрос содержит один аргумент
`КОМАНДА АРГУМЕНТ. КОНТРОЛЬНАЯ_СУММА`. 
Например: `ls dir1. 31A6`


* если запрос содержит более одного аргумента
`КОМАНДА СПИСОК_АРГУМЕНТОВ. КОНТРОЛЬНАЯ_СУММА`
В этом случае аргументы записываются через пробел. 
Например: `auth login1 password1. B4F1`

### Контрольная сумма ###

 Значение контрольной суммы должно быть вычислено по всему телу запроса, включая символы разделения.
 
 Значение контрольной суммы должно состоять из 4 байт!
 
 Для вычисления контрольной суммы по умолчанию используется **функция простой контрольной суммы**, определенная в модуле `CheckSum.py`.
 
 Чтобы использовать собственную функцию контрольной суммы, нужно при инициализации объекта класса `photoAlbumServer` передать аргументу `checkSum` объект-функцию, реализующий вычисление контрольной суммы.
 
 Например:
 
```python
server = photoAlbumServer(checkSum=myChechSum)
```


## Ответы от сервера ##

---

### Структура ответа ###

Сервер отправляет ответы в виде байтовой последовательности, которая затем должна быть декодирована в строку с кодировкой `UTF-8`.

Любой ответ сервера состоит из тела ответа и значения контрольной суммы, вычисленной по телу ответа. Тело ответа заканчивается символами разделения `.ㅤ` (точка с пробелом).

Любой ответ сервера начинается с трёхзначного кода ответа. В зависимости от него ответ может иметь разную структуру.
* eсли код ответа `000`: `000 СООБЩЕНИЕ. КОНТРОЛЬНАЯ_СУММА`


* eсли код ответа от `100` до `199`: `КОД СЛУЖЕБНОЕ_СООБЩЕНИЕ. КОНТРОЛЬНАЯ_СУММА`


* если код ответа `200`, то в зависимости от отправленной команды ответ может быть: `200 СЛУЖЕБНОЕ_СООБЩЕНИЕ. СООБЩЕНИЕ. КОНТРОЛЬНАЯ_СУММА` или `200 СЛУЖЕБНОЕ_СООБЩЕНИЕ. КОНТРОЛЬНАЯ_СУММА`. Подробнее об ответах на команды см. в разделе **Команды**

### Список кодов ответов ###

| Код ответа |         Служебное сообщение      | Описание | 
|:-----------|:--------------------------------:|  :--- |
| 000        |                                  |Ответ содержит файл|
| 100        |      ERR User is not authorized  | Невозможно выполнить команду, т.к. клиент не авторизован|
| 101        |       ERR Authorisation Error    | Ошибка авторизации|
| 102        |      ERR Invalid command format  | Неверный формат запроса|
| 103        |         ERR Unsupported file     |Запрашиваемый файл не поддерживается сервером|
| 104        |      ERR File could not be sent  | Невозможно отправить файл|
| 149        | ERR Such directory/file is not exist | Запрашиваемого каталога или файла не существует|
| 199        | ERR Checksum verification failed |Ошибка при сравнении контрольной суммы|
| 200        |                  OK              | Команда выполнена успешно     |


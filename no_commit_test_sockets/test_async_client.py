import hashlib
import asyncio


async def send_request():
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)  # 1 запрос

    # Аутентификация клиента
    auth_success = await authenticate_client(reader, writer)
    if not auth_success:
        print("Ошибка аутентификации! Закрытие соединения.")
        writer.close()
        return

    try:
        while True:
            print("Введите команду (info - информация о клиентах):")
            command = input().lower()

            writer.write(command.encode())
            await writer.drain()  # 1

            response = await reader.read(100)
            print(f"Сервер сообщает: {response.decode()}")
    except Exception as e:
        print(f'Ошибка при работе с сервером: {str(e)}')
    finally:
        writer.close()
        await writer.wait_closed()


async def authenticate_client(reader, writer):
    # Здесь вы можете реализовать логику аутентификации клиента.
    # Например, запрашивать учетные данные и отправлять их на сервер.
    # В данном примере предполагается ввод пароля.

    response = await reader.read(100)  # 1 ответ
    password = response.decode().strip()
    #print(password)
    if password == "Write password:":
        print(f"Сервер запросил пароль. Введите логин и пароль:")

        login = input("Введите логин: ").encode()
        passwd = input("Введите пароль: ").encode()

        writer.write(login+b'|'+passwd)
        await writer.drain()


        response = await reader.read(100)
        print(f"Сервер сообщает: {response.decode()}")
        return response.decode() == "OK"
    else:
        return False #Страховка на случай непредвиденного ответа


asyncio.run(send_request())

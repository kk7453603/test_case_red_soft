import hashlib
import asyncio


async def send_request():
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)

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
            await writer.drain()

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

    response = await reader.read(100)
    password = response.decode().strip()
    print(f"Сервер запросил пароль. Введите пароль:")
    writer.write(password.encode())
    await writer.drain()

    response = await reader.read(100)
    print(f"Сервер сообщает: {response.decode()}")
    return response.decode() == "OK"


asyncio.run(send_request())

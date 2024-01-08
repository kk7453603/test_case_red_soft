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
            print("Введите команду: ")
            command = input().lower()

            if command == "add_client":
                username = input("Введите имя пользователя: ").strip().encode()
                user_passwd = input("Введите пароль пользователя: ").strip().encode()
                ram_size = input("Введите объем RAM пользователя: ").strip().encode()
                cpu_count = input("Введите количество ядер процессора пользователя: ").strip().encode()
                disk_size = input("Введите объем жесткого диска пользователя: ").strip().encode()
                id_hard_drive = input("Введите id жесткого диска пользователя: ").strip().encode()

                query = b'|'.join((command.encode(),username,user_passwd,ram_size,cpu_count,disk_size,id_hard_drive))
                print(query)
                writer.write(query)
                #await writer.drain()

                response = await reader.read(255)
                print(f"Сервер сообщает:\n {response.decode()}")

            elif command == "all_connected_clients":
                writer.write(command.encode()+b'|')
                response = await reader.read(255)
                print(f"Сервер сообщает:\n {response.decode()}")

            elif command == "all_auth_clients":
                pass
            elif command == "all_clients":
                pass
            elif command == "exit":
                pass
            elif command == "update_client":
                pass
            elif command == "info":
                pass
            elif command == "del_virtbox":
                pass
            elif command == "stats":
                pass

            await writer.drain()
            #writer.write(command.encode())
            #await writer.drain()  # 1

            response = await reader.read(255)
            print(f"Сервер сообщает:\n {response.decode()}")
    except Exception as e:
        print(f'Ошибка при работе с сервером: {str(e)}')
    finally:
        writer.close()
        await writer.wait_closed()


async def authenticate_client(reader, writer):
    response = await reader.read(255)  # 1 ответ
    password = response.decode().strip()
    #print(password)
    if password == "Write password:":
        print(f"Сервер запросил пароль. Введите логин и пароль:")

        login = input("Введите логин: ").encode()
        passwd = input("Введите пароль: ").encode()

        writer.write(login+b'|'+passwd)
        await writer.drain()

        # Отсюда дальше не выполняется
        response = await reader.read(255)
        print(f"Сервер сообщает: {response.decode()}")
        return response.decode() == "Correct auth"
    else:
        return False #Страховка на случай непредвиденного ответа


asyncio.run(send_request())

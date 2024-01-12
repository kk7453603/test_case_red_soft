import asyncio
import json



async def send_request():
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)

    auth_success = await authenticate_client(reader, writer)
    if not auth_success:
        print("Ошибка аутентификации! Закрытие соединения.")
        writer.close()
        return

    try:
        while True:
            print("Введите команду: ")
            command = input().lower().strip()

            if command == "add_client" or command == "update_client":
                username = input("Введите имя пользователя: ").strip().encode()
                user_passwd = input("Введите пароль пользователя: ").strip().encode()
                ram_size = input("Введите объем RAM пользователя: ").strip().encode()
                cpu_count = input("Введите количество ядер процессора пользователя: ").strip().encode()
                disk_size = input("Введите объем жесткого диска пользователя: ").strip().encode()
                id_hard_drive = input("Введите id жесткого диска пользователя: ").strip().encode()

                query = b'|'.join(
                    (command.encode(), username, user_passwd, ram_size, cpu_count, disk_size, id_hard_drive))

                writer.write(query)
                response = await reader.read(255)
                print(f"Сервер сообщает:\n {response.decode()}")

            elif command == "all_connected_clients":
                writer.write(command.encode() + b'|')
                response = await reader.read(255)
                print("Сервер сообщает:\n")
                for client in response.decode().split('!'):
                    print(client)

            elif command == "all_auth_clients":
                writer.write(command.encode() + b'|')
                response = await reader.read(255)
                data = json.loads(response.decode())
                print("Сервер сообщает:\n")
                for client in data:
                    print(
                        f"Имя клиента: {client[0]}, Объем RAM: {client[1]}, Количество ядер CPU: {client[2]}, Объем жесткого диска: {client[3]}, ID жесткого диска: {client[4]}")

            elif command == "all_clients":
                writer.write(command.encode() + b'|')
                response = await reader.read(255)
                data = json.loads(response.decode())
                print("Сервер сообщает:\n")
                for client in data:
                    print(
                        f"Имя клиента: {client[0]}, Объем RAM: {client[1]}, Количество ядер CPU: {client[2]}, Объем жесткого диска: {client[3]}, ID жесткого диска: {client[4]}")

            elif command == "exit":
                writer.write(command.encode() + b'|')
                await writer.drain()
                response = await reader.read(255)
                writer.close()
                await writer.wait_closed()
                print(f"Сервер сообщает:\n {response.decode()}")
                break

            elif command == "get_stats":
                writer.write(command.encode() + b'|')
                response = await reader.read(255)
                data = json.loads(response.decode())
                print(f"Количество виртуальных машин: {data[0]}, Суммарный объем RAM: {data[1]}, Суммарное "
                          f"количество ядер CPU: {data[2]}, Суммарный оюъем дисков: {data[3]}")

            elif command == "del_client":
                id = input("Введите id виртуальной машины, которую хотите удалить: ").strip().encode()
                writer.write(command.encode() + b'|' + id)
                response = await reader.read(255)
                print(f"Сервер сообщает:\n {response.decode()}")

            elif command == "get_info":
                writer.write(command.encode() + b'|')
                response = await reader.read(300)
                data = json.loads(response.decode())
                for client in data:
                    print(f"Id Клиента: {client[0]},Имя клиента: {client[1]}, Пароль клиента: {client[2]}, Объем RAM: {client[3]}, Количество ядер CPU: {client[4]}, Объем жесткого диска: {client[5]}, ID жесткого диска: {client[6]}, Статус подключения: {client[7]}")

            else:
                print("Команды не существует! Попробуйте снова")

            if command != "exit":
                await writer.drain()

    except Exception as e:
        print(f'Ошибка при работе с сервером: {str(e)}')

    finally:
        writer.close()
        await writer.wait_closed()


async def authenticate_client(reader, writer):
    response = await reader.read(255)
    password = response.decode().strip()
    if password == "Write password:":
        print(f"Сервер запросил пароль. Введите логин и пароль:")
        login = input("Введите логин: ")
        passwd = input("Введите пароль: ")
        data = json.dumps({"login": login, "passwd": passwd})
        writer.write(data.encode())
        await writer.drain()

        response = await reader.read(255)
        print(f"Сервер сообщает: {response.decode()}")
        return response.decode() == "Correct auth"
    else:
        return False


asyncio.run(send_request())

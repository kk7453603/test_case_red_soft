import asyncio
import hashlib
import sqlite3

clients = {}  # Словарь для хранения авторизованных подключенных клиентов
connected = {}  # Словарь для хранения  подключенных клиентов (без авторизации)


async def handle_client(reader, writer):
    address = writer.get_extra_info('peername')
    print(f'Новое подключение от {address}')

    connected[address] = writer

    # Аутентификация клиента
    auth_success = await authenticate_client(reader, writer)
    if not auth_success[0]:
        writer.write(b"Auth Error! Close Connection.")
        await writer.drain()
        writer.close()
        print(f'Аутентификация не удалась для {address}')
        return


    # Добавление авторизованного клиента в список
    client_id = auth_success[1]
    clients[client_id] = writer
    print(clients)


    try:
        while True:
            data = await reader.read(100)
            message = data.decode()

            # Обработка команд от клиента
            if message.lower() == 'info':  # Получение информации о клиентах
                info = get_clients_info()
                writer.write(info.encode())
                await writer.drain()
            else:
                writer.write(b"Unsupportable command.")
                await writer.drain()
    except Exception as e:
        print(f'Ошибка при работе с клиентом {address}: {str(e)}')
    finally:
        writer.close()
        print(f'Соединение с {address} закрыто')
        del clients[client_id]  # Удаление клиента из списка


async def authenticate_client(reader, writer):
    # Здесь вы можете реализовать логику аутентификации клиента.
    # Например, проверять учетные данные, хранящиеся на сервере.
    # В данном примере просто предлагается ввод пароля.

    writer.write(b"Write password: ")  # 1 запрос
    await writer.drain()

    # data = await reader.read(100)
    login_passwd = await reader.read(100)
    login, passwd = login_passwd.split(b'|')

    print(login, passwd)

    login = login.decode().strip()
    passwd = passwd.decode().strip()

    # writer.write(b"password on server")
    # await writer.drain()

    auth = check_auth(login, passwd)
    print(auth)
    if auth == -1:
        writer.write(b"Incorrect password!")
        await writer.drain()
        return [False]

    writer.write(b"Correct auth")
    await writer.drain()
    return [True, auth]


def check_auth(login, passwd):
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    resp = c.execute("""SELECT id FROM clients WHERE (user_name=? and user_passwd=?)
    """, (login, passwd))
    result = resp.fetchone()


    if result is not None and len(result) == 1:

        c.execute("""UPDATE clients SET conn_status = 1""")
        conn.commit()
        c.close()
        conn.close()

        return result[0]
    else:

        c.close()
        conn.close()
        return -1


# верно
def create_table():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_name TEXT,
                        user_passwd TEXT,
                        ram_size DOUBLE,
                        cpu_count INT,
                        disk_size DOUBLE,
                        id_hard_drive INT UNIQUE,
                        conn_status BOOLEAN DEFAULT 0
                    )''')
    conn.commit()
    conn.close()


# верно
def add_client(user_name, user_passwd, ram_size, cpu_count, disk_size, id_hard_drive, conn_status=0):
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('''INSERT INTO clients (user_name, user_passwd, ram_size, cpu_count, disk_size, id_hard_drive, conn_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (user_name, user_passwd, ram_size, cpu_count, disk_size, id_hard_drive, conn_status))
    conn.commit()
    conn.close()


# верно не точно, возвращает ip адрес  неавторизованных, но подключенных клиентов
def get_not_authorized_clients():
    row = []
    for key in connected.keys():
        row.append(key)
    return row


# не проверено, возвращает id авторизованных клиентов
def get_authorized_clients():
    row = []
    for key in clients.keys():
        row.append(key)
    return row


# Не доделано!
def get_all_authorized_and_connected_clients():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('SELECT * FROM clients WHERE conn_status = 1')
    rows = c.fetchall()
    conn.close()

    return rows


# Верно
def update_auth_client(id, user_name, ram_size, cpu_count, disk_size, id_hard_drive):
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    resp = c.execute('''SELECT (id) FROM clients WHERE id_hard_drive = ?''', (id_hard_drive,))
    res = resp.fetchone()
    print(res)
    if res is None or res[0] == id:
        c.execute('''UPDATE clients SET user_name = ?, ram_size = ?, cpu_count = ?, disk_size = ?, id_hard_drive = ?
                WHERE id = ?''', (user_name, ram_size, cpu_count, disk_size, id_hard_drive, id))
        conn.commit()
        conn.close()
        return True

    conn.close()
    return False


# Верно
def get_all_disks():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('''SELECT COUNT(*),SUM(ram_size),SUM(cpu_count) FROM clients''')
    rows = c.fetchall()
    conn.close()
    return rows


# Не проверено
async def kill_server(server):
    print("Закрытие сервера...")
    for conn in clients:
        conn.close()
        await conn.wait_closed()

    server.close()
    await server.wait_closed()
    print("Сервер успешно остановлен.")


async def exit_client(writer):
    print("Отключение клиента...")
    writer.close()
    await writer.wait_closed()
    print("Клиент успешно отключен.")


def update_vm_params(vm_id, ram_size=None, cpu_count=None, disk_size=None):
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()

    update_query = 'UPDATE clients SET'
    update_values = []

    if ram_size is not None:
        update_query += ' ram_size = ?,'
        update_values.append(ram_size)

    if cpu_count is not None:
        update_query += ' cpu_count = ?,'
        update_values.append(cpu_count)

    if disk_size is not None:
        update_query += ' disk_size = ?,'
        update_values.append(disk_size)

    # Удаление последней запятой из запроса
    update_query = update_query.rstrip(',')

    # Добавление условия по vm_id
    update_query += ' WHERE id = ?'
    update_values.append(vm_id)

    c.execute(update_query, tuple(update_values))
    conn.commit()
    conn.close()


async def main():
    create_table()
    server = await asyncio.start_server(
        handle_client, '127.0.0.1', 8888)  # 1 запрос

    addr = server.sockets[0].getsockname()
    print(f'Сервер запущен на {addr}')

    async with server:
        await server.serve_forever()


asyncio.run(main())

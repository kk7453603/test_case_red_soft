import asyncio
import hashlib
import sqlite3

clients = {}  # Словарь для хранения подключенных клиентов


async def handle_client(reader, writer):
    address = writer.get_extra_info('peername')
    print(f'Новое подключение от {address}')

    # Аутентификация клиента
    auth_success = await authenticate_client(reader, writer)
    if not auth_success:
        writer.write(b"Ошибка аутентификации! Закрытие соединения.")
        await writer.drain()
        writer.close()
        print(f'Аутентификация не удалась для {address}')
        return

    # Добавление клиента в список
    client_id = address[0]  # Используем IP-адрес клиента в качестве ID
    clients[client_id] = writer

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
                writer.write(b"Недопустимая команда.")
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

    writer.write(b"Введите пароль: ")
    await writer.drain()

    data = await reader.read(100)
    password = data.decode().strip()
    if password != "mypassword":
        writer.write(b"Неверный пароль!")
        await writer.drain()
        return False

    return True


def get_clients_info():
    info = "Список клиентов:\n"
    for client_id, writer in clients.items():
        info += f"ID: {client_id}\n"
    return info


def create_table():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT,
                    ram_size INTEGER,
                    cpu_count INTEGER,
                    disk_size INTEGER
                )''')
    conn.commit()
    conn.close()


def add_client(client_id, ram_size, cpu_count, disk_size):
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('''INSERT INTO clients (client_id, ram_size, cpu_count, disk_size)
                    VALUES (?, ?, ?, ?)''', (client_id, ram_size, cpu_count, disk_size))
    conn.commit()
    conn.close()


def get_all_clients():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('SELECT * FROM clients')
    rows = c.fetchall()
    conn.close()

    return rows


def get_authorized_clients():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('SELECT * FROM clients WHERE auth_status = 1')
    rows = c.fetchall()
    conn.close()

    return rows


def get_all_connected_clients():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('SELECT * FROM clients WHERE connection_status = 1')
    rows = c.fetchall()
    conn.close()

    return rows


def update_auth_client(client_id, ram_size, cpu_count, disk_size):
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('''UPDATE clients SET ram_size = ?, cpu_count = ?, disk_size = ?
            WHERE client_id = ?''', (ram_size, cpu_count, disk_size, client_id))
    conn.commit()
    conn.close()


def get_all_disks():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('''SELECT disks.disk_id, disks.disk_size, clients.client_id
                FROM disks JOIN clients ON disks.client_id = clients.client_id''')
    rows = c.fetchall()
    conn.close()

    return rows


def exit_server():
    # Закрытие всех соединений и остановка сервера
    # Также может включать сохранение данных и очистку ресурсов
    pass


def get_total_stats():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('''SELECT COUNT(*) AS total_clients, SUM(ram_size) AS total_ram,
                SUM(cpu_count) AS total_cpu FROM clients''')
    row = c.fetchone()
    conn.close()

    total_clients = row[0]
    total_ram = row[1]
    total_cpu = row[2]

    return total_clients, total_ram, total_cpu


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
    server = await asyncio.start_server(
        handle_client, '127.0.0.1', 8888)

    addr = server.sockets[0].getsockname()
    print(f'Сервер запущен на {addr}')

    async with server:
        await server.serve_forever()


asyncio.run(main())

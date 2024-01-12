import asyncio
import sqlite3
import json

clients = {}  # Словарь для хранения авторизованных подключенных клиентов
connected = {}  # Словарь для хранения  подключенных клиентов (без авторизации)


async def handle_client(reader, writer):
    address = writer.get_extra_info('peername')
    print(f'Новое подключение от {address}')
    connected[address] = writer
    auth_success = await authenticate_client(reader, writer)
    if not auth_success[0]:
        writer.write(b"Auth Error! Close Connection.")
        await writer.drain()
        writer.close()
        print(f'Аутентификация не удалась для {address}')
        del connected[address]
        return

    # Добавление авторизованного клиента в список
    client_id = auth_success[1]
    clients[client_id] = writer

    try:
        while True:
            data = await reader.read(255)
            message = data.decode().split('|')
            if message[0].lower() == 'add_client':

                if add_client(message[1], message[2], message[3], message[4], message[5], message[6]):
                    writer.write(b"user added!")
                else:
                    writer.write(b"user add error, hard drive id already exists!")

                await writer.drain()

            elif message[0].lower() == 'all_connected_clients':
                res = get_not_authorized_clients()
                writer.write(res.encode())
                await writer.drain()

            elif message[0].lower() == 'all_auth_clients':
                res = get_authorized_clients()
                writer.write(res)
                await writer.drain()

            elif message[0].lower() == 'all_clients':
                res = get_all_authorized_and_connected_clients()
                writer.write(res)
                await writer.drain()

            elif message[0].lower() == 'exit':
                writer.write(b"You are disconnected from the server!")
                await writer.drain()
                await writer.wait_closed()
                writer.close()
                print(f'Соединение с {address} закрыто')
                del clients[client_id]
                break

            elif message[0].lower() == 'update_client':
                if update_client(client_id, message[1], message[2], message[3], message[4], message[5], message[6]):
                    writer.write(b"user modified!")
                else:
                    writer.write(b"user modify error!")

            elif message[0].lower() == 'get_stats':
                res = get_stats()
                writer.write(res)
                await writer.drain()

            elif message[0].lower() == 'del_client':
                id = message[1]
                rm_client_id(id)
                writer.write(b"Operation complete")
                await writer.drain()

            elif message[0].lower() == 'get_info':
                res = get_all_clients()
                print(res)
                writer.write(res)
                await writer.drain()
            else:
                writer.write(b"Unsupportable command.")
                await writer.drain()


    except Exception as e:
        print(f'Ошибка при работе с клиентом {address}: {str(e)}')
    finally:
        print(f'Соединение с {address} закрыто')


async def authenticate_client(reader, writer):
    writer.write(b"Write password: ")
    await writer.drain()
    response = await reader.read(255)
    data = json.loads(response.decode())
    login = data["login"]
    passwd = data["passwd"]
    auth = await check_auth(login, passwd)
    if auth == -1:
        writer.write(b"Incorrect password!")
        await writer.drain()
        return [False]

    writer.write(b"Correct auth")
    await writer.drain()
    return [True, auth]


async def check_auth(login, passwd):
    try:
        conn = sqlite3.connect('clients.db')
        c = conn.cursor()
        resp = c.execute("""SELECT id FROM clients WHERE (user_name=? and user_passwd=?)
        """, (login, passwd))
        result = resp.fetchone()
        conn.commit()
    except Exception as e:
        print(e)
    finally:

        if result is not None and len(result) == 1:
            try:
                c.execute("""UPDATE clients SET conn_status = 1 WHERE id = ?""", (result[0],))
                conn.commit()
            except sqlite3.Error as e:
                print(e.sqlite_errorcode)
            finally:
                c.close()
                conn.close()
                return result[0]
        else:
            c.close()
            conn.close()
            return -1


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
                        id_hard_drive TEXT UNIQUE,
                        conn_status BOOLEAN DEFAULT 0
                    )''')
    c.execute('''INSERT INTO clients (user_name, user_passwd, ram_size, cpu_count, disk_size, id_hard_drive, conn_status)
    SELECT 'admin', '123', '16', '6', '128', RANDOM(), '0' 
    WHERE NOT EXISTS (SELECT 1 FROM clients WHERE user_name = 'admin');''')
    conn.commit()
    c.close()
    conn.close()


def add_client(user_name, user_passwd, ram_size, cpu_count, disk_size, id_hard_drive, conn_status=0):
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()

    resp = c.execute('''SELECT (id) FROM clients WHERE id_hard_drive = ?''', (id_hard_drive,))
    res = resp.fetchone()
    if res is None:
        c.execute('''INSERT INTO clients (user_name, user_passwd, ram_size, cpu_count, disk_size, id_hard_drive, conn_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (user_name, user_passwd, ram_size, cpu_count, disk_size, id_hard_drive, conn_status))
        conn.commit()
        conn.close()
        return True

    conn.close()
    return False


def get_not_authorized_clients():
    row = "!".join([str(ip) + ':' + str(port) for ip, port in connected.keys()])
    return row


def get_authorized_clients():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    placeholders = ', '.join(['?'] * len(clients))
    query = "SELECT user_name, ram_size, cpu_count, disk_size, id_hard_drive FROM clients WHERE id IN ({})".format(
        placeholders)
    c.execute(query, list(clients.keys()))
    data = c.fetchall()
    conn.close()
    json_data = json.dumps(data).encode()
    return json_data


def get_all_authorized_and_connected_clients():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute(
        'SELECT user_name, ram_size, cpu_count, disk_size, id_hard_drive FROM clients WHERE conn_status = 1')
    rows = c.fetchall()
    rows_json = json.dumps(rows).encode()
    conn.close()
    return rows_json


def get_all_clients():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute(
        'SELECT * FROM clients')
    rows = c.fetchall()
    rows_json = json.dumps(rows).encode()
    c.close()
    conn.close()
    return rows_json


def update_client(id, user_name, passwd, ram_size, cpu_count, disk_size, id_hard_drive):
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    resp = c.execute('''SELECT (id) FROM clients WHERE id_hard_drive = ?''', (id_hard_drive,))
    res = resp.fetchone()
    if res is None or res[0] == id:
        c.execute('''UPDATE clients SET user_name = ?, user_passwd = ?, ram_size = ?, cpu_count = ?, disk_size = ?, id_hard_drive = ?
                WHERE id = ?''', (user_name, passwd, ram_size, cpu_count, disk_size, id_hard_drive, id))
        conn.commit()
        conn.close()
        return True

    conn.close()
    return False


def get_stats():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('''SELECT COUNT(*),SUM(ram_size),SUM(cpu_count),SUM(disk_size) FROM clients''')
    row = c.fetchone()
    conn.close()
    response_data = json.dumps(row).encode()
    return response_data





def rm_client_id(id):
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('DELETE FROM clients WHERE id = ?', (id,))
    conn.commit()
    conn.close()


async def main():
    create_table()
    server = await asyncio.start_server(
        handle_client, '127.0.0.1', 8888)

    addr = server.sockets[0].getsockname()
    print(f'Сервер запущен на {addr}')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())

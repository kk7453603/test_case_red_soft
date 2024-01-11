import sqlite3
from hashlib import sha256
import unittest
from random import randint
from server import update_client, get_stats, add_client, create_table, get_authorized_clients


class TestMethods(unittest.TestCase):

    def setUp(self):
        # Подготовка базы данных перед каждым тестом
        self.conn = sqlite3.connect('clients.db')
        self.curs = self.conn.cursor()
        create_table()
        self.conn.commit()

    def tearDown(self):
        # Закрытие соединения с базой данных после каждого теста
        # self.curs.execute("DELETE FROM clients")
        self.conn.commit()
        self.curs.close()
        self.conn.close()

    def test_update_client(self):
        self.curs.execute("SELECT MAX(id) FROM clients;")
        id = int(self.curs.fetchone()[0])
        id_hard_drive_hash = sha256((str(id) + "updated_user").encode()).hexdigest()
        truncated_hash = id_hard_drive_hash[:16]
        result = update_client(id, 'updated_user','123', 8, 4, 200, truncated_hash)
        self.assertTrue(result)

    def test_add_client(self):
        result = add_client("test_cli", "123", "13", "4", "120", str(randint(1000, 10000)))
        self.assertTrue(result)

    def test_get_stats(self):
        result = get_stats().decode()
        self.assertIsNotNone(result)

    def test_get_authorized_clients(self):
        result = get_authorized_clients()
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()

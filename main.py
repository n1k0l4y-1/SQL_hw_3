import psycopg2 as pg


class CustomerStorage:

    conn = None
    cur = None

    def __init__(self):
        self.conn = pg.connect(database='postgres', user='postgres', password='postgres')
        self.cur = self.conn.cursor()

    def create_tabs(self):
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS clients(
            id SERIAL PRIMARY KEY,
            name VARCHAR(60) NOT NULL,
            surname VARCHAR(60) NOT NULL,
            mail VARCHAR(320) UNIQUE NOT NULL);
        """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS phones(
            id SERIAL PRIMARY KEY,
            number INT UNIQUE);
        """)
        self.conn.commit()

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS clients_phones(
            id_clients INT NOT NULL REFERENCES clients(id),
            id_phones INT NOT NULL REFERENCES phones(id));
        """)
        self.conn.commit()
        return print('Создана структура БД (таблицы).')

    def new_client_to_db(self, name, surname, mail, num_phone=None):
        self.cur.execute("""
        INSERT INTO clients(name, surname, mail) VALUES(%s, %s, %s);
        """, (name, surname, mail))
        self.conn.commit()

        self.cur.execute("""
        SELECT * FROM clients;
        """)

        id_client = self.cur.fetchall()[-1][0]
        list_id_phone = []

        if num_phone is not None:
            list_num_phone = list(map(int, num_phone.split(',')))
            for _ in list_num_phone:
                self.cur.execute("""
                INSERT INTO phones(number) VALUES (%s);
                """, (_,))
                self.conn.commit()

                self.cur.execute("""
                SELECT * FROM phones;
                """)
                list_id_phone.append(self.cur.fetchall()[-1][0])
        else:
            self.cur.execute("""
            INSERT INTO phones(number) VALUES (NULL);
            """)
            self.conn.commit()

            self.cur.execute("""
            SELECT * FROM phones;
            """)
            list_id_phone.append(self.cur.fetchall()[-1][0])

        for _ in list_id_phone:
            self.cur.execute("""
            INSERT INTO clients_phones(id_clients, id_phones) VALUES (%s, %s);
            """, (id_client, _))
            self.conn.commit()

        list_id_phone.clear()
        return print('Добавлен новый клиент.')

    def add_phone_to_client(self, mail, num_phone):
        self.cur.execute("""
        SELECT id, mail FROM clients
        WHERE mail = %s;
        """, (mail,))

        id_client = self.cur.fetchall()[-1][0]
        list_id_phone = []
        list_num_phone = list(map(int, num_phone.split(',')))

        self.cur.execute("""
        SELECT id_clients, id_phones FROM clients_phones
        WHERE id_clients = %s;
        """, (id_client,))

        id_saved_number = self.cur.fetchone()[1]

        self.cur.execute("""
        SELECT id, number FROM phones
        WHERE id = %s;
        """, (id_saved_number,))

        null_true_false = self.cur.fetchone()[1]

        if null_true_false is None:
            self.cur.execute("""
            UPDATE phones
            SET number = %s
            WHERE id = %s;
            """, (list_num_phone.pop(0), id_saved_number))
            self.conn.commit()

        if len(list_num_phone) > 0:
            for _ in list_num_phone:
                self.cur.execute("""
                INSERT INTO phones(number) VALUES (%s);
                """, (_,))
                self.conn.commit()

                self.cur.execute("""
                SELECT * FROM phones;
                """)
                list_id_phone.append(self.cur.fetchall()[-1][0])

            for _ in list_id_phone:
                self.cur.execute("""
                INSERT INTO clients_phones(id_clients, id_phones) VALUES (%s, %s);
                """, (id_client, _))
                self.conn.commit()

        list_id_phone.clear()
        return print('Клиенту добавлен телефон.')

    def change_client(self, id_or_mail, new_name=None, new_surname=None, new_mail=None):
        if not id_or_mail.isdigit():
            self.cur.execute("""
            SELECT id, mail FROM clients
            WHERE mail = %s;
            """, (id_or_mail,))

            id_client = self.cur.fetchall()[-1][0]
        else:
            id_client = id_or_mail

        if new_name is not None:
            self.cur.execute("""
            UPDATE clients
            SET name = %s
            WHERE id = %s;
            """, (new_name, id_client))
            self.conn.commit()

        if new_surname is not None:
            self.cur.execute("""
            UPDATE clients
            SET surname = %s
            WHERE id = %s;
            """, (new_surname, id_client))
            self.conn.commit()

        if new_mail is not None:
            self.cur.execute("""
            UPDATE clients
            SET mail = %s
            WHERE id = %s;
            """, (new_mail, id_client))
            self.conn.commit()

        return print('Данные о клиенте изменены.')

    def delete_phones(self, mail):
        self.cur.execute("""
        SELECT id, mail FROM clients
        WHERE mail = %s;
        """, (mail,))

        id_client = self.cur.fetchall()[-1][0]

        self.cur.execute("""
        SELECT id_clients, id_phones FROM clients_phones
        WHERE id_clients = %s;
        """, (id_client,))

        list_id_phones = [_[1] for _ in self.cur.fetchall()]

        dict_phones_index = {}
        for i, val in enumerate(list_id_phones):
            self.cur.execute("""
            SELECT id, number FROM phones
            WHERE id = %s;
            """, (val,))
            dict_phones_index.setdefault(self.cur.fetchall()[0][1], list_id_phones[i])

        print(*dict_phones_index)
        delete_phones = list(map(int, input('Введите номера для удаления: ').split(',')))

        if len(delete_phones) == len(dict_phones_index):
            up_null = delete_phones.pop(0)
            self.cur.execute("""
            UPDATE phones
            SET number = NULL
            WHERE id = %s;
            """, (dict_phones_index[up_null],))
            self.conn.commit()

        for _ in delete_phones:
            self.cur.execute("""
            DELETE FROM clients_phones
            WHERE id_phones = %s;
            """, (dict_phones_index[_],))
            self.conn.commit()

            self.cur.execute("""
            DELETE FROM phones
            WHERE id = %s;
            """, (dict_phones_index[_],))
            self.conn.commit()

        return print('Выбранные номера удалены.')

    def delete_client(self, mail):
        self.cur.execute("""
        SELECT id, mail FROM clients
        WHERE mail = %s;
        """, (mail,))

        id_client = self.cur.fetchall()[-1][0]

        self.cur.execute("""
        SELECT id_clients, id_phones FROM clients_phones
        WHERE id_clients = %s;
        """, (id_client,))

        list_id_phones = [_[1] for _ in self.cur.fetchall()]

        self.cur.execute("""
        DELETE FROM clients_phones
        WHERE id_clients = %s;
        """, (id_client,))
        self.conn.commit()

        for _ in list_id_phones:
            self.cur.execute("""
            DELETE FROM phones
            WHERE id = %s;
            """, (_,))
            self.conn.commit()

        self.cur.execute("""
        DELETE FROM clients
        WHERE id = %s;
        """, (id_client,))
        self.conn.commit()

        return print('Выбранный клиент удалён из БД.')

    def get_info_client(self, mail_or_phone=None):
        if not mail_or_phone.isdigit():
            self.cur.execute("""
            SELECT id, mail FROM clients
            WHERE mail = %s;
            """, (mail_or_phone,))

            id_client = self.cur.fetchall()[-1][0]
        else:
            self.cur.execute("""
            SELECT id, number FROM phones
            WHERE number = %s;
            """, (mail_or_phone,))

            id_phone = self.cur.fetchall()[-1][0]

            self.cur.execute("""
            SELECT id_clients, id_phones FROM clients_phones
            WHERE id_phones = %s;
            """, (id_phone,))

            id_client = self.cur.fetchall()[-1][0]

        self.cur.execute("""
        SELECT id_clients, id_phones FROM clients_phones
        WHERE id_clients = %s;
        """, (id_client,))

        list_id_phones = [_[1] for _ in self.cur.fetchall()]

        self.cur.execute("""
        SELECT id, name, surname, mail FROM clients
        WHERE id = %s;
        """, (id_client,))

        print(f'Данные по клиенту с почтой/номером {mail_or_phone}: ')
        print(*self.cur.fetchall()[0], end=' ')

        list_phones = []
        for _ in list_id_phones:
            self.cur.execute("""
            SELECT id, number FROM phones
            WHERE id = %s;
            """, (_,))
            list_phones.append(self.cur.fetchall()[0][1])

        print(*list_phones)

        return None


if __name__ == "__main__":
    start_logic_db = CustomerStorage()

    start_logic_db.create_tabs()
    start_logic_db.new_client_to_db('Раян', 'Гослинг', 'didnt_died_at_the_end@list.ru')
    start_logic_db.new_client_to_db('Евгений', 'Лукашенко', 'potato_spas@yandex.ru', '26524651, 59741696')
    start_logic_db.new_client_to_db('Михаил', 'Терентьев', 'capital_projitochnogo_min@gmail.com', '5466568, 3866558, 4864486')
    start_logic_db.add_phone_to_client('didnt_died_at_the_end@list.ru', '65484518')
    start_logic_db.add_phone_to_client('capital_projitochnogo_min@gmail.com', '46846515, 664845184')
    start_logic_db.change_client('didnt_died_at_the_end@list.ru', 'Какой-то', 'Водитель', 'died_at_the_end@mail.ru')
    start_logic_db.change_client('2', new_name='Шлёпа', new_mail='flopa_cat@gmail.com')
    start_logic_db.delete_phones('died_at_the_end@mail.ru')
    start_logic_db.delete_phones('flopa_cat@gmail.com')
    start_logic_db.delete_phones('capital_projitochnogo_min@gmail.com')
    start_logic_db.delete_client('potato_spas@yandex.ru')
    start_logic_db.get_info_client('didnt_died_at_the_end@list.ru')

    start_logic_db.cur.close()
    start_logic_db.conn.close()
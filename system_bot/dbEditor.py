"""
Класс для работы с базой данных SqlLite.
"""

import sqlite3

import queries


class SqlLiteEditor:
    """
    Класс для работы с SqlLite
    """
    def __init__(self, db_path=None):
        """
        Конструктор для создания класса
        :param db_path: путь до файла
        """
        self.db_path = db_path if db_path else 'database.db'
        self.con = sqlite3.connect(self.db_path)
        return

    def run(self, query: str, type: str = 'select'):
        """
        Запрос для выполнения запросов sql
        :param query: запрос
        :param type: тип запроса
        :return:
        """
        answer = []
        cursor = self.con.cursor()
        cursor.execute(query)
        if type == 'select':
            # получение названия колонок
            names_columns = [_[0] for _ in cursor.description]
            for row in cursor.fetchall():
                answer_row = {name: value for name, value in zip(names_columns, row)}
                answer.append(answer_row)
        self.con.commit()
        return answer

    def __del__(self):
        """
        Диструктор для закрытия подключения
        :return:
        """
        self.con.close()


if __name__ == '__main__':
    a = SqlLiteEditor('database.db')
    query = 'select * from groups'
    techs_id = [row.get('id_group') for row in a.run(queries.SELECT_TECH_CHANEL, type='select')]
    techs_id = [int(i) for i in techs_id if i is not None]
    print(techs_id)

import sqlite3
import os


class database:
    def path():
        current_directory = os.path.dirname(os.path.abspath(__file__))
        db_name = "articles.db"
        return os.path.join(current_directory, db_name)

    def db_create():
        file_path = database.path()
        conn = sqlite3.connect(file_path)
        c = conn.cursor()
        create_table = """
                        CREATE TABLE IF NOT EXISTS articles (
                            id INTEGER PRIMARY KEY,
                            title TEXT NOT NULL,
                            source TEXT NOT NULL,
                            date_published TEXT NOT NULL,
                            link_url TEXT NOT NULL,
                            content TEXT NOT NULL,
                        )
                        """
        c.execute(create_table)
        conn.commit()
        conn.close()

    def db_select():
        file_path = database.path()
        conn = sqlite3.connect(file_path)
        c = conn.cursor()
        select_query = "SELECT * FROM articles"
        c.execute(select_query)
        rows = c.fetchall()
        conn.commit()
        conn.close()
        return rows

    def db_check_record(link):
        file_path = database.path()
        conn = sqlite3.connect(file_path)
        c = conn.cursor()
        select_query = f"SELECT * FROM articles WHERE link_url = '{link}'"
        c.execute(select_query)
        rows = c.fetchall()
        conn.commit()
        conn.close()
        return rows

    def db_insert(title, source, date_published, link_url, content):
        file_path = database.path()
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        insert_query = "insert into entry(time_stamp,title, source, date_published, link_url, content) values(?,?,?,?,?)"
        cursor.execute(insert_query, (title, source, date_published, link_url, content))
        conn.commit()
        conn.close()

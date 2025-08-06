import sqlite3

SQLITE_DB_PATH = './data.db'
GLOBAL_SQLITE_CONN = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)

def with_cursor(func):
    """Decorator to provide a cursor and handle commit/close logic."""
    def wrapper(*args, **kwargs):
        cursor = GLOBAL_SQLITE_CONN.cursor()
        try:
            result = func(*args, cursor=cursor, **kwargs)
            GLOBAL_SQLITE_CONN.commit()
            return result
        finally:
            cursor.close()
    return wrapper

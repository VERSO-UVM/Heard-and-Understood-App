import mysql.connector
from mysql.connector import Error
#pip install mysql-connector-python ^^^^

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database="audio_files" 
        )
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None

def upload_file_to_db(file_name, file_type, file_data):
    connection = connect_to_database()
    if connection is None:
        print("connection failed to db")
        return False
    try:
        cursor = connection.cursor()
        sql = "insert into audio_files (file_name, file_type, file_data) values (%s, %s, %s)"
        cursor.execute(sql, (file_name, file_type, file_data))
        connection.commit()
        print(f"{file_name} uploaded successfully")
        return True
    except Error as e:
        print(f"error when uploading file:{e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
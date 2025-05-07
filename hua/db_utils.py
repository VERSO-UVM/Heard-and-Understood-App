import pymysql

#pip install pymysql

def connect_to_database():
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            #replace this password/user with your mysql password/user
            password="password",
            database="audio_files"
        )
        print("Connected to DB using PyMySQL")
        return connection
    except Exception as e:
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
    except Exception as e:
        print(f"error when uploading file:{e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
import mysql.connector
from colorama import Fore, Style
from Utils.EnvironmentVariables import env
from typing import Union

print(f'{Fore.YELLOW}Initialized {Fore.BLUE}Utils.DB{Style.RESET_ALL}')

# Initialize conn and cursor
conn: any
cursor: any

# Define functions
async def createConn():
    # Try to construct the connection
    try:
        host: str = env('host1')
        conn = mysql.connector.connect(
            host=host,
            user=env('user'),
            password=env('password'),
            database=env('database')
        )
        return conn
    except mysql.connector.Error:
        pass

    try:
        host: str = env('host2')
        conn = mysql.connector.connect(
            host=host,
            user=env('user'),
            password=env('password'),
            database=env('database')
        )
    except mysql.connector.Error as e:
        print(f'{Fore.RED}FAILED TO CONNECT TO MYSQL{Style.RESET_ALL}: {e}')

async def createCursor(conn):
    # Create cursor object
    try:
        cursor = conn.cursor()
        return cursor
    except mysql.connector.Error as e:
        print(f'{Fore.RED}FAILED TO CREATE CURSOR{Style.RESET_ALL}: {e}')

async def select(query: str, params: any) -> Union[any, bool]:
    # Usage:
    # result: any = db.query("SELECT * FROM your_table WHERE column = %s;", ("value",))

    try:
        # Create connection & cursor
        conn = await createConn()
        cursor = await createCursor(conn)

        # Fetch result
        cursor.execute(query, params)
        result: any = cursor.fetchall()

        # Return result
        cursor.close()
        conn.close()
        return result
    except mysql.connector.Error as err:
        print(f'{Fore.RED}FAILED TO FETCH DATA{Style.RESET_ALL}: {err}')
        cursor.close()
        conn.close()
        return False
    
async def insert(query: str, params: any) -> bool:
    # Usage:
    # result: any = db.query("INSERT INTO table_name (columns) VALUES (%s);", ("value",))

    try:
        # Create connection & cursor
        conn = await createConn()
        cursor = await createCursor(conn)

        
        # Execute
        cursor.execute(query, params)

        # Commit the transaction to persist changes
        conn.commit()

        # Return
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        print(f'{Fore.RED}FAILED TO INSERT DATA{Style.RESET_ALL}: {err}')
        cursor.close()
        conn.close()
        return False
    
async def update(query: str, params: any) -> bool:
    # Usage:
    # result: any = db.query("UPDATE table_name SET column1=%s WHERE column2=%s;", ("value1", "value2",))

    try:
        # Create connection & cursor
        conn = await createConn()
        cursor = await createCursor(conn)

        
        # Execute
        cursor.execute(query, params)

        # Commit the transaction to persist changes
        conn.commit()

        # Return
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        print(f'{Fore.RED}FAILED TO UPDATE DATA{Style.RESET_ALL}: {err}')
        cursor.close()
        conn.close()
        return False
    
async def createTable(query: str) -> bool:
    # Usage:
    # result: any = db.query("create_table_query_here;")

    try:
        # Create connection & cursor
        conn = await createConn()
        cursor = await createCursor(conn)

        
        # Execute
        cursor.execute(query)

        # Return
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        print(f'{Fore.RED}FAILED TO CREATE TABLE{Style.RESET_ALL}: {err}')
        cursor.close()
        conn.close()
        return False
    
async def validateSelect(result): # Returns None if there's no records available
    if not result:
        return None
    return result
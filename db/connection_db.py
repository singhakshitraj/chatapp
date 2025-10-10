import psycopg2
from psycopg2.extras import RealDictCursor
import os
from fastapi.exceptions import HTTPException
from fastapi import status
from dotenv import load_dotenv
def db_connect():
    connection=None
    try:
        load_dotenv()
        connection=psycopg2.connect(
            host=os.environ.get('HOST'),
            port=os.environ.get('PORT'),
            user=os.environ.get('USER'),
            password=os.environ.get('PASSWORD'),
            dbname=os.environ.get('DBNAME'),
            cursor_factory=RealDictCursor
        )
        yield connection
        connection.commit()
    except psycopg2.DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={'details':'Unable to connect to database.'})
    finally:
        if connection is not None:
            connection.close()
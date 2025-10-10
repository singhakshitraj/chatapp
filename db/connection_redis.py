import redis,os
from fastapi import HTTPException,status
from dotenv import load_dotenv

load_dotenv()
def redis_pool():
    try:
        pool=redis.ConnectionPool(
            host=os.environ.get('REDIS_HOST'),
            port=os.environ.get('REDIS_PORT'),
            decode_responses=True
        )
        return pool
    except redis.exceptions.RedisError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail={'message':'Unable to create pool!!'})
    
pool=redis_pool()

def get_redis():
    try:
        redi=redis.Redis(connection_pool=pool)
        redi.ping()
        return redi
    except redis.exceptions.RedisError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail={'message':'Redis not able to connect!!'})
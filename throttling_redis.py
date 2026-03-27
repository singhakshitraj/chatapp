from redis import Redis
from datetime import datetime,timedelta
from dotenv import load_dotenv
import os
from utils.exceptions import TooManyRequestError
from connections.connection_redis import get_redis
load_dotenv()

class RedisThrottling:
    @staticmethod
    def check_validity(username:str):
        rediss=get_redis()
        vals=rediss.zremrangebyscore(username,"-inf",(datetime.now()-timedelta(minutes=int(os.environ.get('SLIDING_WINDOW_SIZE')))).timestamp())
        allowed_requests=int(os.environ.get('NUMBER_OF_ALLOWED_REQUESTS'))
        if rediss.zcard(username)>=allowed_requests:
            raise TooManyRequestError
        rediss.zadd(username,mapping={str(datetime.now()):datetime.now().timestamp()})
        rediss.ping()
        return True
        
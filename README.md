# Chat Application Backend with FastAPI, Redis, and Celery

A scalable and high-performance chat backend built with **FastAPI**, **Redis**, and **Celery** with <i><u>Rate Limiting</u></i> and <i><u>Celery Asynchronous Task Queues</u></i>, designed to handle real-time communication with persistence, throttling, and efficient user management.

## Technologies-
- Python
- FastAPI
- PostgreSQL (Partitioned Tables)
- Redis (As In-Memory Cache as well as Message Brokers runnign of diff. ports)
- Celery (For asynchronous task queue)


## How Things Work

### 1. Partitioned Database

The database, specifically the messages table is partitioned into 4 pieces by hashing the message_id. The specific table is resolved as runtime by a simple hash function -
```
table_id = message_id % number_of_partitions
```
This makes the queries faster because instead of searching thorughout the database, it searches in the specific partitioned section.

### 2. Rate Limiting

Message rate-limiting with Redis is used to prevent overwhelming of the database by excessive requests. The way this works is by employing a sliding-window approach. In redis, we maintain a ```sorted set of timestamps``` of for every user. Before every request, we figure out the number of requests sent by the user in the particular window, and if - 

```
number of requests sent >= the number of allowed requests
``` 

then return a HTTP response ```429 TOO_MANY_REQUESTS``` and an email to the user with Celery as an asynchronous task queue in the background with Redis as the message broker.  

### 3. Chat-Users Caching

The Redis cache is used to store the participants of the chat because it is necessary to store it ```in-memory``` to prevent frequent database hits because of the highly dynamic nature of participants. If it is stored in the db, it would get hit whenever every user becomes offline or leaves the chat.

## Key Features

### 1. Real-time Chat Functionality
- One-to-one and group chats with message persistence.  
- Offline message storage ensures messages are delivered when users reconnect.

### 2. Group Chat Support
- Enables multi-participant communication with efficient Redis-based participant tracking.

### 3. Optimized Message Storage
- **Partitioned message tables** for faster data access and scalability.

### 4. Redis-backed User Presence Management
- Tracks connected users in real time via Redis.  
- Prevents stale socket connections and ensures accurate online/offline tracking.  
- Facilitates instant retrieval of active participants for ongoing chats.

### 5. Offline Message Persistence
- Messages sent to offline users are stored and delivered automatically upon reconnection.  
- Ensures consistent user experience and reliable message delivery.

### 6. Secure Authentication
- JWT-based authentication for secure and efficient user verification.

### 7. Rate Limiting and Throttling
- Implements **sliding window rate limiting** for message control.  
- Prevents message bursts close to interval resets.  
- Sends throttled notification emails using **Celery asynchronous task queues**.

### 8. Celery Asynchronous Processing
- Used for non-blocking tasks such as email throttling notifications.  
- Improves scalability and responsiveness of the chat service.


## Project Setup-

### 1. Clone the repo
```bash
git clone https://github.com/singhakshitraj/chat-application.git
```

### 2. Install dependencies for project
```bash
pip install -r requirements.txt
```

### 3. Configure Project
Frrom the PostgreSQL shell-
#### 1. For Setting Up PostgreSQL Database
```sql
CREATE DATABASE chatapp;
```

#### 2. For migrating db-tables  
From the project root directory, run command in the particular order only because the subsequent ones are dependent on ones before them by Foreign Keys or other relationships.

Order:
```sql
\i 'connections/schemas/users.sql';
\i 'connections/schemas/chats.sql';
\i 'connections/schemas/user_chats.sql';
\i 'connections/schemas/messages.sql';
\i 'connections/schemas/unread_inbox.sql';
```

#### 3. Setup Environment Variables (RANDOM-NAMES USED HERE)
```env
# POSTGRESQL-CONNECT
HOST=localhost
PORT=5432
USER=postgres_user
PASSWORD=postgres_password
DBNAME=chat_app_db

# JWT-AUTH
SECRET_KEY='sample_secret_key_for_jwt_encryption'
ALGORITHM='HS256'
ACCESS_TOKEN_EXPIRE_MINUTES=120

# REDIS-CACHE
REDIS_HOST=localhost
REDIS_PORT=6379

# REDIS-BACKGROUND-WORKER
REDIS_URL='redis://localhost:6379/1'

# EMAIL-CREDENTIALS
MAIL_USERNAME='your_email@example.com'
MAIL_PASSWORD='your_app_specific_password'
MAIL_FROM='your_email@example.com'
MAIL_PORT=587
MAIL_SERVER="smtp.gmail.com"
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
USE_CREDENTIALS=True
VALIDATE_CERTS=True

# REDIS-THROTTLING-SLIDING_WINDOW
SLIDING_WINDOW_SIZE=60        # MINUTES
NUMBER_OF_ALLOWED_REQUESTS=10

```


### 4. Run Application-
I've used memurai.exe for running Redis locally om Windows. 
#### 1. DEV MODE
```bash
uvicorn main:app --reload
celery -A celery_worker.celery_app worker
"Location of Memurai" >> memurai.exe --loglevel DEBUG

```

- `--pool=solo`  
  For running celery on Windows, use `--pool=solo` to disable multiprocessing.
- `--loglevel=info OR --loglevel DEBUG`  
  Enables informational logs for celery/memurai during development.




## Database Design

Messages are stored in **partitioned tables** for faster per-user access and improved scalability. Redis is used to manage socket connections and active chat users.

<img width="1213" height="684" alt="chatapp-db-schema" src="https://github.com/user-attachments/assets/c91d59fe-8428-47dc-9231-ed003784e045" />



## Code Structure

This project is modularized for scalability and maintainability. The key directories are as follows:

```
/connections
├── connection_db.py
├── connection_redis.py
└── ws_connection_manager.py

/routers
├── auth.py
├── chat.py
├── chats_ws.py
└── contacts.py

/utils
├── exceptions.py
├── passwords.py
├── send_email.py
├── token.py
└── validation_models.py

.gitignore
celery_worker.py
main.py
requirements.txt
throttling_redis.py
```


import asyncio
from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException, Depends,APIRouter,Header
from pydantic import BaseModel
from typing import Optional
import bcrypt
from datetime import timedelta, datetime
from jose import JWTError, jwt
from processors.query_executor import QueryExecutor
from app import get_query_executor


SECRET_KEY = "9d6e1d742ed54824a16d0040b145b10a"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60000  # Short-lived token
REFRESH_TOKEN_EXPIRE_DAYS = 7000  # Long-lived token

class User(BaseModel):
    login: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenRefresh(BaseModel):
    refresh_token: str



auth_router = APIRouter()


# Регистрация нового пользователя
@auth_router.post("/register")
async def register(user: User,query_executor: QueryExecutor = Depends(get_query_executor)):
    result = await query_executor.user.create_user(user.login, user.password)
    if result.get("succes")==False:
        raise HTTPException(status_code=400, detail=result)
    return {"message": result}


# Авторизация пользователя и получение JWT
@auth_router.post("/token", response_model=Token)
async def login_for_access_token(user: User, query_executor: QueryExecutor = Depends(get_query_executor)):
    user_info = await query_executor.user.get_user_info(user.login)
    if not user_info or not await query_executor.user.verify_user_password(user.login, user.password):
        raise HTTPException(status_code=401, detail="Invalid login or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    data = {
        "sub": user.login,
        "user_id": user_info[0],
        "user_role": user_info[1]
    }

    access_token = create_access_token(data=data, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data=data, expires_delta=refresh_token_expires)

    return JSONResponse(content={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }, status_code=200)

# Проверка валидности access токена



@auth_router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: TokenRefresh):
    try:
        payload = jwt.decode(refresh_token.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("user_id")
        user_role = payload.get("user_role")

        if not all([username, user_id, user_role]):
            raise HTTPException(status_code=401, detail="Invalid token")

        new_token_data = {
            "sub": username,
            "user_id": user_id,
            "user_role": user_role
        }

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data=new_token_data, expires_delta=access_token_expires)

        return JSONResponse(content={"access_token": access_token, "token_type": "bearer"}, status_code=200)

    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


# Функция для создания JWT токена
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to create refresh token
def create_refresh_token(data: dict, expires_delta: timedelta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(authorization: str = Header(...)) -> dict:
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username = payload.get("sub")
        user_id = payload.get("user_id")
        user_role = payload.get("user_role")

        if not all([username, user_id, user_role]):
            raise HTTPException(status_code=401, detail="Invalid token data")

        return {"username": username, "user_id": user_id, "user_role": user_role}

    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    except IndexError:
        raise HTTPException(status_code=401, detail="Authorization token missing")


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.future import select
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import List

from database import get_pgdb, AsyncSession
from models import User
from routers.auth import get_current_user
from schemas.user import *


router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_current_admin(current_user: User = Depends(get_current_user)):
    if not current_user or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )
    return current_user


@router.get("", response_model=List[UserResponse])
async def get_users(current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_pgdb)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


# THIS IS A TEST ROUTE TO CREATE AN ADMIN USER !!!!
# TODO: TO BE REMOVED IN PRODUCTION
@router.post("/create_test_admin_user", response_model=UserResponse)
async def create_test_admin_user(db: AsyncSession = Depends(get_pgdb)) -> User :
    user_create = UserCreate(username="admin", password="admin", role="admin", email="admin@admin.com")
    result = await db.execute(select(User).filter(User.username == user_create.username))
    user_exists = result.scalar_one_or_none()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    hashed_password = pwd_context.hash(user_create.password)
    user_create.password = hashed_password
    user_data = user_create.model_dump()
    
    db_user = User(**user_data)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return UserResponse.model_validate(db_user)

@router.post("", response_model=UserResponse)
async def create_user(user_create: UserCreate, current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_pgdb)):
    result = await db.execute(select(User).filter(User.username == user_create.username))
    # check if username already exists
    user_exists = result.scalar_one_or_none()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    result = await db.execute(select(User).filter(User.email == user_create.email))
    # check if email already exists
    user_exists = result.scalar_one_or_none()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = pwd_context.hash(user_create.password)
    user_create.password = hashed_password
    user_data = user_create.model_dump()
    
    db_user = User(**user_data)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return UserResponse.model_validate(db_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_pgdb)):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(db_user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_pgdb)):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # check username should not duplicated
    if user_update.username and user_update.username != db_user.username:
        result = await db.execute(select(User).filter(User.username == user_update.username))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Username {user_update.username} already exists")

    if user_update.role not in ['user', 'admin']:
        raise HTTPException(status_code=400, detail=f"Invalid role {user_update.role}")
    
    for key, value in user_update.model_dump(exclude_unset=True).items():
        # password should be hashed
        if key == "password":
            db_user.password =  pwd_context.hash(user_update.password)
        else:
            setattr(db_user, key, value)
   
    await db.commit()
    await db.refresh(db_user)
    return UserResponse.model_validate(db_user)

@router.delete("/{user_id}")
async def delete_user(user_id: int, current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_pgdb) ):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # admin is a special username !
    if db_user.username == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete the system admin user"
        )
    
    # check if this is the last admin user
    if db_user.role == "admin":
        result = await db.execute(select(func.count()).select_from(User).filter(User.role == "admin"))
        admin_count = result.scalar()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last admin user"
            )
    
    await db.delete(db_user)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

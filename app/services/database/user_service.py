"""
User service for database operations related to user management
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func

from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service class for user database operations"""

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> UserModel:
        """
        Create a new user in the database
        
        Args:
            db: Database session
            user_data: User creation data
            
        Returns:
            UserModel: Created user instance
        """
        db_user = UserModel(
            email=user_data.email,
            full_name=user_data.full_name,
            avatar_url=user_data.avatar_url,
            google_id=user_data.google_id,
            is_active=True,
            is_premium=False
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[UserModel]:
        """
        Get user by ID
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Optional[UserModel]: User instance or None
        """
        result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserModel]:
        """
        Get user by email
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            Optional[UserModel]: User instance or None
        """
        result = await db.execute(select(UserModel).where(UserModel.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_google_id(db: AsyncSession, google_id: str) -> Optional[UserModel]:
        """
        Get user by Google ID
        
        Args:
            db: Database session
            google_id: Google ID
            
        Returns:
            Optional[UserModel]: User instance or None
        """
        result = await db.execute(select(UserModel).where(UserModel.google_id == google_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> Optional[UserModel]:
        """
        Update user information
        
        Args:
            db: Database session
            user_id: User ID
            user_data: User update data
            
        Returns:
            Optional[UserModel]: Updated user instance or None
        """
        result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            return None
            
        # Update fields
        for field, value in user_data.dict(exclude_unset=True).items():
            setattr(db_user, field, value)
            
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def update_last_login(db: AsyncSession, user_id: int) -> Optional[UserModel]:
        """
        Update user's last login timestamp
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Optional[UserModel]: Updated user instance or None
        """
        result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            return None
            
        db_user.last_login = func.now()
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """
        Delete user (soft delete by setting is_active to False)
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            bool: True if user was deleted, False otherwise
        """
        result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            return False
            
        db_user.is_active = False
        await db.commit()
        return True
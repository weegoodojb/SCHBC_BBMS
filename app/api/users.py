from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.database.models import User
from app.schemas.schemas import UserResponse, UserCreate, UserUpdate, UserPasswordReset
from app.core.security import hash_password

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    """모든 사용자 목록 조회"""
    users = db.query(User).all()
    return users

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """새로운 사용자 생성"""
    existing_user = db.query(User).filter(User.emp_id == user_in.emp_id).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 직원번호입니다."
        )
    
    new_user = User(
        emp_id=user_in.emp_id,
        name=user_in.name,
        password_hash=hash_password(user_in.password),
        email=user_in.email,
        is_admin=user_in.is_admin,
        remark=user_in.remark
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    """사용자 정보(권한 등) 수정"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    if user_in.name is not None:
        user.name = user_in.name
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.is_admin is not None:
        user.is_admin = user_in.is_admin
    if user_in.remark is not None:
        user.remark = user_in.remark
        
    db.commit()
    db.refresh(user)
    return user

@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, reset_in: UserPasswordReset, db: Session = Depends(get_db)):
    """비밀번호 초기화"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    user.password_hash = hash_password(reset_in.new_password)
    db.commit()
    return {"message": "비밀번호가 성공적으로 변경되었습니다."}

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 삭제"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # Check if trying to delete the last admin
    if user.is_admin == 1:
        admin_count = db.query(User).filter(User.is_admin == 1).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="최소 1명의 관리자가 필요합니다. 삭제할 수 없습니다.")
    
    db.delete(user)
    db.commit()
    return {"message": "사용자가 삭제되었습니다."}

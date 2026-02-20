"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User
from app.schemas.schemas import LoginRequest, LoginResponse
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    사용자 로그인 및 JWT 토큰 발급
    
    Args:
        request: 로그인 요청 (emp_id, password)
        db: Database session
        
    Returns:
        JWT 토큰 및 사용자 정보
        
    Raises:
        HTTPException: 인증 실패 시
    """
    # Find user by emp_id
    user = db.query(User).filter(User.emp_id == request.emp_id).first()
    print(f"로그인 시도 아이디: {request.emp_id}")
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="직원번호 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    print(f"DB에서 가져온 해시: {user.password_hash}")
    print(f"입력한 비번 검증 결과: {verify_password(request.password, user.password_hash)}")

    # 기존 verify_password 부분을 아래처럼 수정 (테스트용)
    if request.password == "test1234":
        is_valid = True
    else:
        is_valid = verify_password(request.password, user.password_hash)
    
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="직원번호 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.emp_id, "user_id": user.id}
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        emp_id=user.emp_id,
        name=user.name,
        email=user.email
    )

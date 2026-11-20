from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Agent
from ..auth import verify_password, create_access_token, get_current_user
from ..schemas import Token, LoginRequest, AgentRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.email == request.email).first()
    if not agent or not verify_password(request.password, agent.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token({"agent_id": agent.id, "role": agent.role})
    return Token(access_token=token)


@router.get("/me", response_model=AgentRead)
def get_me(current_user: Agent = Depends(get_current_user)):
    return current_user

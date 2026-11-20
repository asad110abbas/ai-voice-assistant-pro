from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Agent, EscalationTicket
from ..schemas import AgentCreate, AgentUpdate, AgentRead
from ..auth import get_current_user, hash_password, role_required

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("")
def list_agents(
    db: Session = Depends(get_db),
    _: Agent = Depends(role_required("admin")),
):
    agents = db.query(Agent).all()
    result = []
    for agent in agents:
        open_count = db.query(EscalationTicket).filter(
            EscalationTicket.assigned_to == agent.id,
            EscalationTicket.status != "resolved",
        ).count()
        result.append({
            "id": agent.id,
            "email": agent.email,
            "name": agent.name,
            "role": agent.role,
            "created_at": agent.created_at,
            "open_ticket_count": open_count,
        })
    return result


@router.post("", response_model=AgentRead)
def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db),
    _: Agent = Depends(role_required("admin")),
):
    existing = db.query(Agent).filter(Agent.email == agent_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    agent = Agent(
        email=agent_data.email,
        name=agent_data.name,
        role=agent_data.role,
        hashed_password=hash_password(agent_data.password),
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.patch("/{agent_id}", response_model=AgentRead)
def update_agent(
    agent_id: int,
    update: AgentUpdate,
    db: Session = Depends(get_db),
    _: Agent = Depends(role_required("admin")),
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if update.email is not None:
        agent.email = update.email
    if update.name is not None:
        agent.name = update.name
    if update.role is not None:
        agent.role = update.role

    db.commit()
    db.refresh(agent)
    return agent

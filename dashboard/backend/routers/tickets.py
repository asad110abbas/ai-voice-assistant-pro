from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from ..database import get_db
from ..models import EscalationTicket, Agent, Notification, TicketNote
from ..schemas import TicketRead, TicketUpdate, NoteCreate, NoteRead
from ..auth import get_current_user
from ..email_service import send_assignment_email

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("")
def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Agent = Depends(get_current_user),
):
    query = db.query(EscalationTicket)

    if current_user.role == "agent":
        query = query.filter(EscalationTicket.assigned_to == current_user.id)

    if status:
        query = query.filter(EscalationTicket.status == status)
    if assigned_to is not None:
        query = query.filter(EscalationTicket.assigned_to == assigned_to)
    if keyword:
        query = query.filter(EscalationTicket.issue_summary.contains(keyword))

    total = query.count()
    tickets = query.order_by(EscalationTicket.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {"total": total, "page": page, "page_size": page_size, "items": tickets}


@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(
    ticket_id: int,
    update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: Agent = Depends(get_current_user),
):
    ticket = db.query(EscalationTicket).filter(EscalationTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if update.status == "resolved" and not update.resolution_note and not ticket.resolution_note:
        raise HTTPException(
            status_code=400,
            detail="resolution_note is required when resolving a ticket",
        )

    if update.status is not None:
        ticket.status = update.status
    if update.resolution_note is not None:
        ticket.resolution_note = update.resolution_note
    ticket.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/assign")
def assign_ticket(
    ticket_id: int,
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: Agent = Depends(get_current_user),
):
    if current_user.role not in ("admin", "senior_agent"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    ticket = db.query(EscalationTicket).filter(EscalationTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    ticket.assigned_to = agent_id
    ticket.status = "assigned"
    ticket.updated_at = datetime.utcnow()

    notification = Notification(
        agent_id=agent_id,
        type="ticket_assigned",
        message=f"Ticket #{ticket_id} has been assigned to you: {ticket.issue_summary[:100]}",
    )
    db.add(notification)
    db.commit()

    send_assignment_email(agent.email, ticket_id, ticket.issue_summary)

    return {"message": f"Ticket #{ticket_id} assigned to {agent.name}"}


@router.get("/{ticket_id}/notes")
def get_notes(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_user),
):
    notes = db.query(TicketNote).filter(TicketNote.ticket_id == ticket_id).all()
    return notes


@router.post("/{ticket_id}/notes", response_model=NoteRead)
def add_note(
    ticket_id: int,
    note: NoteCreate,
    db: Session = Depends(get_db),
    current_user: Agent = Depends(get_current_user),
):
    ticket = db.query(EscalationTicket).filter(EscalationTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    new_note = TicketNote(
        ticket_id=ticket_id,
        agent_id=current_user.id,
        content=note.content,
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

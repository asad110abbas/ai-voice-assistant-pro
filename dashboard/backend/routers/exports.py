from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
import io
from ..database import get_db
from ..models import CallRecord, EscalationTicket, Agent
from ..auth import get_current_user
from ..export_service import calls_to_csv, tickets_to_csv, ticket_to_pdf

router = APIRouter(prefix="/export", tags=["exports"])


@router.get("/calls.csv")
def export_calls_csv(
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_user),
):
    records = db.query(CallRecord).all()
    csv_data = calls_to_csv(records)
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=calls.csv"},
    )


@router.get("/tickets.csv")
def export_tickets_csv(
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_user),
):
    tickets = db.query(EscalationTicket).all()
    csv_data = tickets_to_csv(tickets)
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tickets.csv"},
    )


@router.get("/tickets/{ticket_id}.pdf")
def export_ticket_pdf(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_user),
):
    ticket = db.query(EscalationTicket).filter(EscalationTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    pdf_bytes = ticket_to_pdf(ticket)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=ticket_{ticket_id}.pdf"},
    )

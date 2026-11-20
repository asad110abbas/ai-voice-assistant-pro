import csv
import io
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from .models import CallRecord, EscalationTicket


def calls_to_csv(call_records: List[CallRecord]) -> str:
    """Returns CSV string of call records."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "start_time", "end_time", "duration", "language", "escalated"])

    for record in call_records:
        writer.writerow([
            record.id,
            record.start_time,
            record.end_time,
            record.duration_seconds,
            record.language,
            record.escalated,
        ])

    return output.getvalue()


def tickets_to_csv(tickets: List[EscalationTicket]) -> str:
    """Returns CSV string of escalation tickets."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "issue_summary", "status", "assigned_to", "created_at", "resolution_note"])

    for ticket in tickets:
        writer.writerow([
            ticket.id,
            ticket.issue_summary,
            ticket.status,
            ticket.assigned_to,
            ticket.created_at,
            ticket.resolution_note or "",
        ])

    return output.getvalue()


def ticket_to_pdf(ticket: EscalationTicket) -> bytes:
    """Returns PDF bytes for a single ticket via reportlab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Briha Support — Ticket #{ticket.id}", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Issue:</b> {ticket.issue_summary}", styles["Normal"]))
    story.append(Paragraph(f"<b>Status:</b> {ticket.status}", styles["Normal"]))
    story.append(Paragraph(f"<b>Created:</b> {ticket.created_at}", styles["Normal"]))
    story.append(Spacer(1, 12))

    if ticket.resolution_note:
        story.append(Paragraph("<b>Resolution Note:</b>", styles["Heading3"]))
        story.append(Paragraph(ticket.resolution_note, styles["Normal"]))
        story.append(Spacer(1, 12))

    if ticket.conversation:
        story.append(Paragraph("<b>Conversation Transcript:</b>", styles["Heading3"]))
        for turn in ticket.conversation:
            role = turn.get("role", "unknown").capitalize()
            content = str(turn.get("content", ""))
            story.append(Paragraph(f"<b>{role}:</b> {content}", styles["Normal"]))
        story.append(Spacer(1, 12))

    if ticket.notes:
        story.append(Paragraph("<b>Internal Notes:</b>", styles["Heading3"]))
        for note in ticket.notes:
            story.append(Paragraph(f"- {note.content} (Agent #{note.agent_id})", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

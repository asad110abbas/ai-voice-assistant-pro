from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="agent")  # admin, senior_agent, agent
    created_at = Column(DateTime, default=datetime.utcnow)

    assigned_tickets = relationship("EscalationTicket", foreign_keys="EscalationTicket.assigned_to", back_populates="assignee")
    notes = relationship("TicketNote", back_populates="agent")
    notifications = relationship("Notification", back_populates="agent")


class CallRecord(Base):
    __tablename__ = "call_records"

    id = Column(Integer, primary_key=True, index=True)
    session_dir = Column(String, unique=True, nullable=False)
    start_time = Column(String)
    end_time = Column(String)
    duration_seconds = Column(Float, default=0.0)
    language = Column(String, default="en")
    transcript = Column(JSON)
    escalated = Column(Boolean, default=False)
    outcome = Column(String, default="bot_handled")  # bot_handled | agent_transfer | spam | timeout
    cost_usd = Column(Float, default=0.0)
    audio_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    tickets = relationship("EscalationTicket", back_populates="call_record")


class EscalationTicket(Base):
    __tablename__ = "escalation_tickets"

    id = Column(Integer, primary_key=True, index=True)
    call_record_id = Column(Integer, ForeignKey("call_records.id"), nullable=True)
    issue_summary = Column(Text, nullable=False)
    status = Column(String, default="open")  # open, assigned, resolved
    assigned_to = Column(Integer, ForeignKey("agents.id"), nullable=True)
    conversation = Column(JSON)
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    call_record = relationship("CallRecord", back_populates="tickets")
    assignee = relationship("Agent", foreign_keys=[assigned_to], back_populates="assigned_tickets")
    notes = relationship("TicketNote", back_populates="ticket")


class TicketNote(Base):
    __tablename__ = "ticket_notes"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("escalation_tickets.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("EscalationTicket", back_populates="notes")
    agent = relationship("Agent", back_populates="notes")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    type = Column(String, nullable=False)  # new_escalation, ticket_assigned
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="notifications")

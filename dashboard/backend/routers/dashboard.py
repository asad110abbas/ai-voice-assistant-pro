from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import CallRecord, EscalationTicket, Agent
from ..auth import get_current_user

AGENT_MONTHLY_SALARY_PKR = 30_000
PKR_TO_USD = 278.0
AGENT_CALLS_PER_MONTH = 3_000

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_user),
):
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())

    total_calls_today = db.query(CallRecord).filter(
        CallRecord.created_at >= today_start
    ).count()

    open_tickets = db.query(EscalationTicket).filter(
        EscalationTicket.status.in_(["open", "assigned"])
    ).count()

    resolved_today = db.query(EscalationTicket).filter(
        EscalationTicket.status == "resolved",
        EscalationTicket.updated_at >= today_start,
    ).count()

    avg_duration_result = db.query(func.avg(CallRecord.duration_seconds)).filter(
        CallRecord.created_at >= today_start
    ).scalar()
    avg_duration = round(avg_duration_result or 0, 2)

    return {
        "total_calls_today": total_calls_today,
        "open_tickets": open_tickets,
        "resolved_today": resolved_today,
        "avg_duration_seconds": avg_duration,
    }


@router.get("/analytics")
def get_analytics(
    type: str = Query(...),
    days: int = Query(30),
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_user),
):
    if type == "call_volume":
        since = datetime.utcnow() - timedelta(days=days)
        records = db.query(CallRecord).filter(CallRecord.created_at >= since).all()
        counts: dict = {}
        for r in records:
            date_str = r.created_at.strftime("%Y-%m-%d")
            counts[date_str] = counts.get(date_str, 0) + 1
        return [{"date": d, "count": c} for d, c in sorted(counts.items())]

    elif type == "resolution_time":
        resolved = db.query(EscalationTicket).filter(
            EscalationTicket.status == "resolved"
        ).all()
        if not resolved:
            return {"avg_hours": 0}
        total_hours = sum(
            (t.updated_at - t.created_at).total_seconds() / 3600
            for t in resolved
            if t.updated_at and t.created_at
        )
        return {"avg_hours": round(total_hours / len(resolved), 2)}

    elif type == "agent_performance":
        agents = db.query(Agent).all()
        result = []
        for agent in agents:
            all_tickets = db.query(EscalationTicket).filter(
                EscalationTicket.assigned_to == agent.id
            ).all()
            resolved = [t for t in all_tickets if t.status == "resolved"]
            open_count = len([t for t in all_tickets if t.status != "resolved"])
            avg_hrs = 0.0
            if resolved:
                total = sum(
                    (t.updated_at - t.created_at).total_seconds() / 3600
                    for t in resolved
                    if t.updated_at and t.created_at
                )
                avg_hrs = round(total / len(resolved), 2)
            result.append({
                "agent_id": agent.id,
                "name": agent.name,
                "tickets_handled": len(all_tickets),
                "avg_resolution_hours": avg_hrs,
                "open_tickets": open_count,
            })
        return result

    return {"error": "Unknown analytics type"}


@router.get("/call_outcomes")
def get_call_outcomes(
    days: int = Query(30),
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_user),
):
    since = datetime.utcnow() - timedelta(days=days)
    records = db.query(CallRecord).filter(CallRecord.created_at >= since).all()

    counts = {"bot_handled": 0, "agent_transfer": 0, "spam": 0, "timeout": 0}
    for r in records:
        outcome = r.outcome or "bot_handled"
        if outcome in counts:
            counts[outcome] += 1
        else:
            counts["bot_handled"] += 1

    return counts


@router.get("/cost")
def get_cost(
    days: int = Query(30),
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_user),
):
    since = datetime.utcnow() - timedelta(days=days)
    records = db.query(CallRecord).filter(CallRecord.created_at >= since).all()

    total_calls = len(records)
    total_bot_cost = sum(r.cost_usd or 0.0 for r in records)
    avg_cost = round(total_bot_cost / total_calls, 6) if total_calls else 0.0

    # Extrapolate to monthly if days != 30
    bot_monthly_cost = round(total_bot_cost * (30 / days), 4) if days else 0.0

    agent_monthly_usd = round(AGENT_MONTHLY_SALARY_PKR / PKR_TO_USD, 2)
    agent_cost_per_call = round(agent_monthly_usd / AGENT_CALLS_PER_MONTH, 4)

    savings_pct = 0.0
    if agent_monthly_usd > 0:
        savings_pct = round((1 - bot_monthly_cost / agent_monthly_usd) * 100, 1)
        savings_pct = max(0.0, min(savings_pct, 100.0))

    return {
        "total_bot_cost_usd": round(total_bot_cost, 4),
        "avg_cost_per_call_usd": avg_cost,
        "total_calls": total_calls,
        "bot_monthly_cost_usd": bot_monthly_cost,
        "agent_monthly_cost_pkr": AGENT_MONTHLY_SALARY_PKR,
        "agent_monthly_cost_usd": agent_monthly_usd,
        "agent_cost_per_call_usd": agent_cost_per_call,
        "savings_percent": savings_pct,
    }

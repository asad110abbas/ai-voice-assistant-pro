import json
import os
from fastapi import APIRouter, Depends, HTTPException
from ..models import Agent
from ..auth import role_required

router = APIRouter(tags=["blocklist"])

BLOCKLIST_FILE = os.getenv("BLOCKLIST_FILE", "../../blocklist.json")
ABUSE_LOG_FILE = os.getenv("ABUSE_LOG_FILE", "../../abuse_log.json")


@router.get("/blocklist")
def get_blocklist(_: Agent = Depends(role_required("admin"))):
    if not os.path.exists(BLOCKLIST_FILE):
        return []
    try:
        with open(BLOCKLIST_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except (json.JSONDecodeError, IOError):
        return []


@router.delete("/blocklist/{ip}")
def unblock_ip(ip: str, _: Agent = Depends(role_required("admin"))):
    if not os.path.exists(BLOCKLIST_FILE):
        raise HTTPException(status_code=404, detail="IP not found in blocklist")

    try:
        with open(BLOCKLIST_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            blocklist = json.loads(content) if content else []
    except (json.JSONDecodeError, IOError):
        raise HTTPException(status_code=500, detail="Could not read blocklist")

    original_len = len(blocklist)
    blocklist = [entry for entry in blocklist if entry.get("ip") != ip]

    if len(blocklist) == original_len:
        raise HTTPException(status_code=404, detail="IP not found in blocklist")

    with open(BLOCKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(blocklist, f, ensure_ascii=False, indent=2)

    return {"message": f"IP {ip} removed from blocklist"}


@router.get("/abuse-log")
def get_abuse_log(_: Agent = Depends(role_required("admin"))):
    if not os.path.exists(ABUSE_LOG_FILE):
        return []
    try:
        with open(ABUSE_LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except (json.JSONDecodeError, IOError):
        return []

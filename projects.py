from datetime import datetime
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import ReturnDocument

import db as dbmod
from models import ProjectIn, ProjectOut
from auth import get_current_user  # auth.py-ում արդեն ունենք

router = APIRouter(prefix="/projects", tags=["projects"])


def _to_out(d: dict) -> ProjectOut:
    return {
        "id": str(d["_id"]),
        "title": d["title"],
        "description": d.get("description"),
        "owner_id": str(d["owner_id"]),
        "created_at": d["created_at"],
    }


@router.post("", response_model=ProjectOut)
async def create_project(data: ProjectIn, user=Depends(get_current_user)):
    if dbmod.db is None:
        raise HTTPException(503, "DB not ready")
    doc = {
        "title": data.title,
        "description": data.description,
        "owner_id": ObjectId(user["_id"]),
        "created_at": datetime.utcnow(),
    }
    res = await dbmod.db.projects.insert_one(doc)
    doc["_id"] = res.inserted_id
    return _to_out(doc)


@router.get("", response_model=List[ProjectOut])
async def list_projects(
    user=Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    if dbmod.db is None:
        raise HTTPException(503, "DB not ready")
    cur = (
        dbmod.db.projects.find({"owner_id": ObjectId(user["_id"])})
        .skip(skip)
        .limit(limit)
        .sort("created_at", -1)
    )
    return [_to_out(d) async for d in cur]


@router.get("/{pid}", response_model=ProjectOut)
async def get_project(pid: str, user=Depends(get_current_user)):
    if dbmod.db is None:
        raise HTTPException(503, "DB not ready")
    doc = await dbmod.db.projects.find_one(
        {"_id": ObjectId(pid), "owner_id": ObjectId(user["_id"])}
    )
    if not doc:
        raise HTTPException(404, "Not found")
    return _to_out(doc)


@router.put("/{pid}", response_model=ProjectOut)
async def update_project(pid: str, data: ProjectIn, user=Depends(get_current_user)):
    if dbmod.db is None:
        raise HTTPException(503, "DB not ready")
    res = await dbmod.db.projects.find_one_and_update(
        {"_id": ObjectId(pid), "owner_id": ObjectId(user["_id"])},
        {"$set": {"title": data.title, "description": data.description}},
        return_document=ReturnDocument.AFTER,
    )
    if not res:
        raise HTTPException(404, "Not found")
    return _to_out(res)


@router.delete("/{pid}")
async def delete_project(pid: str, user=Depends(get_current_user)):
    if dbmod.db is None:
        raise HTTPException(503, "DB not ready")
    r = await dbmod.db.projects.delete_one(
        {"_id": ObjectId(pid), "owner_id": ObjectId(user["_id"])}
    )
    if r.deleted_count == 0:
        raise HTTPException(404, "Not found")
    return {"ok": True}

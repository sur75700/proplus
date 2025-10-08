from fastapi import Query

def get_pagination(page: int = Query(1, ge=1), limit: int = Query(25, ge=1, le=200)):
    skip = (page - 1) * limit
    return {"page": page, "limit": limit, "skip": skip}

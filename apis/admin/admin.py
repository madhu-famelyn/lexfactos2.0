from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from schemas.admin.admin import AdminCreate, AdminUpdate, AdminResponse
from service.admin.admin import AdminService
from config.db.session import get_db

admin_router = APIRouter(prefix="/admins", tags=["Admin"])

# ------------------------------
# Create Admin
# ------------------------------
@admin_router.post("/", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
def create_admin(data: AdminCreate, db: Session = Depends(get_db)):
    try:
        return AdminService.create_admin(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ------------------------------
# Get All Admins
# ------------------------------
@admin_router.get("/", response_model=List[AdminResponse])
def list_admins(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return AdminService.get_all_admins(db, skip=skip, limit=limit)

# ------------------------------
# Get Admin by ID
# ------------------------------
@admin_router.get("/{admin_id}", response_model=AdminResponse)
def get_admin(admin_id: str, db: Session = Depends(get_db)):
    try:
        return AdminService.get_admin_by_id(db, admin_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ------------------------------
# Update Admin
# ------------------------------
@admin_router.put("/{admin_id}", response_model=AdminResponse)
def update_admin(admin_id: str, updates: AdminUpdate, db: Session = Depends(get_db)):
    try:
        admin = AdminService.get_admin_by_id(db, admin_id)
        return AdminService.update_admin(db, admin, updates)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ------------------------------
# Delete Admin
# ------------------------------
@admin_router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin(admin_id: str, db: Session = Depends(get_db)):
    try:
        admin = AdminService.get_admin_by_id(db, admin_id)
        AdminService.delete_admin(db, admin)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return

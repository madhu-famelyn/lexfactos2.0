from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import json
from pydantic import EmailStr
from sqlalchemy import func
from fastapi import Query

from config.db.session import get_db

from schemas.lawyer.lawyer import (
    LawyerCreate,
    LawyerUpdate,
    LawyerStatusUpdate,
    LawyerResponse,
    LawyerExcelUpload
)

from service.lawyer.lawyer import LawyerService

lawyer_router = APIRouter(prefix="/lawyers", tags=["Lawyers"])


# ============================================================
# CREATE LAWYER (Single)








@lawyer_router.get("/search-by-country")
def search_lawyers_by_country(
    country: str = Query(..., description="Country to filter"),
    keyword: str = Query(None, description="Optional keyword search"),
    start: int = Query(1, ge=1),
    end: int = Query(10, ge=1),
    db: Session = Depends(get_db)
):
    return LawyerService.search_lawyers_by_country(
        db=db,
        country=country,
        keyword=keyword,
        start=start,
        end=end
    )





@lawyer_router.post("/", response_model=LawyerResponse)
async def create_lawyer(
    full_name: str = Form(...),
    address_line_1: str = Form(...),
    address_line_2: str = Form(None),
    city: str = Form(...),
    state: str = Form(...),
    country: str = Form(...),
    zip_code: str = Form(...),
    email: EmailStr = Form(...),
    phone_number: str = Form(...),
    password: str = Form(...),
    website_link: str = Form(None),
    linkedin_link: str = Form(None),
    known_languages: str = Form(None),
    profile_photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    langs = known_languages.split(",") if known_languages else None

    data = LawyerCreate(
        full_name=full_name,
        address_line_1=address_line_1,
        address_line_2=address_line_2,
        city=city,
        state=state,
        country=country,
        zip_code=zip_code,
        email=email,
        phone_number=phone_number,
        password=password,
        website_link=website_link,
        linkedin_link=linkedin_link,
        known_languages=langs
    )

    return LawyerService.create_lawyer(db, data, profile_photo)

# ============================================================
# GET ALL LAWYERS
# ============================================================
@lawyer_router.get("/", response_model=List[LawyerResponse])
def get_all(db: Session = Depends(get_db)):
    return LawyerService.get_all_lawyers(db)


# ============================================================
# GET LAWYERS BY STATUS
# ============================================================
@lawyer_router.get("/status/{status}", response_model=List[LawyerResponse])
def get_by_status(status: str, db: Session = Depends(get_db)):
    try:
        return LawyerService.get_lawyers_by_status(db, status)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# BULK IMPORT FROM EXCEL
# ============================================================


@lawyer_router.post("/bulk-upload", response_model=List[LawyerResponse])
async def bulk_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        df = pd.read_excel(file.file)

        # Replace NaN with None
        df = df.where(pd.notnull(df), None)

        processed_rows = []

        for row in df.to_dict(orient="records"):

            # Convert zip_code → string
            if row.get("zip_code") is not None:
                row["zip_code"] = str(row["zip_code"])

            # Convert phone_number → string
            if row.get("phone_number") is not None:
                row["phone_number"] = str(row["phone_number"])

            # known_languages: JSON string → list
            if isinstance(row.get("known_languages"), str):
                row["known_languages"] = json.loads(row["known_languages"])

            processed_rows.append(LawyerExcelUpload(**row))

        return LawyerService.bulk_create_lawyers(db, processed_rows)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))






# ============================================================
# GET LAWYER BY PRIMARY ID
# ============================================================
@lawyer_router.get("/{id}", response_model=LawyerResponse)
def get_by_id(id: str, db: Session = Depends(get_db)):
    try:
        return LawyerService.get_lawyer_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# UPDATE LAWYER (Full or Partial)
# ============================================================
@lawyer_router.put("/{id}", response_model=LawyerResponse)
def update_lawyer(id: str, update_data: LawyerUpdate, db: Session = Depends(get_db)):
    try:
        return LawyerService.update_lawyer(db, id, update_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# UPDATE LAWYER STATUS ONLY
# ============================================================
@lawyer_router.patch("/{id}/status", response_model=LawyerResponse)
def update_status(id: str, status_data: LawyerStatusUpdate, db: Session = Depends(get_db)):
    try:
        return LawyerService.update_lawyer_status(db, id, status_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))




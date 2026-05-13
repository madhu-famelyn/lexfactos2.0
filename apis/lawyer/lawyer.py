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
    LawyerExcelUpload,
    UpdateLawyerPositionRequest
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
    city: str = Form(...),
    state: str = Form(...),
    country: str = Form(...),
    zip_code: str = Form(...),
    email: EmailStr = Form(...),
    phone_number: str = Form(...),
    password: str = Form(...),
    website_link: str = Form(None),
    linkedin_link: str = Form(None),
    bio: str = Form(None),
    practice_areas: str = Form(None),
    courts: str = Form(None),
    known_languages: str = Form(None),

    # ✅ NEW FIELD
    experience: int = Form(None),

    profile_photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    langs = [lang.strip() for lang in known_languages.split(",") if lang.strip()] if known_languages else None
    areas = [area.strip() for area in practice_areas.split(",") if area.strip()] if practice_areas else None
    court_list = [court.strip() for court in courts.split(",") if court.strip()] if courts else None

    data = LawyerCreate(
        full_name=full_name,
        address_line_1=address_line_1,
        city=city,
        state=state,
        country=country,
        zip_code=zip_code,
        email=email,
        phone_number=phone_number,
        password=password,
        website_link=website_link,
        linkedin_link=linkedin_link,
        bio=bio,
        practice_areas=areas,
        courts=court_list,
        known_languages=langs,
        experience=experience
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

        # Normalize column headers → strip whitespace, lowercase, spaces→underscores
        # So "Bio", "Image URL", "Known Languages" all map correctly
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

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

            # JSON list columns — support both JSON arrays and plain "A, B, C" CSV strings
            for list_col in ("known_languages", "practice_areas", "courts"):
                raw = row.get(list_col)
                if isinstance(raw, str):
                    stripped = raw.strip()
                    if not stripped:
                        row[list_col] = None  # empty cell → null
                    elif stripped.startswith("["):
                        # Proper JSON array → parse it
                        try:
                            row[list_col] = json.loads(stripped)
                        except json.JSONDecodeError:
                            # Malformed JSON — fall back to comma split
                            row[list_col] = [v.strip() for v in stripped.strip("[]").split(",") if v.strip()]
                    else:
                        # Plain "Telugu, Hindi, English" → split by comma
                        row[list_col] = [v.strip() for v in stripped.split(",") if v.strip()]


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


# ============================================================
# BULK DELETE LAWYERS BY STATUS (Admin Only)
# ============================================================
@lawyer_router.delete("/admin/bulk-delete/{status}")
def bulk_delete_lawyers_by_status(status: str, db: Session = Depends(get_db)):
    """
    Delete all lawyers with a specific status.
    Status must be: pending, approved, or rejected
    
    Usage: DELETE /lawyers/admin/bulk-delete/approved
    """
    try:
        result = LawyerService.delete_lawyers_by_status(db, status)
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete lawyers")


# ============================================================
# DELETE LAWYER (Single)
# ============================================================
@lawyer_router.delete("/{id}")
def delete_lawyer(id: str, db: Session = Depends(get_db)):
    try:
        result = LawyerService.delete_lawyer(db, id)
        return result
    except ValueError:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete lawyer")






@lawyer_router.put("/{lawyer_id}/position")
def change_lawyer_position(
    lawyer_id: str,
    payload: UpdateLawyerPositionRequest,
    db: Session = Depends(get_db)
):
    lawyer = LawyerService.update_lawyer_position(
        db=db,
        lawyer_id=lawyer_id,
        position_status=payload.position_status,
        position_status_days=payload.position_status_days
    )

    return {
        "success": True,
        "message": "Lawyer position updated successfully",
        "data": {
            "lawyer_id": lawyer.id,
            "position_status": lawyer.position_status,
            "position_status_days": lawyer.position_status_days,
            "position_status_expiry": lawyer.position_status_expiry
        }
    }

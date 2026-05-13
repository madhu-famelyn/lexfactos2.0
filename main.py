from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import os

# ✅ Import all models to initialize relationships
import models.base

# ✅ App configuration
env = os.getenv("ENV", "dev")

app = FastAPI(
    title="Lexfactos",
    version="1.0.0",
    docs_url="/docs" if env in ["dev", "staging"] else None,
    redoc_url=None,
    openapi_url="/openapi.json" if env in ["dev", "staging"] else None,
)

# ✅ Global CORS configuration (must be added AFTER app creation and BEFORE route definition)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://lexfactos.com",
        "https://www.lexfactos.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# ✅ Universal preflight handler
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return JSONResponse(content={"message": "CORS preflight OK"})

# ============================================================
# ✅ LOADER.IO VERIFICATION (REQUIRED)
# ============================================================

@app.get("/loaderio-18417bec5160efb8d991b24b7ff945dc.txt")
async def loaderio_verification():
    return PlainTextResponse(
        "loaderio-18417bec5160efb8d991b24b7ff945dc"
    )

# ============================================================
# ✅ ROUTER REGISTRATION
# ============================================================
def include_routers(app: FastAPI):
    from apis.admin.admin import admin_router
    from apis.admin.auth import auth_router
    from apis.lawyer.lawyer import lawyer_router
    from apis.users.user import user_router
    from apis.reviews.reviews import review_router
    from apis.message.message import message_router

    # Admin
    app.include_router(admin_router)
    app.include_router(auth_router)

    # Lawyer
    app.include_router(lawyer_router)

    # User
    app.include_router(user_router)

    # Review
    app.include_router(review_router)

    # Message
    app.include_router(message_router)

# ✅ Load routers immediately (before startup)
include_routers(app)

# ✅ Local development entrypoint
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )

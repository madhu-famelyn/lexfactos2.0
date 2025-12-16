from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

# ✅ App configuration
env = os.getenv("ENV", "dev")

app = FastAPI(
    title="Lexfactos",
    version="1.0.0",
    docs_url="/docs" if env in ["dev", "staging"] else None,
    redoc_url=None,
    openapi_url="/openapi.json" if env in ["dev", "staging"] else None,
)

# ✅ Global CORS configuration (fixed regex)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://www.lexfactos.com"

    ],
    allow_origin_regex=r"https://(?:.*\.)?fliplyn-(user|customer)\.(?:pages\.dev|onrender\.com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# ✅ Universal preflight handler (handles OPTIONS requests)
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return JSONResponse(content={"message": "CORS preflight OK"})

# ✅ Lazy load routers (imported on startup to avoid circular imports)
def include_routers(app: FastAPI):
    # --- Admin Routers ---
    from apis.admin.admin import admin_router
    from apis.admin.auth import auth_router
    from apis.lawyer.lawyer import lawyer_router
    from apis.users.user import user_router
    from apis.reviews.reviews import review_router
    from apis.message.message import message_router
  
#admin router
    app.include_router(admin_router)
    app.include_router(auth_router)
    


#lawyer router
    app.include_router(lawyer_router)


#user router

    app.include_router(user_router)

#review router

    app.include_router(review_router)

#message router
    app.include_router(message_router)

   

 
 
# ✅ Load routers on startup
@app.on_event("startup")
async def startup_event():
    include_routers(app)
    print("🚀 FastAPI app started with routers loaded!")

# ✅ For local development
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        reload_exclude=["node_modules", "migrations"],
    )

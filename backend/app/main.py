import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, categories, fields, modules, records, system, upload, users
from app.core.config import settings
from app.services.backup import auto_backup_loop
from app.core.secrets import ensure_secrets
from app.services.bootstrap import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 确保数据子目录存在 → 密钥 → 建表 + 轻量迁移 + 初始化管理员
    settings.upload_dir_path
    settings.backup_dir_path
    ensure_secrets()
    init_database()
    stop_backup_task = asyncio.Event()
    backup_task = asyncio.create_task(auto_backup_loop(stop_backup_task))
    yield
    stop_backup_task.set()
    await backup_task


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

# CORS — allow dev frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:17500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API routes (all under /api/v1)
api_prefix = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=api_prefix)
app.include_router(users.router, prefix=api_prefix)
app.include_router(categories.router, prefix=api_prefix)
app.include_router(fields.router, prefix=api_prefix)
app.include_router(modules.router, prefix=api_prefix)
app.include_router(records.router, prefix=api_prefix)
app.include_router(upload.router, prefix=api_prefix)
app.include_router(system.router, prefix=api_prefix)


# Serve static frontend if built (production)
static_path = settings.static_dir_path
if static_path:
    static_root = static_path.resolve()
    assets_dir = static_root / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        # Don't intercept API
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        if full_path:
            candidate = (static_root / full_path).resolve()
            if static_root in candidate.parents and candidate.is_file():
                return FileResponse(candidate)
        index = static_root / "index.html"
        if index.exists():
            return FileResponse(index)
        return {"detail": "Frontend not built"}

else:

    @app.get("/")
    def root():
        return {
            "name": settings.PROJECT_NAME,
            "docs": f"{settings.API_V1_PREFIX}/docs",
            "note": "Frontend not built. Run `npm run dev` in frontend/.",
        }

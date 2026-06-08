from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from . import db, crud
from .crud import AliasConflictError
from .schemas import ShortenRequest, ShortenResponse, LinkMeta
from .cache import SimpleCache

app = FastAPI(title="URL Shortener")

# initialize DB and cache
db.init_db()
cache = SimpleCache(ttl_seconds=300, max_items=2000)


def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()


@app.post("/shorten", response_model=ShortenResponse, status_code=201)
def shorten(req: ShortenRequest, session: Session = Depends(get_db)):
    """Create a shortened URL.
    
    Accepts a target URL and optional custom alias.
    Returns the shortened link metadata with HTTP 201 Created.
    """
    try:
        # Ensure target_url is a plain string when persisting (Pydantic HttpUrl may
        # be a rich type on Pydantic v2). Convert to str to avoid DB binding errors.
        link = crud.create_link(
            session,
            str(req.target_url),
            custom_alias=req.custom_alias,
            expires_at=req.expires_at,
        )
    except AliasConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    # populate cache
    cache.set(link.alias, link.target_url)

    return ShortenResponse(
        alias=link.alias,
        target_url=link.target_url,
        created_at=link.created_at,
        access_count=link.access_count,
        expires_at=link.expires_at,
    )


@app.get("/{alias}")
def redirect_alias(alias: str, session: Session = Depends(get_db)):
    """Redirect to the original URL for a shortened alias.
    
    Returns HTTP 307 Temporary Redirect. No response_model is used because
    this endpoint returns a redirect response, not JSON data.
    """
    link = crud.get_link_by_alias(session, alias)
    if not link:
        raise HTTPException(status_code=404, detail="Alias not found")

    # use cache for resolved target if available
    target = cache.get(alias)
    if not target:
        target = link.target_url
        cache.set(alias, target)

    # increment access count
    try:
        crud.increment_access(session, link.id)
    except Exception:
        # non-fatal for redirect
        session.rollback()

    return RedirectResponse(url=target, status_code=307)


@app.get("/{alias}/meta", response_model=LinkMeta)
def meta(alias: str, session: Session = Depends(get_db)):
    """Retrieve metadata for a shortened URL.
    
    Returns the alias, target URL, creation time, access count, and expiration info.
    Uses response_model to validate and document the JSON response.
    """
    link = crud.get_link_by_alias(session, alias)
    if not link:
        raise HTTPException(status_code=404, detail="Alias not found")
    return LinkMeta(
        alias=link.alias,
        target_url=link.target_url,
        created_at=link.created_at,
        access_count=link.access_count,
        last_accessed=link.last_accessed,
        expires_at=link.expires_at,
    )

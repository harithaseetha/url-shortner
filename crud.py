import string
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from . import models
from datetime import datetime

ALPHABET = string.digits + string.ascii_letters


class AliasConflictError(Exception):
    """Raised when a requested alias is already in use."""


def encode_base62(num: int) -> str:
    """Convert a decimal number to base62 string encoding.
    
    Uses digits 0-9 followed by lowercase and uppercase letters (62 chars total).
    Example: id=67 encodes to '15'.
    """
    if num == 0:
        return ALPHABET[0]
    arr = []
    base = len(ALPHABET)
    while num:
        num, rem = divmod(num, base)
        arr.append(ALPHABET[rem])
    arr.reverse()
    return ''.join(arr)


def create_link(session: Session, target_url: str, custom_alias: str = None, expires_at=None):
    # If custom alias provided, attempt to insert and let DB enforce uniqueness
    if custom_alias:
        link = models.Link(alias=custom_alias, target_url=target_url, expires_at=expires_at)
        session.add(link)
        try:
            session.commit()
            session.refresh(link)
            return link
        except IntegrityError:
            session.rollback()
            raise AliasConflictError(f"Alias '{custom_alias}' already exists")

    # Otherwise create row to obtain id, then generate alias from id
    link = models.Link(target_url=target_url, expires_at=expires_at)
    session.add(link)
    session.flush()  # assigns id from database AUTOINCREMENT
    generated = encode_base62(link.id)
    link.alias = generated
    try:
        session.commit()
        session.refresh(link)
        return link
    except IntegrityError:
        session.rollback()
        # Very unlikely: base62(id) should be unique by design.
        # Could indicate database corruption or a system-level issue.
        raise AliasConflictError(
            "Failed to generate a unique alias. This is a rare system error. "
            "Please retry or contact support if the issue persists."
        )


def get_link_by_alias(session: Session, alias: str):
    return session.query(models.Link).filter(models.Link.alias == alias, models.Link.is_active == True).first()


def increment_access(session: Session, link_id: int):
    """Atomically increment the access count and update last_accessed timestamp.
    """
    update_stmt = (
        models.Link.__table__.update()
        .where(models.Link.id == link_id)
        .values(
            access_count=models.Link.access_count + 1,
            last_accessed=datetime.utcnow()
        )
    )
    
    # Execute the statement and commit the transaction
    session.execute(update_stmt)
    session.commit()

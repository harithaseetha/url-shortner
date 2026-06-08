
from pydantic import BaseModel, HttpUrl, constr
from typing import Optional
from datetime import datetime


class ShortenRequest(BaseModel):
	target_url: HttpUrl
	# Use `pattern` for Pydantic v2 compatibility (matches regex semantics)
	custom_alias: Optional[constr(pattern=r'^[A-Za-z0-9]{1,64}$')] = None
	expires_at: Optional[datetime] = None


class ShortenResponse(BaseModel):
	alias: str
	target_url: HttpUrl
	created_at: datetime
	access_count: int
	expires_at: Optional[datetime] = None

	class Config:
		orm_mode = True


class LinkMeta(BaseModel):
	alias: str
	target_url: HttpUrl
	created_at: datetime
	access_count: int
	last_accessed: Optional[datetime] = None
	expires_at: Optional[datetime] = None

	class Config:
		orm_mode = True


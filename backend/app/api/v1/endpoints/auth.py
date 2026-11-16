from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from jose import jwt

from app.core.database import get_db
from app.api.deps import get_current_user
from app.core.security import extract_user_id
from app.crud import get_profile_by_supabase_user_id, create_profile
from app.models.base import Profile
from app.schemas import ProfileOut, ProfileUpdate

router = APIRouter()


@router.get("/me", response_model=ProfileOut)
def me(current_user: Profile = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=ProfileOut)
def update_profile(
    profile_in: ProfileUpdate,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_data = profile_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(current_user, k, v)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/profile", response_model=ProfileOut)
async def ensure_profile(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Get the caller's profile, creating it from the Supabase JWT on first use."""
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1]
    user_id_str = await extract_user_id(token)
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = UUID(user_id_str)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    profile = get_profile_by_supabase_user_id(db, user_id)
    if profile is not None:
        return profile

    claims = jwt.get_unverified_claims(token)
    email = claims.get("email") or ""
    user_metadata = claims.get("user_metadata") or {}
    full_name = user_metadata.get("full_name") or (email.split("@")[0] if email else "User")
    preferred = user_metadata.get("preferred_language")
    if preferred not in {"en", "hi", "kn", "ta"}:
        preferred = "en"
    profile = create_profile(db, user_id, full_name, email, language=preferred)
    return profile


@router.post("/logout")
def logout():
    # Stateless JWT; client discards token. Return success.
    return {"detail": "Logged out"}

from typing import List  # Changed from ast to typing
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException
from sqlmodel import Session, select
from app.db import get_session, UPLOAD_DIR
from app.models import CoinRequest, User, Notification
from app.schemas import CoinRequestCreate, CoinRequestOut
from app.auth import get_current_user, get_admin_user
from app.utils import save_upload_uploadfile
from datetime import datetime

router = APIRouter(prefix="/coins", tags=["coins"])

@router.post("/request")
def request_coins(
    amount: int = Form(...),
    transaction_image: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    image_path = save_upload_uploadfile(transaction_image, UPLOAD_DIR, prefix="coin_transaction_")
    req = CoinRequest(
        user_id=current_user.id,
        amount=amount,
        image_path=image_path
    )
    session.add(req)
    session.commit()
    session.refresh(req)
    # Notify admins
    admins = session.exec(select(User).where(User.is_admin == True)).all()
    for admin in admins:
        note = Notification(
            user_id=admin.id,
            title="New Coin Request",
            message=f"User {current_user.username} requested {amount} coins with transaction image. Request ID: {req.id}"
        )
        session.add(note)
    session.commit()
    return {"request_id": req.id, "status": "pending"}

@router.get("/requests", response_model=List[CoinRequestOut]) 
def list_coin_requests(
    session: Session = Depends(get_session), 
    current_user=Depends(get_current_user)  # Get any logged-in user
):
    if current_user.is_admin:
        # Admin sees all requests
        query = select(CoinRequest)
    else:
        # Regular user sees only their own requests
        query = select(CoinRequest).where(CoinRequest.user_id == current_user.id)
    
    return session.exec(query).all()


@router.post("/requests/{req_id}/approve")
def approve_coin_request(req_id: int, session: Session = Depends(get_session), admin=Depends(get_admin_user)):
    req = session.get(CoinRequest, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.reviewed:
        raise HTTPException(status_code=400, detail="Already reviewed")
    req.reviewed = True
    req.approved = True
    req.reviewed_at = datetime.utcnow()
    req.reviewer_id = admin.id
    user = session.get(User, req.user_id)
    user.coins += req.amount
    session.add(req)
    session.add(user)
    # Notify user
    note = Notification(
        user_id=user.id,
        title="Coin Request Approved",
        message=f"Your request for {req.amount} coins has been approved. New balance: {user.coins}"
    )
    session.add(note)
    session.commit()
    return {"ok": True}

@router.post("/requests/{req_id}/reject")
def reject_coin_request(req_id: int, session: Session = Depends(get_session), admin=Depends(get_admin_user)):
    req = session.get(CoinRequest, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.reviewed:
        raise HTTPException(status_code=400, detail="Already reviewed")
    req.reviewed = True
    req.approved = False
    req.reviewed_at = datetime.utcnow()
    req.reviewer_id = admin.id
    session.add(req)
    # Notify user
    note = Notification(
        user_id=req.user_id,
        title="Coin Request Rejected",
        message=f"Your request for {req.amount} coins has been rejected."
    )
    session.add(note)
    session.commit()
    return {"ok": True}
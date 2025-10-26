from typing import List
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, Request
from sqlmodel import Session, select
from datetime import datetime
from app.db import get_session, UPLOAD_DIR
from app.models import CoinRequest, User, Notification
from app.schemas import CoinRequestOut
from app.auth import get_current_user, get_admin_user
from app.utils import save_upload_uploadfile

router = APIRouter(prefix="/coins", tags=["coins"])



@router.post("/request")
def request_coins(
    request: Request,
    amount: int = Form(...),
    transaction_image: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        # Debug prints
        token = request.headers.get("authorization", "No token found")
        print(f"💡 Sending coin request with token: {token}")
        print(f"💡 User ID: {current_user.id} | Username: {current_user.username}")

        # Check user validity
        if not current_user or not current_user.id:
            raise HTTPException(status_code=400, detail="Invalid user")

        # Save uploaded image safely
        try:
            image_filename = save_upload_uploadfile(transaction_image, UPLOAD_DIR)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

        # Normalize image path
        image_path = image_filename.replace("\\", "/")
        if not image_path.startswith("uploads/"):
            image_path = f"uploads/{image_path.split('uploads/')[-1]}"

        # Save coin request in DB
        req = CoinRequest(
            user_id=current_user.id,
            amount=amount,
            image_path=image_path,
        )
        session.add(req)
        session.commit()
        session.refresh(req)

        # Notify all admins
        admins = session.exec(select(User).where(User.is_admin == True)).all()
        for admin in admins:
            if not admin.id:
                continue
            note = Notification(
                user_id=admin.id,
                title="New Coin Request",
                message=f"User {current_user.username} requested {amount} coins. Request ID: {req.id}",
            )
            session.add(note)
        session.commit()

        # Return full image URL
        image_url = str(request.base_url) + image_path

        return {
            "request_id": req.id,
            "status": "pending",
            "image_url": image_url,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/requests")
def list_coin_requests(
    request: Request,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """List all coin requests (admins see all, users see their own)."""
    if current_user.is_admin:
        query = select(CoinRequest)
    else:
        query = select(CoinRequest).where(CoinRequest.user_id == current_user.id)

    results = session.exec(query).all()
    output = []

    for r in results:
        image_path = r.image_path.replace("\\", "/").replace("./", "")
        if image_path.startswith("uploads/uploads/"):
            image_path = image_path.replace("uploads/uploads/", "uploads/")
        elif not image_path.startswith("uploads/"):
            image_path = f"uploads/{image_path}"

        output.append({
            "id": r.id,
            "user_id": r.user_id,
            "amount": r.amount,
            "image_url": str(request.base_url) + image_path,
            "created_at": r.created_at,
            "reviewed": r.reviewed,
            "approved": r.approved,
        })

    return output

@router.get("/requests/{user_id}", response_model=List[CoinRequestOut])
def get_user_coin_requests(
    user_id: int,
    session: Session = Depends(get_session),
):
    requests = session.exec(
        select(CoinRequest).where(CoinRequest.user_id == user_id)
    ).all()
    return requests


@router.post("/requests/{req_id}/approve")
def approve_coin_request(
    req_id: int,
    session: Session = Depends(get_session),
    admin=Depends(get_admin_user),
):
    """Admin approves a coin request."""
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
    session.add_all([req, user])

    note = Notification(
        user_id=user.id,
        title="Coin Request Approved",
        message=f"Your request for {req.amount} coins has been approved. New balance: {user.coins}",
    )
    session.add(note)
    session.commit()

    return {"ok": True, "message": "Request approved"}


@router.post("/requests/{req_id}/reject")
def reject_coin_request(
    req_id: int,
    session: Session = Depends(get_session),
    admin=Depends(get_admin_user),
):
    """Admin rejects a coin request."""
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

    note = Notification(
        user_id=req.user_id,
        title="Coin Request Rejected",
        message=f"Your request for {req.amount} coins has been rejected.",
    )
    session.add(note)
    session.commit()

    return {"ok": True, "message": "Request rejected"}

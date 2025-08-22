from dotenv import load_dotenv
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
import stripe
import os

from utils.db.connect_to_my_sql import db

# Load environment variables
load_dotenv()

BASE_URL = os.getenv("BASE_URL")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Initialize router
payment_router = APIRouter()

# Route to create Stripe checkout session
@payment_router.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    user_email = request.query_params.get("email")
    user = db["users"].find_one({"email": user_email})

    if not user:
        return JSONResponse(status_code=404, content={"detail": "User not found"})

    # Create Stripe Checkout Session with customer_email
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "Premium Membership"
                },
                "unit_amount": 500,  # $5.00
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{BASE_URL}/payment-success?email={user_email}",
        cancel_url=f"{BASE_URL}/payment-cancel",
        customer_email=user_email,  # Required for webhook-based identification
    )

    return {"checkout_url": session.url}

# Stripe webhook to handle successful payments
@payment_router.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return JSONResponse(status_code=400, content={"detail": "Invalid webhook signature"})

    # Handle checkout session success
    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]
        customer_email = session_data.get("customer_email")

        if customer_email:
            user = db["users"].find_one({"email": customer_email})
            if user:
                db["users"].update_one({"email": customer_email}, {"$set": {"is_premium": True}})

    return JSONResponse(status_code=200, content={"status": "success"})

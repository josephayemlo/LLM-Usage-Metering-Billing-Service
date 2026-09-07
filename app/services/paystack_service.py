import os

import requests
from dotenv import load_dotenv

load_dotenv()

PAYSTACK_INITIALIZE_URL = os.getenv("PAYSTACK_INITIALIZE_URL")
PAYSTACK_VERIFY_URL = os.getenv("PAYSTACK_VERIFY_URL")

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")


def _headers():
    return {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def initialize_transaction(
    email: str,
    amount: int,
    plan_code: str | None = None,
    reference: str | None = None,
):
    payload = {
        "email": email,
        "amount": amount,
    }

    if plan_code:
        payload["plan"] = plan_code

    if reference:
        payload["reference"] = reference

    response = requests.post(
        PAYSTACK_INITIALIZE_URL,
        headers=_headers(),
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("status"):
        raise ValueError(
            data.get(
                "message",
                "Paystack transaction initialization failed",
            )
        )

    return data["data"]


def verify_transaction(reference: str):
    response = requests.get(
        f"{PAYSTACK_VERIFY_URL}{reference}",
        headers=_headers(),
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("status"):
        raise ValueError(
            data.get(
                "message",
                "Paystack transaction verification failed",
            )
        )

    return data["data"]
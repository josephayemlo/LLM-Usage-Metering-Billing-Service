from sqlalchemy import select

from app.database import SessionLocal
from app.models.plan import Plan


def seed_plans():
    with SessionLocal() as session:
        existing_plans = session.execute(select(Plan)).scalars().all()

        if existing_plans:
            print("Plans already exist. Nothing to seed.")
            return

        free_plan = Plan(
            name="Free",
            description="Free plan for basic usage",
            api_call_limit=1_000,
            ai_token_limit=100_000,
            price_kobo=0,
            billing_interval="monthly",
            paystack_plan_code=None,
        )

        pro_plan = Plan(
            name="Pro",
            description="Pro plan for higher usage limits",
            api_call_limit=10_000,
            ai_token_limit=1_000_000,
            price_kobo=500_000,
            billing_interval="monthly",
            paystack_plan_code=None,
        )

        session.add_all([free_plan, pro_plan])
        session.commit()

        print("Free and Pro plans seeded successfully.")


if __name__ == "__main__":
    seed_plans()
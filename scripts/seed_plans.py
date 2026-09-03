from sqlalchemy import select

from app.database import SessionLocal
from app.models.plan import Plan

# This script is responsible for seeding the database with initial plan data.
def seed_plans():
    with SessionLocal() as session:
        existing_plans = session.execute(select(Plan)).scalars().all()

        if existing_plans:
            print("Plans already exist. Nothing to seed.")
            return

        free_plan = Plan(
            name="Free",
            api_call_limit=1_000,
            ai_token_limit=100_000,
        )

        pro_plan = Plan(
            name="Pro",
            api_call_limit=10_000,
            ai_token_limit=1_000_000,
        )

        session.add_all([free_plan, pro_plan])
        session.commit()

        print("Free and Pro plans seeded successfully.")


#this line allows the script to be run directly, 
# which will execute the seed_plans function to populate 
# the database with initial plan data if it doesn't already exist.
# it also prevents the function from being executed if the script is imported as a module in another script.
if __name__ == "__main__":
    seed_plans()
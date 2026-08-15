"""Seed script for ServiceHub AI.

Populates the database with realistic sample data for local testing:
- 1 admin account
- Multiple customers
- Multiple providers (each with profile, schedule, portfolio)
- Categories (Cleaning, Plumbing, Electrical, etc.)
- Services under each provider/category
- Bookings (various statuses)
- Reviews
- Favorite providers

Run from the backend directory:

    # Run inside the Docker backend container:
    docker compose exec backend python seed.py

    # Or run locally (with a .env pointing at your DB):
    python seed.py

All created accounts use the password "Password123" so you can log in and test.
"""

import asyncio
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.common.constants import (
    BookingStatus,
    DayOfWeek,
    PriceUnit,
    UserRole,
)
from app.database.base import Base
from app.database.database import AsyncSessionLocal as async_session_factory, engine
from app.models.booking import Booking
from app.models.category import Category
from app.models.provider import Provider
from app.models.provider_portfolio import ProviderPortfolioImage
from app.models.review import Review
from app.models.schedule import ProviderSchedule
from app.models.service import Service
from app.models.user import User
from app.models.user_profile import FavoriteService, UserProfile

# All test accounts share this password.
SEED_PASSWORD = "Password123"
HASHED_PASSWORD = hash_password(SEED_PASSWORD)

# Cities available for random distribution.
CITIES = [
    "Karachi",
    "Lahore",
    "Islamabad",
    "Rawalpindi",
    "Faisalabad",
    "Multan",
    "Peshawar",
    "Quetta",
]

CATEGORIES = [
    {
        "name": "Cleaning",
        "slug": "cleaning",
        "description": "Home and office cleaning services.",
        "icon": "🧹",
    },
    {
        "name": "Plumbing",
        "slug": "plumbing",
        "description": "Pipe repairs, installations and maintenance.",
        "icon": "🔧",
    },
    {
        "name": "Electrical",
        "slug": "electrical",
        "description": "Wiring, fixtures and electrical repairs.",
        "icon": "⚡",
    },
    {
        "name": "Painting",
        "slug": "painting",
        "description": "Interior and exterior painting services.",
        "icon": "🎨",
    },
    {
        "name": "Appliance Repair",
        "slug": "appliance-repair",
        "description": "Repair of AC, fridge, washing machine and more.",
        "icon": "🛠️",
    },
    {
        "name": "Tutoring",
        "slug": "tutoring",
        "description": "Academic and skills tutoring.",
        "icon": "📚",
    },
    {
        "name": "Beauty & Spa",
        "slug": "beauty-spa",
        "description": "Salon and spa services at home.",
        "icon": "💆",
    },
    {
        "name": "IT & Tech",
        "slug": "it-tech",
        "description": "Computer, network and tech support.",
        "icon": "💻",
    },
]

# Provider business definitions. Each gets a user, provider profile, schedule
# and a couple of services.
PROVIDERS = [
    {
        "email": "ahmed.cleaning@test.com",
        "full_name": "Ahmed Khan",
        "business_name": "Sparkle Clean Co.",
        "category_text": "Cleaning",
        "city": "Karachi",
        "hourly_rate": 800,
        "rating": 4.8,
        "is_verified": True,
        "description": "Professional home and office cleaning with eco-friendly products.",
        "services": [
            {
                "title": "Deep Home Cleaning",
                "price": 3000,
                "price_unit": PriceUnit.PER_VISIT,
                "duration_minutes": 240,
                "description": "Top-to-bottom deep cleaning of your entire home.",
                "is_featured": True,
            },
            {
                "title": "Office Cleaning",
                "price": 1500,
                "price_unit": PriceUnit.PER_HOUR,
                "duration_minutes": 120,
                "description": "Regular office and workspace cleaning.",
                "is_featured": False,
            },
            {
                "title": "Sofa & Carpet Shampoo",
                "price": 1200,
                "price_unit": PriceUnit.PER_VISIT,
                "duration_minutes": 90,
                "description": "Steam cleaning for sofas and carpets.",
                "is_featured": False,
            },
        ],
    },
    {
        "email": "ali.plumbing@test.com",
        "full_name": "Ali Raza",
        "business_name": "Rapid Plumbers",
        "category_text": "Plumbing",
        "city": "Lahore",
        "hourly_rate": 1000,
        "rating": 4.6,
        "is_verified": True,
        "description": "24/7 emergency plumbing and leak repairs.",
        "services": [
            {
                "title": "Leak Repair",
                "price": 1500,
                "price_unit": PriceUnit.PER_VISIT,
                "duration_minutes": 60,
                "description": "Fix leaking pipes and faucets.",
                "is_featured": True,
            },
            {
                "title": "Water Heater Installation",
                "price": 3500,
                "price_unit": PriceUnit.FIXED,
                "duration_minutes": 180,
                "description": "Install or replace geyser/water heater.",
                "is_featured": False,
            },
        ],
    },
    {
        "email": "usman.electric@test.com",
        "full_name": "Usman Tariq",
        "business_name": "Bright Spark Electricals",
        "category_text": "Electrical",
        "city": "Islamabad",
        "hourly_rate": 1100,
        "rating": 4.9,
        "is_verified": True,
        "description": "Certified electrician for homes and businesses.",
        "services": [
            {
                "title": "Wiring Repair",
                "price": 2000,
                "price_unit": PriceUnit.PER_VISIT,
                "duration_minutes": 120,
                "description": "Faulty wiring diagnosis and repair.",
                "is_featured": True,
            },
            {
                "title": "Fan & Light Installation",
                "price": 500,
                "price_unit": PriceUnit.PER_VISIT,
                "duration_minutes": 45,
                "description": "Install ceiling fans and light fixtures.",
                "is_featured": False,
            },
        ],
    },
    {
        "email": "bilal.painting@test.com",
        "full_name": "Bilal Hussain",
        "business_name": "ColorPro Painters",
        "category_text": "Painting",
        "city": "Rawalpindi",
        "hourly_rate": 900,
        "rating": 4.4,
        "is_verified": False,
        "description": "Interior/exterior painting and wall textures.",
        "services": [
            {
                "title": "Room Painting",
                "price": 12000,
                "price_unit": PriceUnit.FIXED,
                "duration_minutes": 480,
                "description": "Paint a standard sized room.",
                "is_featured": False,
            },
        ],
    },
    {
        "email": "zain.appliance@test.com",
        "full_name": "Zain Malik",
        "business_name": "CoolFix Appliances",
        "category_text": "Appliance Repair",
        "city": "Faisalabad",
        "hourly_rate": 950,
        "rating": 4.5,
        "is_verified": True,
        "description": "AC, fridge and washing machine repair.",
        "services": [
            {
                "title": "AC Servicing",
                "price": 1800,
                "price_unit": PriceUnit.PER_VISIT,
                "duration_minutes": 90,
                "description": "Full AC cleaning and gas top-up.",
                "is_featured": True,
            },
            {
                "title": "Washing Machine Repair",
                "price": 1600,
                "price_unit": PriceUnit.PER_VISIT,
                "duration_minutes": 75,
                "description": "Diagnose and fix washing machine faults.",
                "is_featured": False,
            },
        ],
    },
    {
        "email": "sara.tutor@test.com",
        "full_name": "Sara Iqbal",
        "business_name": "Bright Minds Tutoring",
        "category_text": "Tutoring",
        "city": "Karachi",
        "hourly_rate": 1500,
        "rating": 5.0,
        "is_verified": True,
        "description": "Maths, Physics and English tutoring for all grades.",
        "services": [
            {
                "title": "O-Level Maths Tutoring",
                "price": 2000,
                "price_unit": PriceUnit.PER_HOUR,
                "duration_minutes": 60,
                "description": "One-on-one O-Level mathematics sessions.",
                "is_featured": True,
            },
            {
                "title": "IELTS Prep",
                "price": 2500,
                "price_unit": PriceUnit.PER_HOUR,
                "duration_minutes": 60,
                "description": "IELTS speaking and writing preparation.",
                "is_featured": False,
            },
        ],
    },
    {
        "email": "ayesha.beauty@test.com",
        "full_name": "Ayesha Nadeem",
        "business_name": "Glow Beauty Studio",
        "category_text": "Beauty & Spa",
        "city": "Lahore",
        "hourly_rate": 1800,
        "rating": 4.7,
        "is_verified": True,
        "description": "Bridal makeup and home spa treatments.",
        "services": [
            {
                "title": "Bridal Makeup",
                "price": 8000,
                "price_unit": PriceUnit.FIXED,
                "duration_minutes": 180,
                "description": "Complete bridal makeup and styling.",
                "is_featured": True,
            },
            {
                "title": "Facial & Massage",
                "price": 2500,
                "price_unit": PriceUnit.PER_VISIT,
                "duration_minutes": 90,
                "description": "Relaxing facial and head massage.",
                "is_featured": False,
            },
        ],
    },
    {
        "email": "hamza.it@test.com",
        "full_name": "Hamza Sheikh",
        "business_name": "TechHelp IT Solutions",
        "category_text": "IT & Tech",
        "city": "Islamabad",
        "hourly_rate": 1300,
        "rating": 4.6,
        "is_verified": True,
        "description": "PC repair, networking and data recovery.",
        "services": [
            {
                "title": "PC Repair & Format",
                "price": 2000,
                "price_unit": PriceUnit.PER_VISIT,
                "duration_minutes": 120,
                "description": "Diagnose, format and optimize your PC.",
                "is_featured": True,
            },
            {
                "title": "Home Network Setup",
                "price": 1500,
                "price_unit": PriceUnit.PER_VISIT,
                "duration_minutes": 60,
                "description": "WiFi router and network configuration.",
                "is_featured": False,
            },
        ],
    },
]

CUSTOMERS = [
    {"email": "customer1@test.com", "full_name": "Fatima Zaidi"},
    {"email": "customer2@test.com", "full_name": "Imran Ali"},
    {"email": "customer3@test.com", "full_name": "Kiran Shah"},
    {"email": "customer4@test.com", "full_name": "Omar Farooq"},
    {"email": "customer5@test.com", "full_name": "Mahnoor Khan"},
]


def _make_schedule() -> list[ProviderSchedule]:
    """Create a default Mon-Sat 9-6 schedule for a provider."""
    sched = []
    for day in DayOfWeek:
        sched.append(
            ProviderSchedule(
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(18, 0),
                is_available=day != DayOfWeek.SUNDAY,
            )
        )
    return sched


async def _get_or_create(session: AsyncSession, model, defaults=None, **filters):
    """Fetch a row by filters, or create it."""
    result = await session.execute(select(model).filter_by(**filters))
    instance = result.scalar_one_or_none()
    if instance:
        return instance, False
    params = {**filters, **(defaults or {})}
    instance = model(**params)
    session.add(instance)
    await session.flush()
    return instance, True


async def seed() -> None:
    """Populate the database with sample data."""
    async with async_session_factory() as session:
        # --- Admin -------------------------------------------------------------
        admin, _ = await _get_or_create(
            session,
            User,
            defaults={
                "full_name": "Site Admin",
                "hashed_password": HASHED_PASSWORD,
                "role": UserRole.ADMIN,
                "is_active": True,
                "is_verified": True,
            },
            email="admin@test.com",
        )

        # --- Categories --------------------------------------------------------
        category_map = {}
        for cat in CATEGORIES:
            obj, _ = await _get_or_create(
                session,
                Category,
                defaults={
                    "name": cat["name"],
                    "description": cat["description"],
                    "icon": cat["icon"],
                    "is_active": True,
                },
                slug=cat["slug"],
            )
            category_map[cat["slug"]] = obj

        # --- Customers ----------------------------------------------------------
        customer_users = []
        for c in CUSTOMERS:
            user, created = await _get_or_create(
                session,
                User,
                defaults={
                    "full_name": c["full_name"],
                    "hashed_password": HASHED_PASSWORD,
                    "role": UserRole.CUSTOMER,
                    "is_active": True,
                    "is_verified": True,
                },
                email=c["email"],
            )
            customer_users.append(user)
            if created:
                session.add(
                    UserProfile(
                        user_id=user.id,
                        phone_number=f"+92{300 + user.id}000000",
                        bio=f"Test customer {c['full_name']}.",
                    )
                )

        # --- Providers + schedules + services ---------------------------------
        provider_objs = []
        for p in PROVIDERS:
            user, _ = await _get_or_create(
                session,
                User,
                defaults={
                    "full_name": p["full_name"],
                    "hashed_password": HASHED_PASSWORD,
                    "role": UserRole.PROVIDER,
                    "is_active": True,
                    "is_verified": True,
                },
                email=p["email"],
            )
            provider, _ = await _get_or_create(
                session,
                Provider,
                defaults={
                    "business_name": p["business_name"],
                    "description": p["description"],
                    "is_verified": p["is_verified"],
                    "rating": p["rating"],
                    "city": p["city"],
                    "address": f"Street 5, {p['city']}",
                    "category": p["category_text"],
                    "hourly_rate": p["hourly_rate"],
                },
                user_id=user.id,
            )
            provider_objs.append(provider)

            # Schedule (idempotent: only add if none exist).
            sched_result = await session.execute(
                select(ProviderSchedule).filter_by(provider_id=provider.id)
            )
            if not sched_result.scalars().first():
                for slot in _make_schedule():
                    slot.provider_id = provider.id
                    session.add(slot)

            # Portfolio image.
            await _get_or_create(
                session,
                ProviderPortfolioImage,
                defaults={"caption": f"{p['business_name']} showcase"},
                provider_id=provider.id,
                image_url=f"https://picsum.photos/seed/{provider.id}/600/400",
            )

            # Services.
            cat = category_map[p["slug"]] if False else category_map.get(
                next(
                    (c["slug"] for c in CATEGORIES if c["name"] == p["category_text"]),
                    None,
                )
            )
            for i, svc in enumerate(p["services"]):
                service, _ = await _get_or_create(
                    session,
                    Service,
                    defaults={
                        "provider_id": provider.id,
                        "title": svc["title"],
                        "description": svc["description"],
                        "price": svc["price"],
                        "price_unit": svc["price_unit"],
                        "duration_minutes": svc["duration_minutes"],
                        "is_active": True,
                        "is_featured": svc.get("is_featured", False),
                        "images": [f"https://picsum.photos/seed/{provider.id}-{i}/600/400"],
                    },
                    category_id=cat.id,
                    slug=f"{cat.slug}-{provider.id}-{i + 1}",
                )

        # --- Bookings -----------------------------------------------------------
        # Create a mix of statuses across customers/providers/services.
        services_result = await session.execute(select(Service))
        all_services = services_result.scalars().all()
        if all_services:
            booking_specs = [
                BookingStatus.COMPLETED,
                BookingStatus.ACCEPTED,
                BookingStatus.PENDING,
                BookingStatus.COMPLETED,
                BookingStatus.REJECTED,
                BookingStatus.CANCELLED,
                BookingStatus.ACCEPTED,
                BookingStatus.PENDING,
            ]
            for idx, status in enumerate(booking_specs):
                svc = all_services[idx % len(all_services)]
                customer = customer_users[idx % len(customer_users)]
                provider = next(
                    (pr for pr in provider_objs if pr.id == svc.provider_id),
                    provider_objs[0],
                )
                days_out = idx - 3
                bdate = date.today() + timedelta(days=days_out)
                total = (
                    svc.price
                    if svc.price_unit != PriceUnit.PER_HOUR
                    else svc.price * (svc.duration_minutes // 60 or 1)
                )
                booking, created = await _get_or_create(
                    session,
                    Booking,
                    defaults={
                        "service_id": svc.id,
                        "customer_id": customer.id,
                        "provider_id": provider.id,
                        "scheduled_date": bdate,
                        "scheduled_start": time(10, 0),
                        "scheduled_end": time(
                            10 + (svc.duration_minutes // 60 or 1), 0
                        ),
                        "status": status,
                        "service_title": svc.title,
                        "total_price": total,
                        "location": f"{customer.full_name}'s home, {provider.city}",

                        "customer_notes": "Please arrive on time.",
                    },
                    reference_code=f"SH{1000 + idx}",
                )
                if status == BookingStatus.COMPLETED and created:
                    booking.completed_at = datetime.now(timezone.utc)

        # --- Reviews ------------------------------------------------------------
        completed = await session.execute(
            select(Booking).filter_by(status=BookingStatus.COMPLETED)
        )
        for b in completed.scalars().all():
            await _get_or_create(
                session,
                Review,
                defaults={
                    "rating": 5,
                    "comment": "Great service, highly recommended!",
                    "created_at": datetime.now(timezone.utc),
                },
                booking_id=b.id,
                customer_id=b.customer_id,
            )

        # --- Favorites ----------------------------------------------------------
        service_result = await session.execute(select(Service))
        service_objs = service_result.scalars().all()

        for c in customer_users[:3]:
            fav_service = service_objs[customer_users.index(c) % len(service_objs)]
            await _get_or_create(
                session,
                FavoriteService,
                defaults={},
                user_id=c.id,
                service_id=fav_service.id,
            )

        await session.commit()

    print("Seed data created successfully.")
    print("\n--- Login credentials (password for all: %s) ---" % SEED_PASSWORD)
    print("Admin:    admin@test.com")
    for p in PROVIDERS:
        print(f"Provider: {p['email']}")
    for c in CUSTOMERS:
        print(f"Customer: {c['email']}")


async def clear() -> None:
    """Drop all data (useful for re-seeding)."""
    async with engine.begin() as conn:
        # Reverse order to respect FKs.
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


async def main() -> None:
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        await clear()
        print("Database cleared.")
    await seed()


if __name__ == "__main__":
    asyncio.run(main())

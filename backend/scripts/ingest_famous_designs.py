import asyncio
import sys
import os
import datetime

# Add parent directory to path so the script can find the 'app' folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select
from app.db.models import FamousDesign
from app.db.session import AsyncSessionLocal 

FAMOUS_DESIGNS = [
    {
        "system_name": "netflix",
        "title": "Netflix Video Streaming Architecture",
        "diagram_json": {"nodes": ["CDN", "Open Connect", "Zuul Gateway"]},
        "canonical_json": {"sections": ["Video Processing", "Recommendation Engine"]},
        "key_insights": ["Uses AWS S3 for raw storage", "Open Connect for last-mile CDN"],
        "sources": ["netflixtechblog.com"]
    },
    {
        "system_name": "twitter",
        "title": "Twitter Timeline Architecture",
        "diagram_json": {"nodes": ["Fanout Service", "Redis", "Manhattan DB"]},
        "canonical_json": {"sections": ["Push vs Pull", "Graph Services"]},
        "key_insights": ["Push model for normal users", "Pull model for celebrities"],
        "sources": ["blog.twitter.com/engineering"]
    }
]

async def seed():
    async with AsyncSessionLocal() as db:
        try:
            for design_data in FAMOUS_DESIGNS:
                # Check if it already exists to prevent duplicates
                result = await db.execute(
                    select(FamousDesign).where(FamousDesign.system_name == design_data["system_name"])
                )
                exists = result.scalar_one_or_none()
                
                if not exists:
                    print(f"➕ Adding {design_data['system_name']}...")
                    
                    # Create the object
                    design = FamousDesign(**design_data)
                    
                    # FIX: Explicitly set last_updated to avoid NotNullViolation
                    design.last_updated = datetime.datetime.now(datetime.timezone.utc)
                    
                    db.add(design)
                else:
                    print(f"⏭️  {design_data['system_name']} already exists, skipping.")
                    
            await db.commit()
            print("\n✅ Famous designs seeded successfully to the database!")
        except Exception as e:
            await db.rollback()
            print(f"❌ Error seeding database: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(seed())
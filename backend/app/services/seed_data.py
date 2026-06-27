"""
Famous Systems Seed Data
========================
Contains 27 famous system designs for reference.
Populates the database on startup (idempotent).
"""
import logging
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FamousSystem

logger = logging.getLogger(__name__)


# ─── Famous Systems Data (27 Systems) ─────────────────────────────────────────

FAMOUS_SYSTEMS_DATA: List[Dict[str, Any]] = [
    # ═══════════════════════════════════════════════════════════════════════
    # SOCIAL MEDIA
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Twitter",
        "slug": "twitter",
        "description": "Real-time microblogging platform with timeline feeds, trending topics, and follower graphs",
        "design_type": "HLD",
        "key_components": [
            "Timeline Service", "Fan-out Service", "Tweet Service",
            "Graph Service", "Search Service", "Trending Service"
        ],
        "architecture_summary": "Read-heavy system using fan-out-on-write for regular users and pull-based (home timeline) for celebrities with millions of followers. Uses Redis for timeline caching.",
        "tags": ["social", "feed", "real-time", "read-heavy", "fan-out", "timeline"],
        "reference_url": "https://systeminterview.com/design-twitter.php",
    },
    {
        "name": "Instagram",
        "slug": "instagram",
        "description": "Photo and video sharing platform with stories, reels, and social feeds",
        "design_type": "HLD",
        "key_components": [
            "Media Service", "Feed Service", "Story Service",
            "CDN", "Object Storage (S3)", "Notification Service"
        ],
        "architecture_summary": "Object storage with CDN for media delivery. Fan-out service precomputes feeds. Uses Cassandra for feeds and PostgreSQL for user data.",
        "tags": ["social", "media", "feed", "cdn", "object-storage", "stories"],
        "reference_url": "https://systeminterview.com/design-instagram.php",
    },
    {
        "name": "Facebook News Feed",
        "slug": "facebook-newsfeed",
        "description": "Personalized news feed aggregation for billions of users",
        "design_type": "HLD",
        "key_components": [
            "Feed Ranking Service", "Fan-out Service", "Post Service",
            "Edge Rank Algorithm", "Memcached", "TAO (Graph Cache)"
        ],
        "architecture_summary": "Hybrid fan-out approach: on-write for friends, on-read for celebrities. ML-based ranking with thousands of signals. Uses TAO for social graph caching.",
        "tags": ["social", "feed", "ml", "ranking", "fan-out", "graph"],
        "reference_url": "https://engineering.fb.com/",
    },
    {
        "name": "TikTok",
        "slug": "tiktok",
        "description": "Short-form video platform with AI-powered recommendation engine",
        "design_type": "HLD",
        "key_components": [
            "Video Upload Service", "Recommendation Engine", "Feed Service",
            "Transcoding Pipeline", "CDN", "Analytics Service"
        ],
        "architecture_summary": "Heavy ML-based recommendation system analyzing watch time, shares, and engagement. Video transcoding pipeline with multi-bitrate HLS delivery.",
        "tags": ["video", "ml", "recommendation", "feed", "transcoding", "short-form"],
        "reference_url": None,
    },
    {
        "name": "Pinterest",
        "slug": "pinterest",
        "description": "Visual discovery platform with pins, boards, and personalized feeds",
        "design_type": "HLD",
        "key_components": [
            "Pin Service", "Board Service", "Feed Service",
            "Smart Feed (ML)", "Image Processing", "Search Service"
        ],
        "architecture_summary": "Smart Feed uses ML to rank pins. Uses HBase for pin metadata and S3 for images. Heavy image processing for visual search.",
        "tags": ["social", "image", "feed", "ml", "visual-search", "discovery"],
        "reference_url": "https://medium.com/pinterest-engineering",
    },
    {
        "name": "LinkedIn",
        "slug": "linkedin",
        "description": "Professional networking platform with job postings and news feeds",
        "design_type": "HLD",
        "key_components": [
            "Feed Service", "Connection Service", "Job Service",
            "Search Service (Galene)", "Messaging Service", "LinkedIn Learning"
        ],
        "architecture_summary": "Galene search engine for professional data. Kafka-based event streaming. Hybrid feed with both fan-out and on-demand generation.",
        "tags": ["social", "professional", "feed", "search", "jobs", "networking"],
        "reference_url": "https://engineering.linkedin.com/",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # MESSAGING
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "WhatsApp",
        "slug": "whatsapp",
        "description": "Real-time messaging platform with end-to-end encryption for 2B+ users",
        "design_type": "HLD",
        "key_components": [
            "Chat Service", "Presence Service", "Message Queue",
            "Key Store", "Media Service", "Group Chat Service"
        ],
        "architecture_summary": "Originally Erlang/Ejabberd-based for massive concurrency. Uses Signal protocol for E2E encryption. Minimal server-side storage — messages deleted after delivery.",
        "tags": ["messaging", "real-time", "websocket", "encryption", "erlang", "e2e"],
        "reference_url": "https://systeminterview.com/design-whatsapp.php",
    },
    {
        "name": "Telegram",
        "slug": "telegram",
        "description": "Cloud-based messaging with channels, groups, and bots",
        "design_type": "HLD",
        "key_components": [
            "MTProto Protocol", "Chat Service", "Channel Service",
            "Bot API", "Media Service", "Distributed Storage"
        ],
        "architecture_summary": "Custom MTProto protocol for speed. Multi-datacenter architecture with eventual consistency. Large group support via broadcast.",
        "tags": ["messaging", "real-time", "channels", "bots", "mtproto", "distributed"],
        "reference_url": "https://core.telegram.org/",
    },
    {
        "name": "Slack",
        "slug": "slack",
        "description": "Team collaboration platform with channels, threads, and integrations",
        "design_type": "HLD",
        "key_components": [
            "Channel Service", "Message Service", "Search Service",
            "Integration Service", "Presence Service", "Notification Service"
        ],
        "architecture_summary": "WebSocket for real-time updates. Vitess for MySQL scaling. Heavy integration ecosystem via webhooks and APIs.",
        "tags": ["messaging", "collaboration", "real-time", "webhooks", "teams", "integrations"],
        "reference_url": "https://slack.engineering/",
    },
    {
        "name": "Discord",
        "slug": "discord",
        "description": "Voice, video, and text communication for communities and gamers",
        "design_type": "HLD",
        "key_components": [
            "Voice Service (WebRTC)", "Chat Service", "Guild Service",
            "Presence Service", "CDN", "Notification Service"
        ],
        "architecture_summary": "Built on Elixir for real-time messaging. Uses WebRTC for voice/video with selective forwarding units (SFU). ScyllaDB for message history.",
        "tags": ["messaging", "voice", "video", "webrtc", "real-time", "gaming"],
        "reference_url": "https://discord.com/blog/",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # VIDEO & STREAMING
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "YouTube",
        "slug": "youtube",
        "description": "World's largest video sharing platform with 500+ hours uploaded per minute",
        "design_type": "HLD",
        "key_components": [
            "Upload Service", "Transcoding Pipeline", "Streaming Service",
            "Recommendation Engine", "Search Service", "CDN"
        ],
        "architecture_summary": "Massive transcoding pipeline converting uploads to multiple formats/resolutions. Colossus file system. ML-based recommendations (deep neural networks).",
        "tags": ["video", "streaming", "cdn", "ml", "transcoding", "recommendation"],
        "reference_url": "https://systeminterview.com/design-youtube.php",
    },
    {
        "name": "Netflix",
        "slug": "netflix",
        "description": "Video streaming service with 200M+ subscribers and original content",
        "design_type": "HLD",
        "key_components": [
            "Open Connect CDN", "Streaming Service", "Recommendation Engine",
            "Zuul (API Gateway)", "Eureka (Service Discovery)", "Cassandra"
        ],
        "architecture_summary": "Microservices architecture on AWS. Custom Open Connect CDN for video delivery. Heavy ML recommendations. Chaos Engineering with Chaos Monkey.",
        "tags": ["video", "streaming", "cdn", "microservices", "ml", "aws"],
        "reference_url": "https://netflixtechblog.com/",
    },
    {
        "name": "Spotify",
        "slug": "spotify",
        "description": "Music streaming platform with personalized playlists and podcasts",
        "design_type": "HLD",
        "key_components": [
            "Streaming Service", "Playlist Service", "Discovery (ML)",
            "Search Service", "Cache Service", "Artist Platform"
        ],
        "architecture_summary": "Uses Merkle trees for playlist sync. Heavy ML for Discover Weekly. GCP-based infrastructure with Kubernetes.",
        "tags": ["audio", "streaming", "ml", "playlist", "discovery", "music"],
        "reference_url": "https://engineering.atspotify.com/",
    },
    {
        "name": "Twitch",
        "slug": "twitch",
        "description": "Live streaming platform for gaming and content creators",
        "design_type": "HLD",
        "key_components": [
            "Ingest Service", "Transcoding Service", "Edge Network",
            "Chat Service", "Monetization Service", "Analytics"
        ],
        "architecture_summary": "Low-latency live streaming with HLS and WebRTC options. Global edge network for delivery. Real-time chat with millions of concurrent viewers.",
        "tags": ["live-streaming", "video", "chat", "real-time", "gaming", "cdn"],
        "reference_url": None,
    },
    {
        "name": "Zoom",
        "slug": "zoom",
        "description": "Video conferencing platform for meetings and webinars",
        "design_type": "HLD",
        "key_components": [
            "Meeting Service", "Media Router (SFU/MCU)", "Signaling Service",
            "Recording Service", "Calendar Integration", "Chat Service"
        ],
        "architecture_summary": "Hybrid SFU/MCU architecture for optimal quality. Uses WebRTC with proprietary extensions. Multi-cloud strategy for resilience.",
        "tags": ["video", "conferencing", "webrtc", "real-time", "meetings", "sfu"],
        "reference_url": None,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # TRANSPORTATION & LOGISTICS
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Uber",
        "slug": "uber",
        "description": "Ride-sharing platform with real-time location tracking and matching",
        "design_type": "HLD",
        "key_components": [
            "Dispatch Service", "Location Service", "Matching Service",
            "Payment Service", "Surge Pricing Engine", "Maps Service"
        ],
        "architecture_summary": "Quadtree/GeoHash for location indexing. Real-time driver matching using Kafka streams. Dynamic surge pricing based on supply/demand.",
        "tags": ["location", "real-time", "matching", "geo", "dispatch", "pricing"],
        "reference_url": "https://systeminterview.com/design-uber.php",
    },
    {
        "name": "Airbnb",
        "slug": "airbnb",
        "description": "Vacation rental marketplace connecting hosts and guests globally",
        "design_type": "HLD",
        "key_components": [
            "Search Service", "Booking Service", "Payment Service",
            "Review Service", "Messaging Service", "Map Service"
        ],
        "architecture_summary": "Elasticsearch for location-based search. Complex booking state machine. Multi-currency payment processing with Stripe integration.",
        "tags": ["marketplace", "search", "booking", "payments", "geo", "reviews"],
        "reference_url": "https://medium.com/airbnb-engineering",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # E-COMMERCE & PAYMENTS
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Amazon",
        "slug": "amazon",
        "description": "World's largest e-commerce platform with AWS cloud services",
        "design_type": "HLD",
        "key_components": [
            "Product Catalog", "Shopping Cart", "Order Service",
            "Recommendation Engine", "Search (A9)", "Fulfillment Service"
        ],
        "architecture_summary": "Massive microservices architecture. DynamoDB for shopping cart. Two-phase commit for orders. Item-to-item collaborative filtering for recommendations.",
        "tags": ["ecommerce", "microservices", "recommendations", "search", "fulfillment", "scale"],
        "reference_url": None,
    },
    {
        "name": "Shopify",
        "slug": "shopify",
        "description": "E-commerce platform powering millions of online stores",
        "design_type": "HLD",
        "key_components": [
            "Storefront Service", "Checkout Service", "Payment Gateway",
            "Inventory Service", "App Ecosystem", "Analytics"
        ],
        "architecture_summary": "Multi-tenant architecture with sharded MySQL. Heavy use of Redis for caching. GraphQL API for storefronts.",
        "tags": ["ecommerce", "saas", "multi-tenant", "graphql", "payments", "inventory"],
        "reference_url": "https://shopify.engineering/",
    },
    {
        "name": "PayPal",
        "slug": "paypal",
        "description": "Digital payment platform handling billions in transactions",
        "design_type": "HLD",
        "key_components": [
            "Transaction Service", "Fraud Detection", "Wallet Service",
            "Settlement Service", "Risk Engine", "Compliance Service"
        ],
        "architecture_summary": "ACID-compliant transactions with strong consistency. ML-based fraud detection. Two-phase commit for cross-border payments.",
        "tags": ["payments", "transactions", "fraud", "fintech", "acid", "compliance"],
        "reference_url": None,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # SEARCH & DISCOVERY
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Google Search",
        "slug": "google-search",
        "description": "World's dominant search engine indexing trillions of web pages",
        "design_type": "HLD",
        "key_components": [
            "Crawler (Googlebot)", "Indexer", "Ranking (PageRank)",
            "Query Processor", "Knowledge Graph", "Ad Serving"
        ],
        "architecture_summary": "Distributed crawling with Googlebot. MapReduce for indexing. PageRank and BERT for ranking. Colossus distributed file system.",
        "tags": ["search", "crawling", "indexing", "ranking", "ml", "distributed"],
        "reference_url": None,
    },
    {
        "name": "Stack Overflow",
        "slug": "stackoverflow",
        "description": "Q&A platform for developers with voting and reputation system",
        "design_type": "HLD",
        "key_components": [
            "Q&A Service", "Voting Service", "Tag Service",
            "Search (Elasticsearch)", "Reputation Service", "Markdown Renderer"
        ],
        "architecture_summary": "Monolithic .NET application (not microservices!). SQL Server with heavy caching. Elasticsearch for full-text search.",
        "tags": ["qa", "voting", "reputation", "search", "monolith", "caching"],
        "reference_url": "https://nickcraver.com/blog/",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # DEVELOPER TOOLS
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "GitHub",
        "slug": "github",
        "description": "Code hosting platform with Git repositories, CI/CD, and collaboration",
        "design_type": "HLD",
        "key_components": [
            "Git Server", "Web Interface", "Actions (CI/CD)",
            "Issue Tracker", "Code Search", "Package Registry"
        ],
        "architecture_summary": "Git RPC for repository operations. Gitaly for Git storage. Elasticsearch for code search. Kubernetes for Actions runners.",
        "tags": ["git", "devtools", "cicd", "code-search", "collaboration", "repositories"],
        "reference_url": "https://github.blog/engineering/",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # STORAGE & FILES
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Google Drive",
        "slug": "google-drive",
        "description": "Cloud file storage with real-time sync across devices",
        "design_type": "HLD",
        "key_components": [
            "Block Service", "Metadata Service", "Sync Service",
            "Notification Service", "Deduplication Service", "Trash Service"
        ],
        "architecture_summary": "Block-level storage with deduplication. Conflict resolution via vector clocks. Real-time sync using long-polling or WebSocket.",
        "tags": ["storage", "sync", "files", "cloud", "dedup", "real-time"],
        "reference_url": "https://systeminterview.com/design-google-drive.php",
    },
    {
        "name": "Dropbox",
        "slug": "dropbox",
        "description": "File synchronization and sharing service across platforms",
        "design_type": "HLD",
        "key_components": [
            "Block Service", "Metadata Service", "Sync Client",
            "Notification Service", "Dedup Service", "Preview Service"
        ],
        "architecture_summary": "Originally AWS S3, now Magic Pocket (custom storage). Delta sync for efficient updates. Block-level deduplication saves storage.",
        "tags": ["storage", "sync", "files", "dedup", "delta-sync", "desktop"],
        "reference_url": None,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # LOW-LEVEL DESIGN (LLD) EXAMPLES
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Rate Limiter",
        "slug": "rate-limiter",
        "description": "Distributed rate limiting service using various algorithms",
        "design_type": "LLD",
        "key_components": ["Token Bucket", "Sliding Window", "Redis Store", "Counter Service"],
        "architecture_summary": "Distributed rate limiter supporting Token Bucket, Leaky Bucket, Fixed Window, and Sliding Window algorithms. Redis for distributed state.",
        "tags": ["rate-limit", "distributed", "redis", "algorithm", "lld", "concurrency"],
        "reference_url": None,
    },
    {
        "name": "URL Shortener",
        "slug": "url-shortener",
        "description": "URL shortening service like bit.ly with analytics",
        "design_type": "LLD",
        "key_components": ["Hash Generator (Base62)", "Key-Value Store", "Analytics", "Redirect Service"],
        "architecture_summary": "Base62 encoding with distributed ID generator (Snowflake). Redis cache for hot URLs. Analytics pipeline for click tracking.",
        "tags": ["url", "shortener", "hash", "key-value", "lld", "base62"],
        "reference_url": None,
    },
]


# ─── Seed Function ───────────────────────────────────────────────────────────

async def seed_famous_systems(db: AsyncSession) -> int:
    """
    Seed the famous_systems table with reference data.
    Idempotent - safe to run multiple times (uses UPSERT).
    
    Returns:
        Number of systems inserted/updated
    """
    logger.info(f"🌱 Starting seed of {len(FAMOUS_SYSTEMS_DATA)} famous systems...")
    
    inserted_count = 0
    
    for system_data in FAMOUS_SYSTEMS_DATA:
        # Check if already exists
        result = await db.execute(
            select(FamousSystem).where(FamousSystem.slug == system_data["slug"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing record
            existing.name = system_data["name"]
            existing.description = system_data["description"]
            existing.design_type = system_data["design_type"]
            existing.key_components = system_data["key_components"]
            existing.architecture_summary = system_data["architecture_summary"]
            existing.tags = system_data["tags"]
            existing.reference_url = system_data.get("reference_url")
        else:
            # Create new record
            system = FamousSystem(
                name=system_data["name"],
                slug=system_data["slug"],
                description=system_data["description"],
                design_type=system_data["design_type"],
                key_components=system_data["key_components"],
                architecture_summary=system_data["architecture_summary"],
                tags=system_data["tags"],
                reference_url=system_data.get("reference_url"),
            )
            db.add(system)
            inserted_count += 1
    
    await db.commit()
    
    logger.info(f"✅ Seeded {inserted_count} new systems, updated {len(FAMOUS_SYSTEMS_DATA) - inserted_count} existing")
    return inserted_count


def get_all_seed_data() -> List[Dict[str, Any]]:
    """Get all seed data (for testing/caching)."""
    return FAMOUS_SYSTEMS_DATA.copy()
"""
Famous Systems Seed Data
========================
Contains 60 famous system designs for reference (expanded from 27).
Populates the database on startup (idempotent).

Changes vs original:
- Expanded from 27 → 60 systems
- Added richer architecture_summary fields with concrete numbers & trade-offs
- Added 4 new categories: Cloud/Infra, Finance/Crypto, AI/ML Platform, Maps/Location
- All existing entries enriched with deeper technical context
"""
import logging
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FamousSystem

logger = logging.getLogger(__name__)


# ─── Famous Systems Data (60 Systems) ─────────────────────────────────────────

FAMOUS_SYSTEMS_DATA: List[Dict[str, Any]] = [
    # ═══════════════════════════════════════════════════════════════════════
    # SOCIAL MEDIA
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Twitter / X",
        "slug": "twitter",
        "description": "Real-time microblogging with timeline feeds, trending topics, and follower graphs at 350M MAU",
        "design_type": "HLD",
        "key_components": [
            "Timeline Service", "Fan-out Service (Flock)", "Tweet Service",
            "Graph Service (FlockDB)", "Search (Earlybird)", "Trending Service",
            "Notification Service", "Media CDN (BlobStore)"
        ],
        "architecture_summary": (
            "Read-heavy (read:write ≈ 100:1). Fan-out-on-write for users with <20K followers: "
            "tweet is pushed to all follower Redis timeline caches immediately (avg 75 followers → 75 cache writes). "
            "Pull-on-read for celebrities (>20K followers) — Lady Gaga with 50M followers would trigger 50M writes. "
            "Redis stores the latest 800 tweet IDs per user timeline. "
            "Earlybird (in-memory inverted index) powers real-time search with <10s latency. "
            "Manhattan (custom distributed key-value store) replaced MySQL for tweet storage. "
            "Media delivered via BlobStore → Fastly CDN. "
            "Key trade-off: fan-out-on-write gives fast reads but spikes write load during viral events."
        ),
        "tags": ["social", "feed", "real-time", "read-heavy", "fan-out", "timeline", "redis"],
        "reference_url": "https://systeminterview.com/design-twitter.php",
    },
    {
        "name": "Instagram",
        "slug": "instagram",
        "description": "Photo and video sharing with stories, reels, and social feeds at 2B+ MAU",
        "design_type": "HLD",
        "key_components": [
            "Media Upload Service", "Feed Service", "Story Service",
            "CDN (Fastly + custom)", "Object Storage (S3 + internal)", "Cassandra",
            "Notification Service", "Direct Messaging (Threads)"
        ],
        "architecture_summary": (
            "Photos stored in S3, metadata in PostgreSQL with sharding. "
            "Feed generation: fan-out-on-write into Cassandra timeline rows. "
            "Celery + RabbitMQ for async media processing (resize, compress). "
            "Stories use a separate time-windowed data model (TTL = 24h). "
            "Shifted from Django monolith to microservices after acquisition. "
            "Python Django + Gunicorn backend. Heavy use of memcached for object caching. "
            "Key insight: PostgreSQL ID sequence was a bottleneck at scale — replaced with a "
            "distributed ID generator. pgBouncer for connection pooling."
        ),
        "tags": ["social", "media", "feed", "cdn", "object-storage", "stories", "cassandra"],
        "reference_url": "https://systeminterview.com/design-instagram.php",
    },
    {
        "name": "Facebook News Feed",
        "slug": "facebook-newsfeed",
        "description": "Personalized news feed aggregation for 3B+ monthly users",
        "design_type": "HLD",
        "key_components": [
            "Feed Publisher", "Fan-out Service", "Aggregator",
            "Edge Rank / ML Ranker", "TAO (Social Graph Cache)", "Memcached (McRouter)",
            "Haystack (Photo Storage)", "Scuba (Real-time Analytics)"
        ],
        "architecture_summary": (
            "Hybrid fan-out: push for normal users, pull for celebrities and pages. "
            "TAO (The Associations and Objects) — custom graph cache sits in front of MySQL, "
            "handles billions of social graph reads/sec. "
            "Feed ranking uses thousands of ML signals (EdgeRank → GBDT → neural nets). "
            "McRouter manages Memcached sharding and replication. "
            "Haystack stores 260B photos — optimized for high IOPS with needle/haystack indexing. "
            "Key trade-off: eventual consistency in feed (users may see stale data for seconds). "
            "Write fanout to 5000-friend feeds can lag by minutes during peak."
        ),
        "tags": ["social", "feed", "ml", "ranking", "fan-out", "graph", "tao"],
        "reference_url": "https://engineering.fb.com/",
    },
    {
        "name": "TikTok",
        "slug": "tiktok",
        "description": "Short-form video platform with AI-driven For You Page serving 1B+ MAU",
        "design_type": "HLD",
        "key_components": [
            "Video Ingestion Service", "Transcoding Pipeline (FFmpeg clusters)",
            "Recommendation Engine (deep learning)", "For You Page (FYP) Service",
            "CDN (BytePlus / Akamai)", "MLOPS Platform", "Live Streaming Service",
            "Creator Monetization Service"
        ],
        "architecture_summary": (
            "Core differentiator is the recommendation engine: watches watch-time percentage, "
            "shares, re-watches, and profile actions. Uses a two-tower retrieval model then "
            "a ranking model. Cold-start handled by distributing new videos to 100-500 random "
            "users first, then amplifying based on engagement signals. "
            "Video transcoded to multiple bitrates (HLS) for adaptive streaming. "
            "Stores ~72 hours of video per second upload rate. "
            "Uses Kafka for event streaming and ClickHouse for analytics. "
            "Infrastructure built on ByteDance's internal cloud (TCE). "
            "Key trade-off: optimizing for watch time increases engagement but can amplify "
            "extreme content — requires heavy content moderation ML layer."
        ),
        "tags": ["video", "ml", "recommendation", "feed", "transcoding", "short-form", "ai"],
        "reference_url": None,
    },
    {
        "name": "Pinterest",
        "slug": "pinterest",
        "description": "Visual discovery engine with 450M MAU and 300B+ pins",
        "design_type": "HLD",
        "key_components": [
            "Pin Service", "Board Service", "Smart Feed (ML)",
            "Visual Search (PinSage GNN)", "Image Processing Pipeline",
            "HBase (pin metadata)", "S3 (images)", "Kafka"
        ],
        "architecture_summary": (
            "PinSage — graph neural network for related pin recommendations — "
            "operates on a graph of 3B nodes (pins + users) and 18B edges. "
            "Smart Feed ranks candidate pins using a 3-stage pipeline: "
            "candidate generation → lightweight scoring → heavy neural ranker. "
            "Images stored in S3, thumbnails pre-generated at multiple sizes via Lambda. "
            "HBase for pin → board → user graph. Kafka for real-time event streaming. "
            "MySQL for transactional data with horizontal sharding. "
            "Key insight: visual search uses image embeddings (CNN) to find visually similar pins "
            "without needing text metadata — solved cold-start for new pins."
        ),
        "tags": ["social", "image", "feed", "ml", "visual-search", "discovery", "gnn"],
        "reference_url": "https://medium.com/pinterest-engineering",
    },
    {
        "name": "LinkedIn",
        "slug": "linkedin",
        "description": "Professional networking at 900M members with job postings and content feeds",
        "design_type": "HLD",
        "key_components": [
            "Feed Service (Pemberton)", "Voldemort (K-V Store)", "Databus (CDC)",
            "Galene (Search Engine)", "Venice (Feature Store)", "Kafka",
            "OCEAN (Job Matching ML)", "InMail (Messaging)"
        ],
        "architecture_summary": (
            "Migrated from monolith (Leo) to microservices (2012). "
            "Voldemort — custom distributed key-value store — handles billions of profile reads. "
            "Databus — change-data-capture system — propagates DB changes to downstream services. "
            "Galene is a custom search engine built on Lucene, serving 2B+ searches/day. "
            "Venice is a derived data store (feature store) for ML feature serving. "
            "Feed uses a hybrid on-write/on-read strategy. "
            "OCEAN ML system matches jobs to candidates using gradient-boosted trees. "
            "Key trade-off: Voldemort chose availability + partition tolerance over consistency."
        ),
        "tags": ["social", "professional", "feed", "search", "jobs", "networking", "kafka"],
        "reference_url": "https://engineering.linkedin.com/",
    },
    {
        "name": "Reddit",
        "slug": "reddit",
        "description": "Community-driven content voting platform with 50M+ DAU and 100K+ subreddits",
        "design_type": "HLD",
        "key_components": [
            "Post Service", "Vote Service", "Comment Service",
            "Ranking Engine (Reddit Score)", "Subreddit Service",
            "Search (Elasticsearch)", "Media Hosting", "ModQueue"
        ],
        "architecture_summary": (
            "Reddit score formula: score = log10(|ups - downs|) × sign + seconds/45000. "
            "Uses PostgreSQL for transactional data, sharded by subreddit. "
            "Vote fraud detection via ML on voting patterns and account age. "
            "New Reddit (2018) migrated from Python 2 monolith to GraphQL gateway + microservices. "
            "Media (images, videos) hosted via RPAN and media.reddit.com on S3 + CloudFront. "
            "Comment trees stored with adjacency list model, rendered client-side. "
            "Key challenge: hot posts trigger massive read spikes — solved with aggressive caching "
            "and pre-computation of hot/top/new feeds per subreddit."
        ),
        "tags": ["social", "voting", "feed", "community", "comments", "ranking"],
        "reference_url": None,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # MESSAGING
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "WhatsApp",
        "slug": "whatsapp",
        "description": "E2E encrypted messaging at 2B+ users with 100B messages/day",
        "design_type": "HLD",
        "key_components": [
            "Chat Service (Ejabberd/Erlang)", "Presence Service", "Offline Queue",
            "Signal Protocol (E2E Encryption)", "Key Store", "Media Service",
            "Group Chat Service", "Status Service"
        ],
        "architecture_summary": (
            "Built on Erlang/Ejabberd for massive concurrency — Erlang processes are lightweight "
            "(2KB RAM each), allowing millions of concurrent connections per server. "
            "Uses XMPP protocol extended with custom stanzas. "
            "Signal Protocol for E2E encryption: Double Ratchet algorithm for forward secrecy. "
            "Messages stored on server only until delivered, then deleted (7 days for offline users). "
            "Groups limited to 1024 members — fan-out done server-side. "
            "54 engineers supported 900M users in 2015 — extreme ops efficiency. "
            "FreeBSD for OS, custom build of Erlang with latency tuning. "
            "Key trade-off: no server-side message history (privacy) but limits backup features."
        ),
        "tags": ["messaging", "real-time", "websocket", "encryption", "erlang", "e2e", "xmpp"],
        "reference_url": "https://systeminterview.com/design-whatsapp.php",
    },
    {
        "name": "Telegram",
        "slug": "telegram",
        "description": "Cloud-based messaging with channels up to 200K members, bots, and secret chats",
        "design_type": "HLD",
        "key_components": [
            "MTProto 2.0 Protocol", "Multi-DC Architecture (5 regions)", "Chat Service",
            "Channel Service", "Bot API (webhooks)", "Media Service",
            "TDLib (Telegram Database Library)", "Infinite Storage"
        ],
        "architecture_summary": (
            "MTProto 2.0 — custom binary protocol — optimized for high latency/lossy networks; "
            "uses AES-256-IGE + SHA-256 for encryption. "
            "5 globally distributed data centers with cross-DC replication. "
            "Cloud storage: all messages/media stored server-side indefinitely — "
            "contrast with WhatsApp's delete-after-delivery. "
            "Secret Chats use client-client DH key exchange (not stored on servers). "
            "Channels can broadcast to unlimited subscribers via server-side fan-out. "
            "Bot API uses long-polling or webhooks; 10K+ requests/sec handled. "
            "TDLib open-source client library allows building cross-platform clients. "
            "Key trade-off: cloud storage gives multi-device sync but requires trusting Telegram's servers."
        ),
        "tags": ["messaging", "real-time", "channels", "bots", "mtproto", "distributed", "cloud-storage"],
        "reference_url": "https://core.telegram.org/",
    },
    {
        "name": "Slack",
        "slug": "slack",
        "description": "Team collaboration with channels, threads, and 2500+ integrations at 20M DAU",
        "design_type": "HLD",
        "key_components": [
            "Channel Service", "Message Service (Flannel)", "Search (Elasticsearch)",
            "Presence Service", "Notification Service", "Vitess (MySQL scaling)",
            "Integration Hub (Slack App Directory)", "Huddle (Audio/Video)"
        ],
        "architecture_summary": (
            "Flannel — edge cache layer — reduces WebSocket connection load on core servers; "
            "clients connect to Flannel which fans out events. "
            "Vitess for MySQL sharding — scales MySQL horizontally across hundreds of shards. "
            "Each workspace is a shard unit; cross-workspace queries are rare. "
            "Real-time message delivery via WebSocket; persistent long-polling fallback. "
            "Elasticsearch indexes every message for full-text search (important differentiator). "
            "App integrations via slash commands, webhooks, Events API, and Socket Mode. "
            "Migrated to GCP in 2021 with >99.99% uptime SLA. "
            "Key trade-off: per-workspace sharding simplifies isolation but complicates "
            "cross-workspace features like Slack Connect."
        ),
        "tags": ["messaging", "collaboration", "real-time", "webhooks", "teams", "search", "vitess"],
        "reference_url": "https://slack.engineering/",
    },
    {
        "name": "Discord",
        "slug": "discord",
        "description": "Voice/video/text for 19M active servers and 200M+ registered users",
        "design_type": "HLD",
        "key_components": [
            "Gateway Service (Elixir)", "Voice Service (WebRTC + SFU)",
            "Chat Service", "Guild Service", "Presence Service",
            "ScyllaDB (message history)", "Rust media processing", "CDN"
        ],
        "architecture_summary": (
            "Gateway layer built in Elixir — leverages the BEAM VM for massive concurrency; "
            "each WebSocket session is a lightweight process. "
            "Voice uses a custom SFU (Selective Forwarding Unit) built on WebRTC — "
            "server routes media packets without decoding/re-encoding. "
            "ScyllaDB (C++ Cassandra-compatible) for message history — "
            "migrated from Cassandra to ScyllaDB for 40% lower latency and 50% fewer nodes. "
            "Rust for performance-critical media processing (encoding, noise suppression). "
            "Guild (server) metadata in PostgreSQL; large guilds (1M+ members) required "
            "special presence handling — Discord sets 'offline' presence above 75K members. "
            "Key trade-off: WebRTC SFU gives low latency but bandwidth scales with O(N) connections."
        ),
        "tags": ["messaging", "voice", "video", "webrtc", "real-time", "gaming", "elixir", "scylladb"],
        "reference_url": "https://discord.com/blog/",
    },
    {
        "name": "iMessage / Apple Push Notification Service",
        "slug": "apns",
        "description": "Apple's push notification infrastructure delivering 3B+ notifications/day",
        "design_type": "HLD",
        "key_components": [
            "APNs Provider API", "Device Token Registry", "Feedback Service",
            "iMessage Relay", "FaceTime Relay", "Identity Service (IDS)",
            "End-to-End Encryption", "CloudKit Sync"
        ],
        "architecture_summary": (
            "APNs maintains persistent TLS connections to each Apple device worldwide. "
            "Device tokens are ephemeral and rotate — APNs Feedback Service notifies providers "
            "of invalid tokens to prevent repeated sends. "
            "iMessage uses IDS (Identity Directory Service) to look up which Apple ID owns "
            "a phone number/email, then delivers via APNs. "
            "Messages stored in CloudKit — iCloud end-to-end encryption uses device-only keys. "
            "Fallback to SMS when iMessage is unavailable (carrier network). "
            "Key challenge: QoS (Quality of Service) levels for notifications — "
            "priority 10 (immediate), priority 5 (power saving), priority 1 (silent). "
            "Key trade-off: device tokens don't reveal IP addresses (privacy-preserving) "
            "but makes delivery confirmation harder."
        ),
        "tags": ["messaging", "push", "notifications", "apple", "tls", "e2e", "mobile"],
        "reference_url": None,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # VIDEO & STREAMING
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "YouTube",
        "slug": "youtube",
        "description": "Largest video platform: 500+ hours uploaded/minute, 2B+ logged-in users/month",
        "design_type": "HLD",
        "key_components": [
            "Upload Service", "Transcoding Pipeline (Borg jobs)",
            "Colossus File System", "Bigtable (metadata)", "Spanner (global metadata)",
            "Recommendation Engine (neural nets)", "Search", "CDN Edge Servers"
        ],
        "architecture_summary": (
            "Videos uploaded → stored in Colossus (Google's distributed FS) → "
            "transcoding jobs run on Google Borg (container orchestration) converting to "
            "10+ formats and resolutions (360p → 4K, VP9 + H.264). "
            "Metadata (title, description, likes) in Bigtable for fast reads. "
            "Global metadata and user data in Spanner for strong consistency. "
            "Recommendation: two-stage — candidate generation (retrieval) using matrix factorization, "
            "then ranking DNN scoring candidates on 100+ features (watch time, CTR, satisfaction). "
            "Watch time is the primary ranking signal (not views/likes). "
            "CDN edge caches popular content close to users — top 1% of videos served from cache. "
            "Key trade-off: transcoding all formats up-front (storage cost) vs "
            "on-demand transcoding (CPU cost) — YouTube chose pre-transcode."
        ),
        "tags": ["video", "streaming", "cdn", "ml", "transcoding", "recommendation", "bigtable"],
        "reference_url": "https://systeminterview.com/design-youtube.php",
    },
    {
        "name": "Netflix",
        "slug": "netflix",
        "description": "SVOD leader with 238M subscribers streaming 1B+ hours/week globally",
        "design_type": "HLD",
        "key_components": [
            "Open Connect CDN", "Zuul (API Gateway)", "Eureka (Service Discovery)",
            "Hystrix (Circuit Breaker)", "Cassandra (user data)", "Kafka (events)",
            "Recommendation Engine (ML)", "Studio Encoding Pipeline"
        ],
        "architecture_summary": (
            "Fully on AWS — migrated from datacenter over 7 years (2008–2015). "
            "Open Connect: Netflix-built CDN with 17K+ servers in ISP networks worldwide — "
            "serves 95%+ of video traffic, reducing transit costs dramatically. "
            "Content pre-positioned on Open Connect servers using ML predictions of what "
            "subscribers in each region will watch in the next 24h. "
            "Chaos Engineering (Chaos Monkey, Chaos Kong) — deliberately kills services in prod "
            "to ensure resilience. "
            "Hystrix circuit breaker prevents cascade failures — fallback to degraded experience. "
            "Recommendation: two-stage (ALS matrix factorization for candidates, then ranking). "
            "Cassandra for user activity/ratings: 95th percentile latency <1ms at scale. "
            "Key trade-off: eventual consistency in recommendations vs. strong consistency in billing."
        ),
        "tags": ["video", "streaming", "cdn", "microservices", "ml", "aws", "chaos-engineering"],
        "reference_url": "https://netflixtechblog.com/",
    },
    {
        "name": "Spotify",
        "slug": "spotify",
        "description": "Music streaming at 600M MAU with 100M songs and podcast catalog",
        "design_type": "HLD",
        "key_components": [
            "Streaming Service", "Playlist Service (Merkle trees)",
            "Discover Weekly (ML)", "Search (Elasticsearch)",
            "Artist Platform", "Podcast Platform (Anchor)",
            "Backstage (internal developer portal)", "GCP + Kubernetes"
        ],
        "architecture_summary": (
            "Audio served from GCS (Google Cloud Storage) via CDN — adaptive bitrate (96kbps → 320kbps). "
            "Playlist sync uses Merkle trees to efficiently detect changes across devices — "
            "only differing subtrees are synced. "
            "Discover Weekly: matrix factorization (ALS) on 30B+ user-track interactions + "
            "NLP analysis of music blogs for contextual recommendations. "
            "Microservices: 300+ services on GKE (Google Kubernetes Engine). "
            "Backstage (open-sourced) — internal developer portal for service catalog, "
            "TechDocs, and scaffolding. "
            "Key trade-off: storing audio files in cloud storage means $$ costs at scale — "
            "Spotify optimizes with aggressive caching at edge and popular-track pre-positioning."
        ),
        "tags": ["audio", "streaming", "ml", "playlist", "discovery", "music", "kubernetes"],
        "reference_url": "https://engineering.atspotify.com/",
    },
    {
        "name": "Twitch",
        "slug": "twitch",
        "description": "Live streaming at 30M+ daily visitors with 8M+ monthly broadcasters",
        "design_type": "HLD",
        "key_components": [
            "Ingest Service (RTMP)", "Transcoding Service (GPU clusters)",
            "Edge Network (LLHLS + WebRTC)", "Chat Service (IRC-based)",
            "Clip Service", "VOD Service", "Monetization (Bits/Subscriptions)", "Analytics"
        ],
        "architecture_summary": (
            "Broadcasters stream via RTMP to regional ingest servers. "
            "GPU transcoding farms convert to multiple quality levels (160p → 1080p60) in real-time. "
            "Low Latency HLS (LLHLS) delivers ~2-4 second latency to viewers; "
            "Ultra Low Latency mode via WebRTC achieves sub-second for interactive streams. "
            "Chat uses IRC-extended protocol — each channel is a chat room; "
            "high-traffic channels (100K+ viewers) use server-side message sampling to prevent overload. "
            "Clips stored as HLS segments from the live buffer (no re-encoding needed). "
            "Runs on AWS with custom media infrastructure. "
            "Key trade-off: LLHLS gives lower latency than standard HLS but requires "
            "partial segment support in CDN edge servers."
        ),
        "tags": ["live-streaming", "video", "chat", "real-time", "gaming", "cdn", "rtmp"],
        "reference_url": None,
    },
    {
        "name": "Zoom",
        "slug": "zoom",
        "description": "Video conferencing platform scaling from 10M to 300M daily participants in 2020",
        "design_type": "HLD",
        "key_components": [
            "Meeting Service", "Media Router (SFU + MCU hybrid)",
            "Signaling Service (WebSocket)", "Recording Service",
            "Zoom Phone (SIP/PSTN bridge)", "Chat Service", "Calendar Integration"
        ],
        "architecture_summary": (
            "Hybrid SFU/MCU: SFU for small meetings (<5 participants, each stream forwarded separately), "
            "MCU for large meetings (server mixes streams into single composite — saves client bandwidth). "
            "Zoom's proprietary video codec (not VP8/H.264) optimized for unstable networks — "
            "can sustain quality at 40% packet loss. "
            "Multi-cloud: AWS + Azure + Oracle Cloud — switched to Oracle for 20x cost reduction. "
            "End-to-end encryption (E2E option, 2020): Zoom becomes a relay with no media access. "
            "WebRTC-based web client; native apps use proprietary UDP-based transport. "
            "Key trade-off during COVID-19 surge: prioritized availability over security "
            "(routing calls through China datacenters) — caused significant backlash."
        ),
        "tags": ["video", "conferencing", "webrtc", "real-time", "meetings", "sfu", "mcu"],
        "reference_url": None,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # TRANSPORTATION & LOGISTICS
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Uber",
        "slug": "uber",
        "description": "Ride-sharing at 5M+ drivers and 130M+ riders with real-time matching",
        "design_type": "HLD",
        "key_components": [
            "Dispatch Service (ringpop)", "Location Service (H3 hexagonal grid)",
            "Matching Service (Kafka Streams)", "Pricing Engine (surge ML)",
            "Payment Service", "Maps (HERE + custom)", "ETA Service (ML)",
            "Driver App (FIFO queue dispatch)"
        ],
        "architecture_summary": (
            "Location tracking: drivers send GPS updates every 4 seconds → "
            "stored in Cassandra with H3 hexagonal geospatial index. "
            "H3 cells at resolution 9 (~0.1km²) used for supply/demand aggregation. "
            "Dispatch uses ringpop for consistent hashing across dispatch servers — "
            "each geographic cell 'owned' by one server for serialized matching. "
            "ETA service: ML model on road network graph (osrm + proprietary). "
            "Surge pricing: gradient boosted trees on supply/demand per H3 cell. "
            "Kafka Streams for real-time pricing event processing. "
            "Schemaless (Cassandra-backed) key-value store for flexible trip state. "
            "Key trade-off: eventual consistency in driver locations (4s update interval) "
            "is acceptable for matching but would break safety features requiring real-time tracking."
        ),
        "tags": ["location", "real-time", "matching", "geo", "dispatch", "pricing", "h3"],
        "reference_url": "https://systeminterview.com/design-uber.php",
    },
    {
        "name": "Airbnb",
        "slug": "airbnb",
        "description": "Vacation rental marketplace with 7M+ listings across 220 countries",
        "design_type": "HLD",
        "key_components": [
            "Search Service (Elasticsearch + ML ranking)", "Listing Service",
            "Booking Engine (state machine)", "Payment Service (multi-currency)",
            "Review Service", "Messaging Service", "Pricing Intelligence (ML)",
            "Trust & Safety (Sentinel)"
        ],
        "architecture_summary": (
            "Search: Elasticsearch for geo-bounding-box filtering, then ML ranking with "
            "price, availability, reviews, and personalization signals. "
            "Booking state machine: INQUIRY → REQUEST → PRE-APPROVED → ACCEPTED/DECLINED — "
            "distributed saga pattern ensures consistency across payment, calendar, and notification. "
            "Calendar availability uses Redis Sorted Sets for O(log N) range queries. "
            "Multi-currency payments: collects in guest currency, pays out in host currency — "
            "requires FX rate caching and settlement batch jobs. "
            "Sentinel fraud detection: ML models on booking velocity, IP reputation, device fingerprint. "
            "Microservices on AWS, migrated from Rails monolith (2012–2017). "
            "Key trade-off: double-booking prevention requires strong consistency in calendar updates "
            "but most reads can tolerate eventual consistency."
        ),
        "tags": ["marketplace", "search", "booking", "payments", "geo", "reviews", "saga"],
        "reference_url": "https://medium.com/airbnb-engineering",
    },
    {
        "name": "DoorDash",
        "slug": "doordash",
        "description": "Food delivery marketplace with 37M+ consumers, 600K+ dashers, 700K+ merchants",
        "design_type": "HLD",
        "key_components": [
            "Order Service", "Dispatch Platform (Pegasus)", "ETA Service",
            "Menu Service", "Storefront Service", "Payment Service",
            "Merchant Portal", "Dasher App"
        ],
        "architecture_summary": (
            "Pegasus dispatch platform: ML model assigns orders to Dashers, "
            "optimizing for delivery time, pay, and batching (picking up multiple orders). "
            "ETA: combines restaurant prep time (ML on historical data) + "
            "drive time (traffic-aware routing) + wait at merchant. "
            "Menu service uses event sourcing — merchant menu changes propagate via Kafka "
            "to all consumer-facing services. "
            "Storefront: multi-tenant SaaS for restaurants (white-label ordering). "
            "Architecture: migrated from monolith to microservices on Kubernetes/AWS. "
            "DashMart (ghost kitchen) requires real-time inventory management. "
            "Key trade-off: order batching increases dasher efficiency but adds latency for "
            "customers — ML must balance these competing objectives."
        ),
        "tags": ["marketplace", "delivery", "location", "ml", "dispatch", "food-tech"],
        "reference_url": None,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # E-COMMERCE & PAYMENTS
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Amazon",
        "slug": "amazon",
        "description": "World's largest e-commerce at $500B+ GMV with AWS cloud services",
        "design_type": "HLD",
        "key_components": [
            "Product Catalog (P13N)", "Shopping Cart (DynamoDB)", "Order Service",
            "Recommendation Engine (item-to-item CF)", "Search (A9/OpenSearch)",
            "Fulfillment Network", "Prime Delivery Routing", "AWS Lambda (serverless)"
        ],
        "architecture_summary": (
            "Microservices pioneer — Werner Vogels's 'two-pizza team' rule. "
            "Shopping cart uses DynamoDB — always-writeable, eventually consistent (CRDT model). "
            "Recommendation: item-to-item collaborative filtering — 'customers who bought X also bought Y' — "
            "scales better than user-based CF for 350M+ customers. "
            "A9 (now OpenSearch): inverted index + personalized ranking for product search. "
            "Two-phase commit avoided — sagas pattern for order fulfillment: "
            "Place Order → Reserve Inventory → Charge Payment → Schedule Shipment. "
            "Prime delivery: ML optimization on fulfillment center assignment. "
            "Prime Day stress test: 375M items sold in 48 hours (2022). "
            "Key trade-off: accepting abandoned carts in DynamoDB (no lock on items) "
            "prevents inventory reservation conflicts at scale."
        ),
        "tags": ["ecommerce", "microservices", "recommendations", "search", "fulfillment", "dynamodb"],
        "reference_url": None,
    },
    {
        "name": "Shopify",
        "slug": "shopify",
        "description": "E-commerce platform powering 4M+ online stores with $197B+ GMV",
        "design_type": "HLD",
        "key_components": [
            "Storefront API (GraphQL)", "Checkout Service", "Payment Gateway (Shopify Payments)",
            "Inventory Service", "Liquid Template Engine", "Fulfillment Network (SFN)",
            "App Ecosystem (Polaris)", "Flash Sale Handler (Tokengating)"
        ],
        "architecture_summary": (
            "Multi-tenant architecture: each shop is a tenant; data sharded by shop_id in MySQL. "
            "2K+ MySQL shards managed by Vitess for horizontal scaling. "
            "Storefront API: GraphQL allows merchants to query only needed fields, "
            "reducing over-fetching for headless commerce use cases. "
            "Checkout: must handle flash sales — 'Buy with Prime' style tokengating "
            "uses Redis to manage inventory locks with TTL. "
            "Redis caches storefront data aggressively (product catalogs change infrequently). "
            "Shopify Payments: built on Stripe; settled $86B in payments (2022). "
            "BFCM (Black Friday): peaks at 50K+ orders/min — tested via 'Bfcm load testing'. "
            "Key trade-off: per-shop sharding gives strong isolation but "
            "cross-shop reporting (analytics) requires expensive scatter-gather queries."
        ),
        "tags": ["ecommerce", "saas", "multi-tenant", "graphql", "payments", "inventory", "vitess"],
        "reference_url": "https://shopify.engineering/",
    },
    {
        "name": "Stripe",
        "slug": "stripe",
        "description": "Payment infrastructure processing $817B in total payment volume with 99.999% uptime",
        "design_type": "HLD",
        "key_components": [
            "Payment API (REST + Events)", "Idempotency Layer", "Radar (Fraud ML)",
            "Connect (marketplace payments)", "Checkout (hosted page)",
            "Webhook Delivery Service", "Reconciliation Engine", "Stripe CLI"
        ],
        "architecture_summary": (
            "Idempotency keys: every API request can include an Idempotency-Key header — "
            "server stores request/response in Redis for 24h to safely retry without double-charge. "
            "Radar fraud detection: ML on 500+ signals (card BIN, IP, behavior, velocity). "
            "Webhook delivery: guaranteed at-least-once delivery with exponential backoff retries "
            "(up to 3 days). Uses a queue with dead-letter handling. "
            "Connect for marketplaces: money flows Payer → Platform → Connected Account — "
            "requires complex routing and split settlement logic. "
            "Stripe uses Ruby on Rails (unusual at scale) with extensive performance engineering. "
            "Strong consistency for payment records via PostgreSQL with distributed transactions. "
            "Key insight: API design is Stripe's moat — immutable API versioning means "
            "customers' integrations never break when Stripe evolves the API."
        ),
        "tags": ["payments", "fintech", "api", "fraud", "idempotency", "webhooks", "marketplace"],
        "reference_url": "https://stripe.com/blog/engineering",
    },
    {
        "name": "PayPal",
        "slug": "paypal",
        "description": "Digital payment platform handling $1.36T TPV with 435M active accounts",
        "design_type": "HLD",
        "key_components": [
            "Transaction Service", "Fraud Detection (Simility ML)", "Wallet Service",
            "Settlement Service", "Risk Engine", "Compliance/KYC Service",
            "Venmo Integration", "BNPL (Pay Later)"
        ],
        "architecture_summary": (
            "ACID-compliant transaction ledger: double-entry bookkeeping — "
            "every debit has corresponding credit; strong consistency via 2PC. "
            "Fraud detection: graph ML on transaction network (flagging money mule rings), "
            "velocity checks, device fingerprinting. Simility (acquired 2018) brought ML fraud stack. "
            "Settlement: batch processing via ISO 20022 messages to banking networks (FedACH, SWIFT). "
            "Compliance: KYC/AML pipeline — new accounts verified via ID doc scanning + ML. "
            "Migrated from monolith (C++ on proprietary Oracle) to microservices (Java/Node) 2015–2022. "
            "Real-time hold: instant fund availability backed by PayPal's credit facility. "
            "Key trade-off: strong consistency for ledger correctness "
            "means some writes are slow (100ms+) — acceptable for payments."
        ),
        "tags": ["payments", "transactions", "fraud", "fintech", "acid", "compliance", "ledger"],
        "reference_url": None,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # SEARCH & DISCOVERY
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Google Search",
        "slug": "google-search",
        "description": "Dominant search engine indexing 100B+ web pages with 8.5B daily searches",
        "design_type": "HLD",
        "key_components": [
            "Googlebot (Crawler)", "Caffeine (Indexing Pipeline)", "Bigtable (raw crawl)",
            "PageRank Algorithm", "BERT/MUM (Query Understanding)", "Knowledge Graph",
            "Ad Serving (AdWords)", "Quality Rater System"
        ],
        "architecture_summary": (
            "Crawling: Googlebot distributed crawl — prioritizes high-quality, frequently-updated pages. "
            "Caffeine (2010 rewrite): continuous incremental indexing replaces batch map-reduce — "
            "reduces freshness lag from days to seconds. "
            "PageRank (original signal): iterative algorithm on web graph, "
            "converges in 50–100 iterations on trillion-node graph. "
            "Modern ranking: 200+ signals including BERT embeddings for semantic query understanding, "
            "MUM (Multitask Unified Model) for multimodal understanding. "
            "Serving: results pre-computed and cached in Bigtable; "
            "query routing via consistent hashing across index shards. "
            "Colossus FS stores petabytes of crawl data. "
            "Key trade-off: freshness vs. quality — real-time indexing can surface low-quality "
            "or spammy new content; must balance crawl freshness with quality signals."
        ),
        "tags": ["search", "crawling", "indexing", "ranking", "ml", "distributed", "pagerank"],
        "reference_url": None,
    },
    {
        "name": "Elasticsearch",
        "slug": "elasticsearch",
        "description": "Distributed search and analytics engine powering 1B+ daily queries across deployments",
        "design_type": "HLD",
        "key_components": [
            "Shard (Lucene index)", "Primary/Replica Shards", "Node (Data/Master/Coordinating)",
            "Cluster State (master node)", "Translog (WAL)", "Segment Merge",
            "Inverted Index", "Aggregations Engine"
        ],
        "architecture_summary": (
            "Built on Apache Lucene — each shard is a self-contained Lucene index. "
            "Primary shard receives writes → translog (WAL) for durability → "
            "refreshed into memory-mapped segment every 1 second (near-real-time). "
            "Segments immutable — updates are delete + re-insert; "
            "periodic merge reduces segment count (I/O intensive). "
            "Cluster state held in master nodes (3-node quorum) — single-master for consistency. "
            "Coordinating node distributes query to all shards, merges results (scatter-gather). "
            "BKD trees for numeric/geo queries; inverted index for text. "
            "Key trade-off: near-real-time indexing (1s refresh interval) vs. "
            "real-time (0ms) which requires flush to disk on every write — "
            "most use cases accept 1s for 10x throughput improvement."
        ),
        "tags": ["search", "distributed", "lucene", "indexing", "analytics", "inverted-index"],
        "reference_url": "https://www.elastic.co/blog/",
    },
    {
        "name": "Stack Overflow",
        "slug": "stackoverflow",
        "description": "Q&A platform with 100M+ monthly users and 58M+ answers since 2008",
        "design_type": "HLD",
        "key_components": [
            "Q&A Service (.NET/C#)", "Voting Service", "Tag Engine",
            "Search (Elasticsearch)", "Reputation Engine",
            "SQL Server (primary DB)", "Redis (L1 cache)", "HAProxy (load balancer)"
        ],
        "architecture_summary": (
            "Famous for being a monolith at scale — runs on 9 web servers (not hundreds). "
            "SQL Server stores all Q&A data; heavily optimized queries with covering indexes. "
            "Redis for L1 caching: hot questions and user reputation served from RAM. "
            "Tag Engine: pre-computed tag-question mapping in RAM on each web server. "
            "Reputation system: computed in real-time on vote events. "
            "Team Stack: 40 engineers serving 100M+ users — extreme efficiency. "
            "HAProxy for load balancing across 9 IIS web servers. "
            "Elasticsearch for full-text search across questions/answers. "
            "Key insight: most reads are for the same top 10-20% of questions (long-tail distribution) — "
            "aggressive HTTP caching (CDN for anonymous users) handles the bulk of traffic."
        ),
        "tags": ["qa", "voting", "reputation", "search", "monolith", "caching", "sqlserver"],
        "reference_url": "https://nickcraver.com/blog/",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # DEVELOPER TOOLS & CLOUD
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "GitHub",
        "slug": "github",
        "description": "Code hosting with 100M+ developers, 420M+ repositories, and CI/CD at scale",
        "design_type": "HLD",
        "key_components": [
            "Gitaly (Git RPC service)", "GitHub Actions (CI/CD on runners)",
            "Code Search (Zoekt)", "Pull Request Service", "Issues/Projects",
            "Packages (container registry)", "Copilot (AI coding assistant)",
            "MySQL (sharded) + GitHub::KV"
        ],
        "architecture_summary": (
            "Gitaly replaced direct Git process forks — NFS bottleneck removed; "
            "Gitaly servers hold repository data on local disk, accessible via gRPC. "
            "MySQL sharded by repository_id for relational data. "
            "GitHub Actions: ephemeral VM-based runners (hosted or self-hosted); "
            "runner assignment via FIFO queue per org/repo with priority queuing. "
            "Code Search uses Zoekt (trigram-based) for fast in-repo search; "
            "Blackbird for cross-GitHub code search (separate scale challenge). "
            "Spokes: triple-redundant Git storage across 3 DCs per repository. "
            "DDoS protection: Cloudflare + custom GitHub network tooling. "
            "Key trade-off: Git's lack of partial clone forces cloning entire repo history — "
            "large repos (Linux kernel) needed partial fetch protocol (2019)."
        ),
        "tags": ["git", "devtools", "cicd", "code-search", "collaboration", "repositories", "mysql"],
        "reference_url": "https://github.blog/engineering/",
    },
    {
        "name": "AWS S3",
        "slug": "aws-s3",
        "description": "Object storage at 300 trillion+ objects with 99.999999999% (11 9s) durability",
        "design_type": "HLD",
        "key_components": [
            "Frontend Service (request routing)", "Index Service (key→location mapping)",
            "Storage Service (actual data)", "Erasure Coding (data durability)",
            "S3 Lifecycle (transition/expiry)", "Replication Service (cross-region)",
            "Access Control (IAM + ACLs)", "Event Notifications (SNS/SQS/Lambda)"
        ],
        "architecture_summary": (
            "Objects partitioned by key prefix across storage nodes. "
            "Durability via erasure coding (Reed-Solomon) across ≥3 AZs — "
            "12+4 coding: can reconstruct from any 12 of 16 fragments. "
            "Index service maps object keys to storage locations — "
            "sharded B-tree; hot prefixes get extra shards (prefix optimization tip). "
            "Eventual consistency (until 2020), then strong read-after-write consistency for all objects. "
            "Storage classes: S3 Standard, IA, Glacier, Deep Archive — "
            "Glacier uses tape storage for <$0.001/GB/month. "
            "Multipart upload: required for objects >5GB; recommended for >100MB for parallelism. "
            "Key trade-off: flat namespace (no real directories) is simple but causes issues "
            "with 'list by prefix' at billions of objects — expensive O(N) scan."
        ),
        "tags": ["storage", "object-storage", "aws", "durability", "cloud", "erasure-coding"],
        "reference_url": "https://aws.amazon.com/blogs/aws/",
    },
    {
        "name": "Kubernetes",
        "slug": "kubernetes",
        "description": "Container orchestration managing millions of clusters with billions of pods",
        "design_type": "HLD",
        "key_components": [
            "API Server (etcd-backed)", "Scheduler", "Controller Manager",
            "kubelet (node agent)", "kube-proxy (networking)", "etcd (distributed KV)",
            "CNI Plugin (Calico/Flannel)", "CSI Plugin (storage)"
        ],
        "architecture_summary": (
            "Control plane: API server is the single gateway — all reads/writes go through it. "
            "etcd stores all cluster state as the source of truth — "
            "Raft consensus, strong consistency, 3-5 node quorum. "
            "Scheduler: watches unscheduled pods, applies filtering (node selectors, affinity, "
            "resource requirements) then scores remaining nodes. "
            "Controller Manager runs reconciliation loops — Deployment controller "
            "continuously reconciles desired state vs. actual state. "
            "kubelet on each node watches its assigned pods and manages container lifecycle. "
            "Service mesh (Istio/Linkerd) adds L7 routing, mTLS, observability via sidecar proxies. "
            "Key trade-off: etcd is the scalability bottleneck — clusters capped at ~5K nodes "
            "to keep etcd write latency below 10ms; large fleets shard into multiple clusters."
        ),
        "tags": ["kubernetes", "containers", "orchestration", "cloud", "devops", "etcd"],
        "reference_url": "https://kubernetes.io/blog/",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # STORAGE & FILES
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Google Drive",
        "slug": "google-drive",
        "description": "Cloud file storage with 3B+ users and real-time collaborative editing",
        "design_type": "HLD",
        "key_components": [
            "Block Storage Service", "Metadata Service (Spanner)", "Sync Service",
            "Conflict Resolution (OT/CRDT)", "Notification Service (WebSocket/SSE)",
            "Deduplication Service", "Viewer Service", "Sharing/ACL Service"
        ],
        "architecture_summary": (
            "Files split into 256KB blocks — each block stored with content hash for deduplication. "
            "Only modified blocks uploaded on sync (delta sync). "
            "Spanner for metadata: strong consistency + global distribution for file hierarchy. "
            "Real-time collaboration (Docs/Sheets/Slides): Operational Transformation (OT) "
            "for character-level merge; server acts as arbiter for transform sequencing. "
            "Sync conflicts: last-writer-wins for binary files; OT/CRDT for collaborative docs. "
            "Notification service pushes file change events to all devices via WebSocket. "
            "Deduplication: blocks with same SHA-256 stored once — saves storage for common files. "
            "Key trade-off: block-level deduplication requires computing hashes on client side "
            "(CPU cost) before upload — worthwhile for storage savings at billions of files."
        ),
        "tags": ["storage", "sync", "files", "cloud", "dedup", "real-time", "collaboration"],
        "reference_url": "https://systeminterview.com/design-google-drive.php",
    },
    {
        "name": "Dropbox",
        "slug": "dropbox",
        "description": "File sync SaaS with 700M registered users and 4B+ GB stored",
        "design_type": "HLD",
        "key_components": [
            "Block Server", "Metadata Server (edgestore)", "Sync Client (desktop/mobile)",
            "Notification Service (long-poll)", "Magic Pocket (block storage)",
            "Paper (collaborative docs)", "Business Admin Console"
        ],
        "architecture_summary": (
            "Magic Pocket: custom-built exabyte-scale block storage — "
            "migrated away from S3 in 2016 to reduce costs (90% of data in Magic Pocket). "
            "Block-level content-addressed storage: file → SHA-256 chunked blocks → stored once. "
            "Delta sync: only changed blocks are uploaded, not entire files. "
            "Edgestore: distributed key-value store for file/folder metadata. "
            "Sync client uses long-polling for change notification (not WebSocket) — "
            "server holds request open until change occurs, then responds. "
            "Python backend (originally) → Rust and Go for performance-critical paths. "
            "Key trade-off: building Magic Pocket required massive engineering investment "
            "but saved ~$75M/year vs S3 at Dropbox's scale."
        ),
        "tags": ["storage", "sync", "files", "dedup", "delta-sync", "desktop", "block-storage"],
        "reference_url": None,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # MAPS & LOCATION
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Google Maps",
        "slug": "google-maps",
        "description": "Mapping platform with 1B+ monthly users, Street View, and real-time traffic",
        "design_type": "HLD",
        "key_components": [
            "Tile Server (raster + vector tiles)", "Route Planning (Dijkstra/A* on road graph)",
            "Real-Time Traffic (anonymous GPS aggregation)", "Street View (panorama storage)",
            "Places API (200M+ POIs)", "Geocoding Service", "Maps API (SDK/embed)",
            "ETA ML Model"
        ],
        "architecture_summary": (
            "Road graph: 1B+ nodes (intersections), 2B+ edges (road segments) — "
            "stored as compressed adjacency list, partitioned geographically. "
            "Tile server: raster tiles pre-rendered at 21 zoom levels, "
            "vector tiles computed on-demand (client renders). "
            "Real-time traffic: billions of GPS pings/day from Android devices → "
            "aggregated into traffic speed per road segment → "
            "used in routing to find fastest path (modified Dijkstra with traffic weights). "
            "ETA model: gradient boosted trees on historical + real-time traffic, time of day, events. "
            "Street View: 80B+ panoramic photos stored in Spanner + Colossus. "
            "Key trade-off: vector tiles transfer less data but require more client CPU for rendering — "
            "raster tiles are simpler but bandwidth-heavy at high zoom."
        ),
        "tags": ["maps", "geo", "routing", "real-time", "traffic", "location", "tiles"],
        "reference_url": None,
    },
    {
        "name": "Waze",
        "slug": "waze",
        "description": "Community-based GPS navigation with real-time road incident reporting",
        "design_type": "HLD",
        "key_components": [
            "Map Editing Service (Waze Map Editor)", "Real-Time Event Service",
            "Route Calculation Service", "Traffic Model (crowdsourced + ML)",
            "Carpool Service", "Ads Platform (zero-speed advertising)",
            "Alert Service (police, hazards)", "SDK Integration"
        ],
        "architecture_summary": (
            "Crowdsourced road graph: users can edit roads, add POIs, report incidents — "
            "edits versioned and quality-controlled via ML + community moderators. "
            "Real-time event system: road alerts (police traps, accidents, closures) reported "
            "by drivers → validated against GPS speed anomalies → broadcast to nearby drivers. "
            "Route calculation: modified Dijkstra incorporating crowdsourced travel times, "
            "recalculated live as new data arrives. "
            "Zero-speed advertising: only shows ads when car is stopped (traffic light) — "
            "uses GPS speed to trigger ad display. "
            "Integrated with Google infrastructure post-acquisition (2013). "
            "Key trade-off: community editing scales map coverage cheaply but requires "
            "moderation to prevent vandalism — trust score system for contributors."
        ),
        "tags": ["maps", "geo", "routing", "real-time", "crowdsourced", "community", "navigation"],
        "reference_url": None,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # AI / ML PLATFORMS
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "OpenAI API / ChatGPT",
        "slug": "openai-api",
        "description": "LLM inference platform serving 100M+ users with GPT-4 and custom models",
        "design_type": "HLD",
        "key_components": [
            "API Gateway (rate limiting, auth)", "Inference Cluster (H100 GPUs)",
            "Token Streaming (SSE)", "Context Window Management",
            "Function Calling / Tool Use", "Fine-tuning Service",
            "Embeddings Service", "Moderation API"
        ],
        "architecture_summary": (
            "Inference: LLMs run on GPU clusters (NVIDIA H100/A100) with tensor parallelism "
            "(model split across multiple GPUs) and pipeline parallelism. "
            "Auto-regressive decoding: each token generated sequentially (1-10ms/token). "
            "KV-Cache: attention key/value tensors cached between tokens in a conversation "
            "to avoid recomputing previous context. "
            "Streaming: tokens streamed via SSE (Server-Sent Events) as generated "
            "to reduce perceived latency. "
            "Rate limiting: token bucket per API key (TPM + RPM limits). "
            "Context management: longer conversations truncated or summarized to fit context window. "
            "Embeddings: separate, cheaper models (Ada-002) for vectorization. "
            "Key trade-off: larger context windows need O(N²) attention compute — "
            "requires flash attention, sparse attention, or sliding window tricks."
        ),
        "tags": ["ai", "llm", "inference", "gpu", "streaming", "api", "ml"],
        "reference_url": None,
    },
    {
        "name": "Recommendation System (Generic)",
        "slug": "recommendation-system",
        "description": "General-purpose recommendation system design covering Netflix/Amazon/Spotify patterns",
        "design_type": "HLD",
        "key_components": [
            "Candidate Generation (retrieval)", "Scoring/Ranking Model",
            "Feature Store (Venice/Feast)", "A/B Testing Framework",
            "Offline Training Pipeline (Spark)", "Online Serving (low-latency inference)",
            "Feedback Loop (implicit/explicit signals)", "Diversity/Freshness Filters"
        ],
        "architecture_summary": (
            "Two-stage architecture universal across major recommenders: "
            "Stage 1 — Retrieval/Candidate Generation: "
            "fast retrieval of top-K candidates from millions of items "
            "using ALS (Alternating Least Squares), two-tower embeddings, or BM25 text match. "
            "ANN (Approximate Nearest Neighbor) index (FAISS/ScaNN) for embedding lookup. "
            "Stage 2 — Ranking: "
            "computationally expensive feature-rich model (GBDT, DNN) scores each candidate; "
            "features include user history, item metadata, context (time, device). "
            "Feature Store: pre-computed features served at <10ms latency (online) "
            "and stored for training (offline). "
            "Feedback loop: implicit signals (clicks, watch time, purchases) continuously "
            "retrain models (near-real-time or daily). "
            "Key trade-off: two-stage trades accuracy (retrieval may miss ideal items) "
            "for scalability (can't run heavy ranker on all items)."
        ),
        "tags": ["ml", "recommendation", "personalization", "feature-store", "ranking", "two-stage"],
        "reference_url": None,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # FINANCE & CRYPTO
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Coinbase",
        "slug": "coinbase",
        "description": "Crypto exchange with $80B+ in assets on platform and 110M verified users",
        "design_type": "HLD",
        "key_components": [
            "Order Matching Engine", "Wallet Service (hot/cold)", "Market Data Feed",
            "Settlement Service", "Regulatory Compliance (AML/KYC)", "Prime Broker",
            "Custody (institutional)", "Coinbase NFT Marketplace"
        ],
        "architecture_summary": (
            "Order matching engine: in-memory order book with price-time priority FIFO matching. "
            "Must be single-threaded (or carefully synchronized) to guarantee ordering determinism. "
            "Hot wallet: <5% of crypto in hot wallets (online, immediate access); "
            "95%+ in cold storage (air-gapped hardware) for security. "
            "Multi-sig cold wallet: requires M-of-N key holders to sign transactions. "
            "Market data: publish order book updates and trade executions via WebSocket feed "
            "at sub-millisecond latency. "
            "Blockchain node infrastructure: full nodes for each supported blockchain — "
            "listens for confirmed transactions. "
            "AML/KYC: transaction graph analysis to detect money laundering patterns. "
            "Key trade-off: cold storage security vs. liquidity — "
            "need instant withdrawals but can't have all funds in hot wallet."
        ),
        "tags": ["crypto", "fintech", "exchange", "matching-engine", "blockchain", "security"],
        "reference_url": "https://www.coinbase.com/blog/engineering",
    },
    {
        "name": "Stock Exchange (Generic)",
        "slug": "stock-exchange",
        "description": "High-frequency trading exchange processing millions of orders/second with microsecond latency",
        "design_type": "HLD",
        "key_components": [
            "Order Gateway (FIX protocol)", "Order Matching Engine (in-memory)",
            "Market Data Publisher (OPRA/ITCH)", "Risk Engine (pre-trade checks)",
            "Settlement (T+2 DTCC)", "Surveillance System", "Colocation Services"
        ],
        "architecture_summary": (
            "Order flow: broker → FIX gateway → risk check → matching engine → confirmation. "
            "Matching engine: C++ in-memory order book; price-time priority; "
            "top exchanges process 1M+ orders/sec at <100 microsecond latency. "
            "FPGA acceleration: some exchanges use FPGAs to reduce parsing latency to nanoseconds. "
            "Market data: ITCH protocol (binary, UDP multicast) distributes trade/quote updates "
            "to all market participants simultaneously. "
            "Co-location: HFT firms pay $500K+/year to place servers in exchange data center "
            "to shave microseconds off round-trip latency. "
            "No traditional RDBMS in hot path — writes to persistent ring buffer (LMAX Disruptor). "
            "Key trade-off: fairness (sequential processing) vs. throughput — "
            "exchanges must process each order fairly, preventing certain HFT strategies."
        ),
        "tags": ["fintech", "trading", "low-latency", "matching-engine", "hft", "fix-protocol"],
        "reference_url": None,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # LOW-LEVEL DESIGN (LLD) EXAMPLES
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Rate Limiter",
        "slug": "rate-limiter",
        "description": "Distributed rate limiting preventing API abuse — Token Bucket, Sliding Window, Leaky Bucket",
        "design_type": "LLD",
        "key_components": [
            "Token Bucket Algorithm", "Sliding Window Log", "Fixed Window Counter",
            "Leaky Bucket (queue-based)", "Redis (distributed state)", "Counter Service",
            "Middleware Layer", "Rate Limit Headers (X-RateLimit-*)"
        ],
        "architecture_summary": (
            "Token Bucket: capacity C tokens, refilled at rate R/sec. "
            "Request consumes 1 token; rejected if bucket empty. "
            "Smooth bursts allowed up to capacity C. "
            "Implementation: Redis INCR + EXPIRE (fixed window) or Lua script for atomic check+consume. "
            "Sliding Window Log: store timestamp of each request in sorted set; "
            "count entries in [now-window, now]; reject if > limit. Accurate but memory-heavy. "
            "Sliding Window Counter: hybrid — use fixed window counts for current and previous window "
            "weighted by overlap % → approximation with O(1) memory. "
            "Distributed: use Redis CLUSTER for sharding rate counters across keys. "
            "Cell-based (Envoy): GCRA algorithm for smooth rate distribution. "
            "Key trade-off: Token Bucket allows bursts (good for APIs), "
            "Leaky Bucket smooths output (good for upstream service protection)."
        ),
        "tags": ["rate-limit", "distributed", "redis", "algorithm", "lld", "concurrency", "token-bucket"],
        "reference_url": None,
    },
    {
        "name": "URL Shortener",
        "slug": "url-shortener",
        "description": "URL shortening service (bit.ly/TinyURL) with analytics and custom aliases",
        "design_type": "LLD",
        "key_components": [
            "Hash Service (Base62 / Snowflake ID)", "Key-Value Store (Redis + DynamoDB)",
            "Redirect Service (301/302)", "Analytics Pipeline (Kafka + ClickHouse)",
            "Custom Alias Service", "Link Expiry (TTL)", "Spam/Malware Filter"
        ],
        "architecture_summary": (
            "Short URL generation strategies: "
            "1. MD5 hash of long URL → take first 7 chars (collision risk). "
            "2. Auto-increment ID → Base62 encode (7 chars = 62^7 = 3.5T URLs). "
            "3. Distributed Snowflake ID → Base62 (no coordination needed). "
            "Redirect: HTTP 301 (permanent, browser caches) vs 302 (temporary, server always hit). "
            "Use 302 for analytics — each click hits server for counting. "
            "Store: Redis cache for hot URLs (LRU eviction); DynamoDB for persistence. "
            "Read:Write ratio ~100:1 (read-heavy after initial creation). "
            "Analytics: Kafka consumer logs each click with metadata → ClickHouse for OLAP queries. "
            "Custom aliases checked against blocklist (reserved words, existing slugs). "
            "Key trade-off: 301 saves server load but breaks analytics — "
            "business decision based on whether click tracking is needed."
        ),
        "tags": ["url", "shortener", "hash", "key-value", "lld", "base62", "redirect"],
        "reference_url": None,
    },
    {
        "name": "Parking Lot System",
        "slug": "parking-lot",
        "description": "Parking lot management system with spot allocation, ticketing, and payment",
        "design_type": "LLD",
        "key_components": [
            "Entry/Exit Gates", "Spot Allocation Service", "Ticket Service",
            "Payment Service", "Spot Status Tracker", "Notification Service",
            "Multi-level Support", "Vehicle Type Manager"
        ],
        "architecture_summary": (
            "Core entities: ParkingLot, Level, Spot (Compact/Large/Handicapped), "
            "Ticket, Vehicle (Motorcycle/Car/Truck), Payment. "
            "Spot allocation: first-fit strategy per vehicle type and level; "
            "nearest-to-entrance optimization using priority queue. "
            "Concurrency: atomic test-and-set for spot reservation (Redis SETNX or DB row lock). "
            "Ticket: created at entry with timestamp and spot ID; closed at exit with fee calc. "
            "Fee: hourly rate × hours rounded up; discount for validation. "
            "State machine: ENTRY → PARKED → EXIT. "
            "Design patterns: Singleton (ParkingLot), Strategy (pricing), Factory (spot type). "
            "Key trade-off: centralized vs. distributed gate processing — "
            "centralized is simpler but single point of failure for gate operations."
        ),
        "tags": ["lld", "oop", "design-patterns", "concurrency", "state-machine", "parking"],
        "reference_url": None,
    },
    {
        "name": "Distributed Cache",
        "slug": "distributed-cache",
        "description": "In-memory distributed cache (Redis/Memcached) design with eviction, consistency, and clustering",
        "design_type": "LLD",
        "key_components": [
            "Cache Node (in-memory hash table)", "Consistent Hashing Ring",
            "LRU Eviction Policy", "Write-Through / Write-Around / Write-Back",
            "Replication (primary-replica)", "Cache Stampede Prevention",
            "Hot Key Detection", "TTL Management"
        ],
        "architecture_summary": (
            "Consistent hashing: each node owns a range of the hash ring; "
            "adding/removing nodes only remaps ~K/N keys (K = keys, N = nodes). "
            "Virtual nodes: each physical node represents multiple ring positions → "
            "better load distribution. "
            "LRU eviction: doubly-linked list + hash map → O(1) get and put. "
            "Cache stampede: when popular key expires, all requests miss simultaneously → "
            "use mutex lock on miss (only one request fetches from DB) + "
            "probabilistic early expiry. "
            "Write strategies: "
            "Write-through: write cache + DB together (consistent, slower writes). "
            "Write-around: write DB only, cache on read (saves cache bandwidth for writes). "
            "Write-back: write cache first, flush to DB async (fast writes, data loss risk). "
            "Hot key sharding: popular keys replicated to multiple cache nodes. "
            "Key trade-off: large cache reduces DB load but increases memory cost; "
            "TTL too short → high miss rate; too long → stale data."
        ),
        "tags": ["cache", "redis", "distributed", "lru", "consistent-hashing", "lld", "in-memory"],
        "reference_url": None,
    },
    {
        "name": "Notification System",
        "slug": "notification-system",
        "description": "Multi-channel notification platform (push/email/SMS) with delivery guarantees",
        "design_type": "LLD",
        "key_components": [
            "Notification API", "Message Queue (Kafka)", "Channel Workers",
            "Push (APNs/FCM)", "Email (SendGrid/SES)", "SMS (Twilio)",
            "Delivery Tracker", "User Preference Store", "Retry Service"
        ],
        "architecture_summary": (
            "Architecture: pub/sub → channel workers → third-party providers. "
            "Flow: API enqueues notification to Kafka topic per channel type → "
            "worker consumes, queries user device tokens/contact, calls provider API. "
            "User preferences: per-channel, per-type opt-ins stored in Redis for fast lookup. "
            "Idempotency: notification_id prevents duplicate sends on worker restart. "
            "Retry with exponential backoff: APNs failures retried up to 3× over 24h. "
            "Dead Letter Queue: failed after retries → alert engineering. "
            "APNs/FCM tokens can be stale — handle 'unregistered device' errors "
            "by removing token from device table. "
            "Rate limiting: respect provider limits (APNs: 2500 notifs/sec per bundle). "
            "Priority queuing: transactional > marketing for queue processing order. "
            "Key trade-off: at-least-once delivery (duplicates possible) vs. "
            "exactly-once (requires expensive 2PC with provider)."
        ),
        "tags": ["notifications", "push", "email", "sms", "kafka", "lld", "idempotency"],
        "reference_url": None,
    },
    {
        "name": "Ticket Booking System",
        "slug": "ticket-booking",
        "description": "High-concurrency event ticket booking (concerts, flights) with seat locking",
        "design_type": "LLD",
        "key_components": [
            "Seat Map Service", "Seat Lock Service (Redis TTL)", "Booking Service",
            "Payment Service", "Queue Management (Virtual Waiting Room)",
            "Inventory Service", "E-Ticket Generator (PDF/QR)", "Notification Service"
        ],
        "architecture_summary": (
            "Core challenge: prevent double-booking under high concurrency "
            "(Taylor Swift tickets: 2M+ concurrent users for 30K seats). "
            "Seat lock: when user selects seat → acquire Redis lock (SETNX with 10-min TTL); "
            "lock released on payment or timeout. "
            "Virtual waiting room: at high load, queue excess users and admit in batches "
            "(Ticketmaster Queue-It pattern). "
            "Pessimistic locking in DB for final booking transaction (SELECT FOR UPDATE). "
            "Inventory tracking: separate seat_status table with states: AVAILABLE, HELD, BOOKED. "
            "Flash sale handling: pre-generate reservation tokens; validate tokens at booking. "
            "E-ticket: PDF generated async post-payment; QR code = signed JWT (prevents forgery). "
            "Key trade-off: short lock TTL (user can lose seat while filling payment form) "
            "vs. long TTL (seats locked by abandoned sessions reduce availability)."
        ),
        "tags": ["booking", "concurrency", "redis", "locking", "lld", "inventory", "payments"],
        "reference_url": None,
    },
    {
        "name": "Chat Application",
        "slug": "chat-application",
        "description": "Real-time 1:1 and group messaging system with presence and message persistence",
        "design_type": "LLD",
        "key_components": [
            "WebSocket Server", "Message Store (Cassandra)", "Presence Service (Redis Pub/Sub)",
            "Group Chat Fan-out", "Message Queue (Kafka)", "Read Receipts",
            "Message Search (Elasticsearch)", "Media Upload Service"
        ],
        "architecture_summary": (
            "Connection management: each user maintains persistent WebSocket connection "
            "to a chat server. Connection mapping (user_id → server_id) stored in Redis. "
            "Message flow: Sender → WebSocket Server → Kafka → Consumer → Recipient WebSocket Server. "
            "Kafka decouples send from deliver; guarantees ordering per partition (per conversation). "
            "Storage: Cassandra with partition key = conversation_id, "
            "clustering key = message_id (time-based) for efficient time-range queries. "
            "Presence: Redis Pub/Sub for online/offline status; heartbeat every 30s. "
            "Group fan-out: for small groups (<500), fan out in consumer; "
            "large groups (>500), clients poll for new messages. "
            "Read receipts: delivered on WebSocket receipt; read on client viewport event. "
            "Key trade-off: WebSocket requires sticky sessions (user must connect to same server) — "
            "complicates horizontal scaling; use consistent hashing for server assignment."
        ),
        "tags": ["messaging", "websocket", "real-time", "cassandra", "kafka", "lld", "presence"],
        "reference_url": None,
    },
    {
        "name": "Search Autocomplete",
        "slug": "search-autocomplete",
        "description": "Typeahead suggestion system serving 1B+ queries/day with sub-100ms latency",
        "design_type": "LLD",
        "key_components": [
            "Trie Data Structure", "Top-K Heap per Node", "Query Log Aggregator",
            "Suggestion API", "Cache Layer (Redis)", "Offline Job (Hadoop/Spark)",
            "Filter Service (profanity, spam)", "A/B Test Framework"
        ],
        "architecture_summary": (
            "Trie with frequency counts: each node stores top-K (e.g., K=5) most frequent "
            "completions for that prefix → O(P) lookup time where P = prefix length. "
            "Build pipeline: query logs → Spark aggregation (word count) → "
            "trie rebuild weekly → swap via atomic pointer update (no downtime). "
            "Real-time updates: hot trending queries (news events) handled with "
            "Bloom filter + separate real-time trending trie refreshed every 5 min. "
            "Serving: prefix → Redis GET (trie serialized per prefix) → sub-1ms. "
            "Cache: preload top-N prefixes (all single and double-character prefixes cover 80%+ of traffic). "
            "Shard trie by first 1-2 characters of prefix for distribution. "
            "Filter: blocklist + ML model for profanity filtering post-lookup. "
            "Key trade-off: trie gives O(P) lookup but is memory-intensive; "
            "alternative: Ternary Search Tree or radix tree for compressed storage."
        ),
        "tags": ["search", "trie", "autocomplete", "typeahead", "lld", "redis", "algorithm"],
        "reference_url": None,
    },
    {
        "name": "Distributed Message Queue",
        "slug": "distributed-message-queue",
        "description": "Kafka-style distributed log with pub/sub, consumer groups, and exactly-once semantics",
        "design_type": "LLD",
        "key_components": [
            "Topic (logical stream)", "Partition (ordered log)",
            "Producer (with partitioner)", "Consumer Group (parallel consumption)",
            "Broker (storage + replication)", "ZooKeeper / KRaft (metadata)",
            "ISR (In-Sync Replicas)", "Offset Management"
        ],
        "architecture_summary": (
            "Log-structured storage: append-only partition log → O(1) writes regardless of size. "
            "Partitions: topic split into P partitions → P consumers in a group can read in parallel. "
            "Replication: each partition has 1 leader + N-1 followers; ISR must contain all live replicas. "
            "Producer acks: acks=0 (fire-and-forget), acks=1 (leader only), acks=all (ISR quorum). "
            "Consumer offset: consumers commit offsets to Kafka __consumer_offsets topic → "
            "crash recovery resumes from committed offset. "
            "At-least-once default (may re-consume messages after crash). "
            "Exactly-once: producer idempotency (sequence numbers) + consumer transactional API. "
            "Retention: configurable time (7 days) or size limit — old segments deleted. "
            "Key trade-off: more partitions → higher throughput but more file handles + "
            "longer leader election time on broker failure."
        ),
        "tags": ["messaging", "kafka", "pub-sub", "distributed", "log", "lld", "consumer-groups"],
        "reference_url": None,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # ADDITIONAL HLD SYSTEMS
    # ═══════════════════════════════════════════════════════════════════════
    {
        "name": "Twitter/X Direct Messages",
        "slug": "twitter-dms",
        "description": "Twitter DM system supporting group chats, reactions, and 30B+ messages",
        "design_type": "LLD",
        "key_components": [
            "Conversation Service", "Message Store (Manhattan)", "Fan-out Worker",
            "Encryption Service (E2E option)", "Media Service", "Notification Service",
            "Inbox Service", "Conversation Metadata (Redis)"
        ],
        "architecture_summary": (
            "DMs stored in Manhattan (Twitter's distributed key-value store). "
            "Conversation model: each conversation has an ID; messages appended as log. "
            "Fan-out: for group DMs, message written to each participant's inbox "
            "(separate from public timeline fan-out). "
            "Inbox: per-user sorted set in Redis with (timestamp, conversation_id) — "
            "recent conversations float to top. "
            "E2E Encryption (2023): Signal Protocol based; keys generated client-side. "
            "Read receipts: updated via long-polling or WebSocket. "
            "Spam filtering: ML model on message content + sender reputation at write time. "
            "Key trade-off: storing messages in sender's AND recipient's inbox "
            "doubles storage but enables fast per-user inbox reads without cross-partition joins."
        ),
        "tags": ["messaging", "twitter", "dms", "lld", "encryption", "manhattan", "inbox"],
        "reference_url": None,
    },
    {
        "name": "Netflix Prize / Collaborative Filtering",
        "slug": "collaborative-filtering",
        "description": "Matrix factorization and collaborative filtering for movie/product recommendations",
        "design_type": "LLD",
        "key_components": [
            "User-Item Matrix", "ALS (Alternating Least Squares)", "SVD Decomposition",
            "User Embeddings (latent factors)", "Item Embeddings",
            "Nearest Neighbor Search (FAISS)", "Implicit Feedback Handler",
            "Cold Start Handler"
        ],
        "architecture_summary": (
            "Matrix factorization decomposes R (users × items) into U (users × k) × V (items × k)^T "
            "where k = latent factor dimensionality (e.g., k=64). "
            "ALS: fix U, solve for V (linear regression per item); fix V, solve for U. "
            "Repeat until convergence (~20 iterations). Parallelizable. "
            "Implicit feedback (clicks, views) uses confidence-weighted matrix. "
            "Online serving: pre-compute user embeddings offline; "
            "at query time, find top-K nearest item embeddings via FAISS ANN index. "
            "Cold start strategies: "
            "New user → popularity-based or content-based (metadata). "
            "New item → content embeddings (NLP/image features). "
            "Bandits (ε-greedy/Thompson) for exploration of new items. "
            "Key trade-off: ALS scales to millions of users/items but "
            "requires distributed compute (Spark MLlib) for matrix operations at scale."
        ),
        "tags": ["ml", "recommendation", "matrix-factorization", "als", "lld", "embeddings", "cold-start"],
        "reference_url": None,
    },
    {
        "name": "Web Crawler",
        "slug": "web-crawler",
        "description": "Distributed web crawler (Googlebot-style) indexing billions of URLs at scale",
        "design_type": "HLD",
        "key_components": [
            "URL Frontier (priority queue)", "Fetcher Service (async HTTP)",
            "DNS Resolver Cache", "robots.txt Cache", "Content Extractor",
            "Link Extractor", "Bloom Filter (visited URLs)", "Content Store (S3)"
        ],
        "architecture_summary": (
            "URL Frontier: priority queue ranking URLs by freshness and importance (PageRank estimate). "
            "Bloom filter: probabilistic membership check for visited URLs — "
            "O(1) lookup, ~10 bits/element for 1% false positive rate. "
            "Politeness: per-domain queue with delay between requests — "
            "respect robots.txt crawl-delay directive; cap at N requests/domain/sec. "
            "Fetcher: async HTTP clients (Scrapy/custom); fetch concurrently but rate-limit per domain. "
            "DNS cache: repeated resolution expensive; cache TTL-respecting DNS lookups. "
            "Content deduplication: SimHash or MinHash to detect near-duplicate pages. "
            "Distributed: URL frontier sharded by URL hash across N crawler nodes. "
            "Content stored in S3 (raw HTML) + Bigtable (extracted metadata). "
            "Key trade-off: BFS (breadth-first) discovers links widely but may crawl low-quality pages; "
            "DFS risks getting trapped in deep but unimportant sites."
        ),
        "tags": ["crawler", "web", "distributed", "bloom-filter", "search", "hld", "politeness"],
        "reference_url": None,
    },
    {
        "name": "Content Delivery Network (CDN)",
        "slug": "cdn",
        "description": "Global CDN architecture serving static/dynamic content with <50ms latency worldwide",
        "design_type": "HLD",
        "key_components": [
            "Edge POP (Point of Presence)", "Origin Server", "Cache Hierarchy (L1/L2)",
            "Anycast Routing", "Cache Invalidation Service", "SSL Termination",
            "DDoS Protection Layer", "Real-Time Analytics"
        ],
        "architecture_summary": (
            "Anycast: CDN edge servers announce same IP prefix globally — "
            "BGP routes user to geographically nearest POP. "
            "Cache hierarchy: L1 edge cache (per-POP) → L2 regional cache → origin. "
            "Hit ratio optimization: consistent hash routing sends same URL to same edge server. "
            "Cache key: URL + Vary header fields (Accept-Encoding, Accept-Language). "
            "Cache invalidation: CDN-specific (Cloudflare Cache Purge API); "
            "immediate purge propagated to all POPs via Kafka-like internal queue. "
            "SSL termination at edge: reduces origin load; enables HTTP/2 and QUIC. "
            "Dynamic content: cache-bypass for personalized or POST requests; "
            "edge side includes (ESI) for partial page caching. "
            "DDoS: absorb at edge (rate limiting, bot fingerprinting, IP reputation). "
            "Key trade-off: aggressive caching (long TTLs) reduces origin load but "
            "requires complex invalidation for stale content."
        ),
        "tags": ["cdn", "caching", "networking", "anycast", "hld", "performance", "ddos"],
        "reference_url": None,
    },
    {
        "name": "API Gateway",
        "slug": "api-gateway",
        "description": "API Gateway pattern handling auth, rate limiting, routing, and request transformation",
        "design_type": "LLD",
        "key_components": [
            "Request Router", "Auth Service (JWT/OAuth)", "Rate Limiter",
            "Load Balancer", "Service Discovery (Consul/Eureka)", "Circuit Breaker (Hystrix)",
            "Request/Response Transformer", "API Analytics Dashboard"
        ],
        "architecture_summary": (
            "Single entry point for all client-to-service traffic — eliminates N×M connections. "
            "Request pipeline: TLS termination → Auth (JWT verify, OAuth token exchange) → "
            "Rate limit check → Route resolution → Load balance → Forward → Transform response. "
            "Service discovery: gateway queries Consul/Eureka for live backend endpoints. "
            "Circuit breaker: if backend error rate > threshold (e.g., 50% in 10s window), "
            "open circuit and return fallback response immediately. "
            "Request transformation: request aggregation (BFF pattern), "
            "protocol translation (REST ↔ gRPC), schema validation. "
            "Kong/AWS API GW/Nginx as common implementations. "
            "Performance: gateway adds ~1-5ms overhead per request; critical to optimize auth path. "
            "Key trade-off: centralized gateway = single point of failure — "
            "mitigate with active-active HA deployment and health checks."
        ),
        "tags": ["api-gateway", "microservices", "auth", "rate-limit", "lld", "routing", "circuit-breaker"],
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

    logger.info(
        f"✅ Seeded {inserted_count} new systems, "
        f"updated {len(FAMOUS_SYSTEMS_DATA) - inserted_count} existing"
    )
    return inserted_count


def get_all_seed_data() -> List[Dict[str, Any]]:
    """Get all seed data (for testing/caching)."""
    return FAMOUS_SYSTEMS_DATA.copy()

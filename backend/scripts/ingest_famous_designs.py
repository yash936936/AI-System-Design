"""
ingest_famous_designs.py
========================
Seeds the `famous_designs` SQL table AND the ChromaDB `famous_designs`
vector collection with rich, curated data for 20 famous system designs.

Run once (or re-run safely — upsert logic prevents duplicates):
    cd backend
    python -m scripts.ingest_famous_designs

Requires:
  - GEMINI_API_KEY in .env (or env var) for vector indexing.
  - Database already initialised (app startup calls init_db automatically;
    run the FastAPI server at least once before running this script, or
    call init_db() explicitly below).
"""

import asyncio
import sys
import os
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.core.config import get_settings
from app.core.gemini import gemini_embed
from app.db.models import FamousDesign
from app.db.session import AsyncSessionLocal
from app.services.vector_store import get_famous_designs_collection

settings = get_settings()

# ── 20 famous system designs ──────────────────────────────────────────────────

FAMOUS_DESIGNS = [
    # ── 1. Netflix ─────────────────────────────────────────────────────────────
    {
        "system_name": "netflix",
        "title": "Netflix Video Streaming Architecture",
        "diagram_json": {
            "nodes": [
                "Client Apps", "AWS CloudFront CDN", "Open Connect Appliance",
                "Zuul API Gateway", "Eureka Service Discovery",
                "Video Processing Pipeline (Encoding Farm)",
                "AWS S3 (Raw Storage)", "Cassandra (Metadata)",
                "Recommendation Engine (Spark ML)",
                "Hystrix Circuit Breaker", "Kafka Event Bus",
            ],
            "edges": [
                {"from": "Client Apps", "to": "AWS CloudFront CDN"},
                {"from": "AWS CloudFront CDN", "to": "Open Connect Appliance"},
                {"from": "Client Apps", "to": "Zuul API Gateway"},
                {"from": "Zuul API Gateway", "to": "Recommendation Engine (Spark ML)"},
                {"from": "Video Processing Pipeline (Encoding Farm)", "to": "AWS S3 (Raw Storage)"},
                {"from": "AWS S3 (Raw Storage)", "to": "Open Connect Appliance"},
                {"from": "Kafka Event Bus", "to": "Recommendation Engine (Spark ML)"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Video Ingestion & Transcoding",
                "CDN & Last-Mile Delivery (Open Connect)",
                "Microservices & API Gateway (Zuul + Eureka)",
                "Recommendation Engine (Collaborative Filtering + Spark)",
                "Resilience Patterns (Hystrix, Chaos Monkey)",
                "Data Pipeline (Kafka + Apache Flink)",
            ]
        },
        "key_insights": [
            "Transcodes each video into 1200+ bitrate/resolution variants for adaptive streaming (HLS/DASH).",
            "Open Connect Appliances are ISP-embedded CDN boxes; 95%+ of traffic served from them, not AWS.",
            "Uses Chaos Monkey / Simian Army to continuously inject failures and test resilience.",
            "Hystrix circuit breaker pattern prevents cascading failures across 700+ microservices.",
            "Recommendation engine accounts for ~80% of hours streamed; uses matrix factorization + deep learning.",
            "Zuul gateway handles dynamic routing, load shedding, and canary releases.",
            "Cassandra used for highly available, geo-replicated viewing history and metadata.",
            "Kafka ingests billions of events/day for real-time analytics and offline training pipelines.",
        ],
        "sources": [
            "netflixtechblog.com",
            "highscalability.com/netflix",
            "aws.amazon.com/solutions/case-studies/netflix",
        ],
    },

    # ── 2. Twitter / X ─────────────────────────────────────────────────────────
    {
        "system_name": "twitter",
        "title": "Twitter (X) Timeline & Fan-out Architecture",
        "diagram_json": {
            "nodes": [
                "Client", "Load Balancer", "Tweet Service",
                "Fan-out Service", "Redis Timeline Cache",
                "Manhattan (Key-Value Store)", "Graph Service",
                "Trend Service", "Search (Blender / Earlybird)",
                "Notification Service", "Media Service (S3 + CDN)",
            ],
            "edges": [
                {"from": "Client", "to": "Load Balancer"},
                {"from": "Load Balancer", "to": "Tweet Service"},
                {"from": "Tweet Service", "to": "Fan-out Service"},
                {"from": "Fan-out Service", "to": "Redis Timeline Cache"},
                {"from": "Fan-out Service", "to": "Manhattan (Key-Value Store)"},
                {"from": "Client", "to": "Redis Timeline Cache", "label": "read home timeline"},
                {"from": "Tweet Service", "to": "Trend Service"},
                {"from": "Tweet Service", "to": "Search (Blender / Earlybird)"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Tweet Ingestion & Storage",
                "Fan-out Service (Push vs Pull)",
                "Home Timeline (Redis Cache)",
                "Graph Service (Follower/Following)",
                "Trending Topics",
                "Search (Earlybird Real-Time Index)",
                "Media Upload & CDN",
            ]
        },
        "key_insights": [
            "Fan-out-on-write for normal users (<= 10k followers): tweet is pushed to all followers' Redis timeline caches at post time.",
            "Fan-out-on-read for celebrities (>10k followers): hot accounts are pulled and merged at read time to avoid fan-out storms.",
            "Redis timeline cache stores the most recent 800 tweet IDs per user; older tweets are fetched from Manhattan.",
            "Manhattan is Twitter's in-house distributed key-value store, optimised for SSD and multi-datacenter replication.",
            "Earlybird is a modified Lucene-based real-time search index; new tweets appear in search within ~15 seconds.",
            "Flockdb (graph DB) stores follower/following relationships as an adjacency list sharded by user ID.",
            "Read-to-write ratio is ~100:1; caching is the primary scaling lever.",
        ],
        "sources": [
            "blog.twitter.com/engineering",
            "highscalability.com/twitter",
            "systemdesignschool.io/twitter",
        ],
    },

    # ── 3. Uber ────────────────────────────────────────────────────────────────
    {
        "system_name": "uber",
        "title": "Uber Ride-Matching & Dispatch Architecture",
        "diagram_json": {
            "nodes": [
                "Rider App", "Driver App", "API Gateway",
                "Trip Service", "Dispatch Service",
                "Location Service", "Geospatial Index (H3 + S2)",
                "Surge Pricing Engine", "Payment Service",
                "Notification Service", "Kafka", "Cassandra",
                "Redis Geo Cache",
            ],
            "edges": [
                {"from": "Rider App", "to": "API Gateway"},
                {"from": "Driver App", "to": "Location Service"},
                {"from": "Location Service", "to": "Redis Geo Cache"},
                {"from": "Location Service", "to": "Geospatial Index (H3 + S2)"},
                {"from": "API Gateway", "to": "Dispatch Service"},
                {"from": "Dispatch Service", "to": "Geospatial Index (H3 + S2)"},
                {"from": "Dispatch Service", "to": "Surge Pricing Engine"},
                {"from": "Dispatch Service", "to": "Trip Service"},
                {"from": "Trip Service", "to": "Cassandra"},
                {"from": "Trip Service", "to": "Kafka"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Location Ingestion & Geo-Indexing",
                "Driver-Rider Matching (Dispatch)",
                "Surge Pricing Computation",
                "Trip Lifecycle Management",
                "Real-Time Notifications",
                "Payments & Receipts",
            ]
        },
        "key_insights": [
            "Drivers send GPS pings every 4 seconds; Location Service writes to Redis Geo (geohash-partitioned).",
            "H3 hexagonal geohash grid divides cities into cells; dispatch queries adjacent cells for nearby drivers.",
            "Surge pricing runs on a separate, eventually-consistent service to avoid blocking dispatch latency.",
            "ETA model is a gradient-boosted tree trained on historical trip data; re-evaluated every 30 seconds.",
            "Ringpop (consistent hashing) routes each city's dispatch traffic to a single shard to avoid coordination.",
            "Kafka fan-out powers analytics, fraud detection, and driver earnings calculation asynchronously.",
            "Cassandra stores immutable trip records; wide rows keyed by driver_id enable efficient history queries.",
        ],
        "sources": [
            "eng.uber.com",
            "highscalability.com/uber",
            "uber.com/en-US/blog/engineering",
        ],
    },

    # ── 4. WhatsApp ────────────────────────────────────────────────────────────
    {
        "system_name": "whatsapp",
        "title": "WhatsApp Messaging Architecture",
        "diagram_json": {
            "nodes": [
                "Client (iOS/Android)", "Load Balancer",
                "Connection Service (XMPP over TCP)",
                "Message Router", "Message Store (Mnesia + Riak)",
                "Media Server (S3 + CDN)", "Push Notification Gateway",
                "Presence Service", "End-to-End Encryption (Signal Protocol)",
                "Group Service", "User Registry (Mnesia)",
            ],
            "edges": [
                {"from": "Client (iOS/Android)", "to": "Connection Service (XMPP over TCP)"},
                {"from": "Connection Service (XMPP over TCP)", "to": "Message Router"},
                {"from": "Message Router", "to": "Message Store (Mnesia + Riak)"},
                {"from": "Message Router", "to": "Push Notification Gateway"},
                {"from": "Client (iOS/Android)", "to": "Media Server (S3 + CDN)", "label": "media upload"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Connection Management (XMPP/WebSocket)",
                "End-to-End Encryption (Signal Protocol)",
                "Message Store & Delivery Guarantees",
                "Media Upload & CDN",
                "Presence & Online Status",
                "Group Messaging",
                "Push Notifications (APNs / FCM)",
            ]
        },
        "key_insights": [
            "2 million connections per server using Erlang/OTP's lightweight process model (each connection = 1 Erlang process).",
            "Signal Protocol provides end-to-end encryption; messages are encrypted client-side; server sees only ciphertext.",
            "Store-and-forward: messages stored on server until the recipient comes online; deleted after ACK.",
            "Mnesia (distributed Erlang DB) stores session state and user registry; Riak for durable message queues.",
            "Media is uploaded directly to S3; only the S3 URL is exchanged in the message payload (encrypted).",
            "At 50+ billion messages/day, WhatsApp ran with <60 engineers — Erlang's concurrency model is key.",
            "Group messages fan out to each member's individual queue rather than a shared group topic.",
        ],
        "sources": [
            "highscalability.com/whatsapp",
            "engineering.whatsapp.com",
            "wired.com/2015/09/whatsapp-serves-900-million-users-50-engineers",
        ],
    },

    # ── 5. YouTube ─────────────────────────────────────────────────────────────
    {
        "system_name": "youtube",
        "title": "YouTube Video Platform Architecture",
        "diagram_json": {
            "nodes": [
                "Client", "CDN (Google Global Cache)", "API Gateway",
                "Upload Service", "Transcoding Farm (Borg Jobs)",
                "Google Cloud Storage (GCS)", "Metadata Service (Spanner)",
                "Recommendation Engine (DNN)", "Search (ElasticSearch)",
                "Comment Service (Spanner)", "Analytics (BigQuery + Dataflow)",
                "Ads Service", "Notification Service",
            ],
            "edges": [
                {"from": "Client", "to": "CDN (Google Global Cache)"},
                {"from": "Client", "to": "Upload Service"},
                {"from": "Upload Service", "to": "Google Cloud Storage (GCS)"},
                {"from": "Google Cloud Storage (GCS)", "to": "Transcoding Farm (Borg Jobs)"},
                {"from": "Transcoding Farm (Borg Jobs)", "to": "CDN (Google Global Cache)"},
                {"from": "Client", "to": "Recommendation Engine (DNN)"},
                {"from": "Analytics (BigQuery + Dataflow)", "to": "Recommendation Engine (DNN)"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Video Upload & Ingestion",
                "Transcoding Pipeline",
                "CDN & Adaptive Streaming (MPEG-DASH / HLS)",
                "Metadata Storage (Spanner)",
                "Recommendation Engine (Deep Neural Networks)",
                "Search & Discovery",
                "Comments & Social Features",
                "Ads System",
                "Analytics (BigQuery)",
            ]
        },
        "key_insights": [
            "500 hours of video uploaded every minute; ingestion pipeline parallelises transcoding across thousands of Borg tasks.",
            "Each video transcoded into 10+ resolutions (144p–4K) and formats (VP9, H.264, AV1) for adaptive streaming.",
            "Google's private CDN (Global Cache) deployed in ISP data centres; 99%+ of video traffic bypasses public internet.",
            "Spanner (globally distributed SQL) stores video metadata with strong consistency and multi-region replication.",
            "Recommendation DNN trained on watch time, clicks, and explicit ratings; re-trained daily on petabytes of logs.",
            "MPEG-DASH with segment sizes of 2–10 seconds; clients request the next segment based on current bandwidth estimate.",
            "Comments stored in Spanner with interleaved rows for parent/reply hierarchy — O(1) fetch for a comment thread.",
        ],
        "sources": [
            "highscalability.com/youtube",
            "research.google/youtube-8m",
            "cloud.google.com/customers/youtube",
        ],
    },

    # ── 6. Instagram ───────────────────────────────────────────────────────────
    {
        "system_name": "instagram",
        "title": "Instagram Photo & Video Platform Architecture",
        "diagram_json": {
            "nodes": [
                "Client", "AWS ELB", "Django App Servers",
                "PostgreSQL (sharded)", "Cassandra (Feed / Activity)",
                "Redis (Follower Cache + Rate Limits)",
                "Amazon S3 + CloudFront CDN",
                "Celery Task Queue (RabbitMQ)",
                "Solr Search", "Notification Service",
                "Stories Service", "Reels Service",
            ],
            "edges": [
                {"from": "Client", "to": "AWS ELB"},
                {"from": "AWS ELB", "to": "Django App Servers"},
                {"from": "Django App Servers", "to": "PostgreSQL (sharded)"},
                {"from": "Django App Servers", "to": "Cassandra (Feed / Activity)"},
                {"from": "Django App Servers", "to": "Redis (Follower Cache + Rate Limits)"},
                {"from": "Client", "to": "Amazon S3 + CloudFront CDN", "label": "media"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Media Upload & Storage (S3 + CloudFront)",
                "Feed Generation (Fan-out on Write)",
                "PostgreSQL Sharding Strategy",
                "Cassandra for Activity & Notifications",
                "Redis Caching Layer",
                "Stories Architecture",
                "Reels (Short-form Video)",
                "Explore & Recommendation",
            ]
        },
        "key_insights": [
            "Originally launched with 3 engineers on AWS; scaled to 1B+ users while keeping Python/Django.",
            "PostgreSQL sharded by user_id using a consistent hash ring; each shard replicated with streaming replication.",
            "Feed fan-out: when you post, your photo ID is pushed into each follower's Cassandra feed row at write time.",
            "Redis stores the follow/follower graph in memory for O(1) fan-out target list lookup.",
            "Media never served from app servers — always via S3 + CloudFront; app only returns signed URLs.",
            "Celery + RabbitMQ processes async tasks: push notifications, email, feed fan-out, image resizing.",
            "Stories use a separate Cassandra table with a 24-hour TTL on each item — expiry is free with Cassandra TTLs.",
        ],
        "sources": [
            "instagram-engineering.com",
            "highscalability.com/instagram",
            "slideshare.net/iammutex/scaling-instagram",
        ],
    },

    # ── 7. Facebook News Feed ──────────────────────────────────────────────────
    {
        "system_name": "facebook",
        "title": "Facebook News Feed Architecture",
        "diagram_json": {
            "nodes": [
                "Client", "Load Balancer", "Web Tier (PHP/Hack)",
                "TAO (Social Graph Cache)", "Memcached (Lookaside Cache)",
                "MySQL (Sharded)", "Haystack (Photo Store)",
                "Feed Aggregator", "EdgeRank / ML Ranker",
                "Kafka Event Bus", "Scribe Log Aggregator",
                "Hive / Spark (Offline Analytics)",
            ],
            "edges": [
                {"from": "Client", "to": "Web Tier (PHP/Hack)"},
                {"from": "Web Tier (PHP/Hack)", "to": "TAO (Social Graph Cache)"},
                {"from": "Web Tier (PHP/Hack)", "to": "Memcached (Lookaside Cache)"},
                {"from": "Memcached (Lookaside Cache)", "to": "MySQL (Sharded)"},
                {"from": "Feed Aggregator", "to": "EdgeRank / ML Ranker"},
                {"from": "TAO (Social Graph Cache)", "to": "MySQL (Sharded)"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Social Graph (TAO)",
                "News Feed Aggregation & Ranking",
                "Memcached Caching Layer",
                "MySQL Sharding (User + Content DBs)",
                "Haystack Photo Storage",
                "Kafka + Scribe Event Pipeline",
                "Offline Analytics (Hive / Spark)",
            ]
        },
        "key_insights": [
            "TAO (The Associations and Objects) is a distributed graph cache that sits in front of MySQL and serves social graph reads at microsecond latency.",
            "Memcached cluster has tens of thousands of servers; Facebook contributed mcrouter (Memcached proxy) to OSS.",
            "EdgeRank considers affinity (who you interact with), edge weight (like vs comment), and time decay.",
            "Hybrid fan-out: push for normal accounts, pull-merge for pages with millions of followers.",
            "Haystack is a custom blob store optimised for small (photo) reads; eliminates filesystem metadata overhead.",
            "HipHop VM (HHVM) compiles PHP to native machine code — 6× CPU throughput improvement over stock PHP.",
            "Scribe aggregates logs across thousands of machines into HDFS for Hive analytics jobs.",
        ],
        "sources": [
            "engineering.fb.com",
            "highscalability.com/facebook",
            "papers.facebook.com/tao",
        ],
    },

    # ── 8. Amazon E-Commerce ───────────────────────────────────────────────────
    {
        "system_name": "amazon",
        "title": "Amazon E-Commerce & Order Management Architecture",
        "diagram_json": {
            "nodes": [
                "Browser / App", "CloudFront CDN", "API Gateway (AWS)",
                "Product Catalog Service", "Search Service (Elasticsearch)",
                "Inventory Service", "Order Service",
                "Payment Service", "Recommendation Engine",
                "DynamoDB (Cart / Session)", "Aurora PostgreSQL (Orders)",
                "S3 (Product Images)", "SQS / SNS",
                "Warehouse Management System", "Logistics / Last-Mile",
            ],
            "edges": [
                {"from": "Browser / App", "to": "CloudFront CDN"},
                {"from": "Browser / App", "to": "API Gateway (AWS)"},
                {"from": "API Gateway (AWS)", "to": "Order Service"},
                {"from": "Order Service", "to": "Inventory Service"},
                {"from": "Order Service", "to": "Payment Service"},
                {"from": "Order Service", "to": "Aurora PostgreSQL (Orders)"},
                {"from": "Order Service", "to": "SQS / SNS"},
                {"from": "SQS / SNS", "to": "Warehouse Management System"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Product Catalog & Search",
                "Shopping Cart (DynamoDB)",
                "Order Processing Pipeline",
                "Inventory Management",
                "Payment & Fraud Detection",
                "Recommendation Engine",
                "Fulfillment & Logistics",
                "CDN & Static Assets",
            ]
        },
        "key_insights": [
            "Amazon pioneered the two-pizza team + microservices model; product page may aggregate 100+ service calls.",
            "DynamoDB (invented at Amazon) stores session data and carts with single-digit ms latency at any scale.",
            "Elasticsearch powers faceted product search with real-time inventory filtering.",
            "Saga pattern coordinates distributed order transactions across inventory, payment, and fulfillment services.",
            "Recommendation engine uses item-to-item collaborative filtering; responsible for 35% of revenue.",
            "Inventory uses optimistic locking with conditional writes in DynamoDB to prevent overselling.",
            "SQS decouples order placement from fulfillment; guarantees at-least-once delivery to warehouse systems.",
        ],
        "sources": [
            "aws.amazon.com/blogs/aws",
            "highscalability.com/amazon",
            "allthingsdistributed.com",
        ],
    },

    # ── 9. Google Search ───────────────────────────────────────────────────────
    {
        "system_name": "google",
        "title": "Google Search Architecture",
        "diagram_json": {
            "nodes": [
                "User Query", "Load Balancer", "Google Web Server (GWS)",
                "Query Understanding (NLP / BERT)",
                "Index Servers (Inverted Index Shards)",
                "Document Servers (Compressed HTML)",
                "PageRank Score Store",
                "Ad Auction System", "Knowledge Graph",
                "Bigtable (Index Store)", "Spanner (Serving Data)",
                "Colossus (Distributed File System)",
                "MapReduce / Flume (Index Build)",
                "Caffeine (Continuous Crawl & Index)",
            ],
            "edges": [
                {"from": "User Query", "to": "Google Web Server (GWS)"},
                {"from": "Google Web Server (GWS)", "to": "Query Understanding (NLP / BERT)"},
                {"from": "Query Understanding (NLP / BERT)", "to": "Index Servers (Inverted Index Shards)"},
                {"from": "Index Servers (Inverted Index Shards)", "to": "Document Servers (Compressed HTML)"},
                {"from": "Index Servers (Inverted Index Shards)", "to": "PageRank Score Store"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Web Crawling (Googlebot)",
                "Inverted Index Construction (MapReduce / Flume)",
                "Continuous Indexing (Caffeine)",
                "Query Understanding (BERT, Synonyms, Spell)",
                "Serving (Index + Document Servers)",
                "Ranking (PageRank + 200+ signals + ML)",
                "Knowledge Graph",
                "Ad Auction (AdWords / Ads Quality)",
            ]
        },
        "key_insights": [
            "Googlebot crawls trillions of pages; Caffeine introduced continuous, incremental index updates (vs batch rebuilds).",
            "Inverted index maps each word to a postings list of (docID, position, frequency) tuples; sharded across thousands of machines.",
            "PageRank is a recursive graph algorithm; computed via iterative MapReduce until convergence.",
            "BERT (Bidirectional Encoder Representations from Transformers) used for query understanding since 2019.",
            "Result ranking uses 200+ signals including PageRank, freshness, click-through rate, and user location.",
            "GFS (Google File System) / Colossus provides the underlying distributed storage for all data.",
            "Bigtable stores the crawled web (URL → content) and serves as the source for the forward index.",
        ],
        "sources": [
            "research.google/pubs/googlefs",
            "research.google/pubs/bigtable",
            "highscalability.com/google",
        ],
    },

    # ── 10. Spotify ────────────────────────────────────────────────────────────
    {
        "system_name": "spotify",
        "title": "Spotify Music Streaming Architecture",
        "diagram_json": {
            "nodes": [
                "Client (Desktop/Mobile)", "CDN (Fastly)",
                "API Gateway (Kong)", "Track Service",
                "Search Service (Elasticsearch)",
                "Playlist Service (Cassandra)",
                "Recommendation Engine (BaRT / Discover Weekly)",
                "Audio Delivery (Ogg Vorbis / AAC)",
                "Google Cloud Storage (Audio Files)",
                "Kafka Event Streaming", "Dataflow (Analytics)",
                "BigQuery (Data Warehouse)", "Podcast Service",
            ],
            "edges": [
                {"from": "Client (Desktop/Mobile)", "to": "CDN (Fastly)"},
                {"from": "CDN (Fastly)", "to": "Google Cloud Storage (Audio Files)"},
                {"from": "Client (Desktop/Mobile)", "to": "API Gateway (Kong)"},
                {"from": "API Gateway (Kong)", "to": "Recommendation Engine (BaRT / Discover Weekly)"},
                {"from": "Kafka Event Streaming", "to": "Dataflow (Analytics)"},
                {"from": "Dataflow (Analytics)", "to": "Recommendation Engine (BaRT / Discover Weekly)"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Audio Ingestion & Transcoding",
                "CDN & Audio Delivery",
                "Track & Metadata Service",
                "Playlist Management (Cassandra)",
                "Search (Elasticsearch)",
                "Recommendation (Collaborative Filtering + NLP)",
                "Discover Weekly & Release Radar",
                "Analytics (Kafka + Dataflow + BigQuery)",
            ]
        },
        "key_insights": [
            "Audio files stored in Google Cloud Storage; CDN (Fastly) caches the most-popular tracks at edge.",
            "Cassandra stores playlists and user library with wide rows keyed by user_id; supports 10M+ writes/day.",
            "Discover Weekly uses matrix factorization (ALS) on the implicit feedback matrix of play counts.",
            "Lyrics, podcast transcripts, and audio features analysed with NLP for natural language music search.",
            "Kafka ingests every play, skip, and search event; aggregated in Dataflow for near-real-time dashboards.",
            "Squads model (autonomous cross-functional teams) allows parallel feature delivery across 60+ teams.",
            "BaRT (Bandits for Recommendations as Treatments) uses contextual multi-armed bandits for personalised radio.",
        ],
        "sources": [
            "engineering.atspotify.com",
            "highscalability.com/spotify",
            "labs.spotify.com/2014/02/discover",
        ],
    },

    # ── 11. Airbnb ─────────────────────────────────────────────────────────────
    {
        "system_name": "airbnb",
        "title": "Airbnb Home-Sharing Platform Architecture",
        "diagram_json": {
            "nodes": [
                "Web / Mobile Client", "AWS ALB",
                "API Gateway (Nginx)", "Search Service (Elasticsearch)",
                "Listing Service (MySQL)", "Booking Service (MySQL)",
                "Payment Service (Stripe / Braintree)",
                "Messaging Service (AWS SQS + WebSocket)",
                "Review Service", "Image Service (S3 + Imgix CDN)",
                "Pricing / Revenue Management Engine",
                "Apache Airflow (ML Pipelines)", "Druid (Analytics)",
            ],
            "edges": [
                {"from": "Web / Mobile Client", "to": "API Gateway (Nginx)"},
                {"from": "API Gateway (Nginx)", "to": "Search Service (Elasticsearch)"},
                {"from": "API Gateway (Nginx)", "to": "Booking Service (MySQL)"},
                {"from": "Booking Service (MySQL)", "to": "Payment Service (Stripe / Braintree)"},
                {"from": "Booking Service (MySQL)", "to": "Messaging Service (AWS SQS + WebSocket)"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Listing Ingestion & Search (Elasticsearch)",
                "Geo-Search & Map Clustering",
                "Availability Calendar & Double-Booking Prevention",
                "Booking Flow & Payments",
                "Messaging (WebSocket + SQS)",
                "Pricing Engine (Smart Pricing)",
                "Image Upload & CDN",
                "Trust & Safety (Fraud Detection)",
            ]
        },
        "key_insights": [
            "Elasticsearch geo-search uses bounding-box queries with post-filter on availability; returned in <200ms.",
            "Availability calendar uses optimistic locking in MySQL with a unique constraint on (listing_id, date) to prevent double bookings.",
            "Smart Pricing ML model uses XGBoost on 100+ features (seasonality, local events, competitor prices) for dynamic rate suggestions.",
            "Payments held in escrow; released to host 24h after guest check-in — reduces fraud window.",
            "Imgix transforms and serves listing images on-the-fly (crop, resize, WebP conversion) from S3 origin.",
            "Apache Airflow schedules ML pipeline DAGs (feature extraction, model training, validation) nightly.",
            "Druid provides sub-second OLAP queries over billions of booking and search events for dashboards.",
        ],
        "sources": [
            "medium.com/airbnb-engineering",
            "highscalability.com/airbnb",
            "databricks.com/customers/airbnb",
        ],
    },

    # ── 12. LinkedIn ───────────────────────────────────────────────────────────
    {
        "system_name": "linkedin",
        "title": "LinkedIn Professional Network Architecture",
        "diagram_json": {
            "nodes": [
                "Client", "LiX (Feature Flags)", "Rest.li API Framework",
                "Feed Service (Espresso)", "Graph Service (Voldemort)",
                "Search (Galene / Elasticsearch)",
                "Messaging Service (Iris)", "Notification Service",
                "Jobs Service", "Learning Service",
                "Kafka (Activity Stream)", "Pinot (Real-time Analytics)",
                "Nuage (ML Platform)",
            ],
            "edges": [
                {"from": "Client", "to": "Rest.li API Framework"},
                {"from": "Rest.li API Framework", "to": "Feed Service (Espresso)"},
                {"from": "Rest.li API Framework", "to": "Graph Service (Voldemort)"},
                {"from": "Kafka (Activity Stream)", "to": "Pinot (Real-time Analytics)"},
                {"from": "Kafka (Activity Stream)", "to": "Nuage (ML Platform)"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Professional Graph (Voldemort / Connections)",
                "Feed Generation & Ranking",
                "Messaging (Iris / WebSocket)",
                "Search & Typeahead (Galene)",
                "Jobs Recommendation",
                "Real-time Analytics (Pinot)",
                "A/B Testing & Feature Flags (LiX)",
            ]
        },
        "key_insights": [
            "Voldemort is LinkedIn's open-source distributed key-value store; stores the social graph as adjacency lists.",
            "Espresso is a document-oriented NoSQL store built on top of MySQL; used for member profile and feed data.",
            "Galene is LinkedIn's in-house search infrastructure; powers typeahead with <50ms P99 latency.",
            "Kafka was invented at LinkedIn (open-sourced 2011); LinkedIn itself sends 1.5 trillion Kafka messages/day.",
            "Pinot provides real-time OLAP (impressions, clicks, job views) with <1s query latency over 100B+ records.",
            "Feed ranking uses a two-stage funnel: retrieval (Voldemort graph traversal) then ML re-ranking (GBT + neural).",
            "LiX (LinkedIn Experiment) provides per-member feature flagging enabling 1000+ simultaneous A/B tests.",
        ],
        "sources": [
            "engineering.linkedin.com",
            "highscalability.com/linkedin",
            "kafka.apache.org/powered-by",
        ],
    },

    # ── 13. Discord ────────────────────────────────────────────────────────────
    {
        "system_name": "discord",
        "title": "Discord Real-Time Messaging & Voice Architecture",
        "diagram_json": {
            "nodes": [
                "Client (Desktop/Mobile)", "Cloudflare DDoS Protection",
                "API Monolith (Elixir / Python)", "Gateway Service (WebSocket)",
                "Voice Service (WebRTC)", "Cassandra (Message History)",
                "ScyllaDB (Message Store — migrated from Cassandra)",
                "Redis (Presence / Pub-Sub)", "Rust Microservices",
                "Media Proxy (Images + Video)", "CDN",
                "Guilded Integration",
            ],
            "edges": [
                {"from": "Client (Desktop/Mobile)", "to": "Cloudflare DDoS Protection"},
                {"from": "Cloudflare DDoS Protection", "to": "Gateway Service (WebSocket)"},
                {"from": "Gateway Service (WebSocket)", "to": "API Monolith (Elixir / Python)"},
                {"from": "API Monolith (Elixir / Python)", "to": "ScyllaDB (Message Store — migrated from Cassandra)"},
                {"from": "Gateway Service (WebSocket)", "to": "Redis (Presence / Pub-Sub)"},
                {"from": "Client (Desktop/Mobile)", "to": "Voice Service (WebRTC)"},
            ],
        },
        "canonical_json": {
            "sections": [
                "WebSocket Gateway & Presence",
                "Message Store (ScyllaDB)",
                "Voice & Video (WebRTC / Selective Forwarding Unit)",
                "Guild (Server) Sharding",
                "Read States & Notifications",
                "DDoS Mitigation (Cloudflare)",
                "Media Proxy & CDN",
            ]
        },
        "key_insights": [
            "Migrated message store from Cassandra to ScyllaDB (C++ Cassandra-compatible); reduced P99 read latency from 40ms to 15ms.",
            "Gateway nodes hold WebSocket connections; guild events fan out via Redis pub/sub to all connected gateway nodes.",
            "Voice uses WebRTC with a selective forwarding unit (SFU) — server relays encrypted audio, no decoding.",
            "Guild sharding: a guild (server) is the unit of consistency; all events within a guild are serialised.",
            "Rewrote core hot paths in Rust for CPU efficiency; reduced median latency by 5× vs Python equivalents.",
            "Read states (which messages you've seen) stored per-user in ScyllaDB with a COUNTER column — cheapest possible write.",
            "Cloudflare absorbs DDoS at 100s of Gbps, making Discord hard to take down despite being a gaming platform.",
        ],
        "sources": [
            "discord.com/blog/engineering",
            "blog.discord.com/how-discord-stores-billions-of-messages",
            "blog.discord.com/why-discord-is-switching-from-go-to-rust",
        ],
    },

    # ── 14. Slack ──────────────────────────────────────────────────────────────
    {
        "system_name": "slack",
        "title": "Slack Team Messaging Architecture",
        "diagram_json": {
            "nodes": [
                "Client (Web/Desktop/Mobile)", "AWS ELB",
                "PHP Webapp (API)", "Real-Time Messaging Server (Go)",
                "WebSocket Gateway", "MySQL (Sharded — per workspace)",
                "Solr Search (Elasticsearch)", "Memcached",
                "Redis (Pub-Sub / Job Queue)", "S3 (File Storage)",
                "Notification Service (APNs / FCM)", "Kafka",
                "Vitess (MySQL Sharding)",
            ],
            "edges": [
                {"from": "Client (Web/Desktop/Mobile)", "to": "AWS ELB"},
                {"from": "AWS ELB", "to": "PHP Webapp (API)"},
                {"from": "PHP Webapp (API)", "to": "Vitess (MySQL Sharding)"},
                {"from": "Client (Web/Desktop/Mobile)", "to": "WebSocket Gateway"},
                {"from": "WebSocket Gateway", "to": "Real-Time Messaging Server (Go)"},
                {"from": "Real-Time Messaging Server (Go)", "to": "Redis (Pub-Sub / Job Queue)"},
                {"from": "Real-Time Messaging Server (Go)", "to": "Notification Service (APNs / FCM)"},
            ],
        },
        "canonical_json": {
            "sections": [
                "WebSocket & Real-Time Messaging",
                "MySQL Sharding (Vitess) per Workspace",
                "Message Search (Elasticsearch)",
                "File Storage (S3)",
                "Notification Delivery",
                "Channel & Thread Model",
                "Presence & Typing Indicators",
            ]
        },
        "key_insights": [
            "Each Slack workspace is a MySQL shard; teams are isolated — no cross-shard queries needed for normal messaging.",
            "Vitess (YouTube-originated) manages MySQL sharding, connection pooling, and horizontal scaling transparently.",
            "WebSocket gateway written in Go handles hundreds of thousands of concurrent connections per node.",
            "Message IDs are flake IDs (time-based, sortable UUIDs) — channel history is a simple range scan by ts.",
            "Presence (online/away/DND) uses Redis pub/sub; status changes fanout to workspace members in <100ms.",
            "Search indexes every message in Elasticsearch in near-real-time; supports slash-search across all history.",
            "Files uploaded to S3; Slack stores only the S3 URL + metadata in MySQL. Preview thumbnails generated async.",
        ],
        "sources": [
            "slack.engineering",
            "highscalability.com/slack",
            "vitess.io/users/slack",
        ],
    },

    # ── 15. Reddit ─────────────────────────────────────────────────────────────
    {
        "system_name": "reddit",
        "title": "Reddit Social News & Community Architecture",
        "diagram_json": {
            "nodes": [
                "Client", "Fastly CDN", "AWS ALB",
                "API Gateway (Python / Thrift)",
                "Post Service (PostgreSQL)", "Comment Service (PostgreSQL)",
                "Vote Service (Cassandra)", "Feed / Listing Service",
                "Search (Elasticsearch)", "Recommendation Service",
                "Reddit Ads", "Media Service (S3 + CDN)",
                "Kafka", "Flink (Stream Processing)",
                "Memcached (Listing Cache)",
            ],
            "edges": [
                {"from": "Client", "to": "Fastly CDN"},
                {"from": "Fastly CDN", "to": "AWS ALB"},
                {"from": "AWS ALB", "to": "Feed / Listing Service"},
                {"from": "Feed / Listing Service", "to": "Memcached (Listing Cache)"},
                {"from": "Feed / Listing Service", "to": "Post Service (PostgreSQL)"},
                {"from": "Feed / Listing Service", "to": "Vote Service (Cassandra)"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Vote & Ranking (Wilson Score / Hot Algorithm)",
                "Post & Comment Storage (PostgreSQL)",
                "Feed Generation & Listing Cache",
                "Subreddit Moderation Tools",
                "Search (Elasticsearch)",
                "Media Upload & CDN",
                "Awards & Premium System",
            ]
        },
        "key_insights": [
            "Hot ranking uses a log-decay formula combining vote score and post age; score doubles approximately every 45k upvotes.",
            "Vote Service uses Cassandra with counter columns for upvote/downvote counts; eventually consistent is acceptable.",
            "Listing cache in Memcached holds pre-ranked lists for popular subreddits; invalidated on new posts or score changes.",
            "Comments use a nested set model in PostgreSQL; entire comment tree fetched in a single range query.",
            "Migrated from Postgres monolith to service-oriented architecture; each service owns its own database.",
            "Fastly CDN handles 90%+ of read traffic; HTML pages for logged-out users served as static cached responses.",
            "Kafka + Flink powers real-time anti-spam (vote manipulation, bot detection) and ad impression counting.",
        ],
        "sources": [
            "redditinc.com/blog/engineering",
            "highscalability.com/reddit",
            "medium.com/reddit-blog",
        ],
    },

    # ── 16. TikTok ─────────────────────────────────────────────────────────────
    {
        "system_name": "tiktok",
        "title": "TikTok Short-Video Platform Architecture",
        "diagram_json": {
            "nodes": [
                "Client App", "Anycast DNS / CDN",
                "API Gateway", "Video Upload Service",
                "Transcoding Pipeline (FFmpeg Clusters)",
                "Object Storage (TOS — TikTok Object Storage)",
                "CDN Edge Cache", "Recommendation Engine (Deep Learning)",
                "User Interest Graph", "Social Graph Service",
                "Kafka Event Bus", "Flink Stream Processing",
                "ByteHouse (ClickHouse fork — Analytics)",
                "Comment & Interaction Service",
            ],
            "edges": [
                {"from": "Client App", "to": "API Gateway"},
                {"from": "Client App", "to": "Video Upload Service"},
                {"from": "Video Upload Service", "to": "Object Storage (TOS — TikTok Object Storage)"},
                {"from": "Object Storage (TOS — TikTok Object Storage)", "to": "Transcoding Pipeline (FFmpeg Clusters)"},
                {"from": "Transcoding Pipeline (FFmpeg Clusters)", "to": "CDN Edge Cache"},
                {"from": "Kafka Event Bus", "to": "Recommendation Engine (Deep Learning)"},
                {"from": "Kafka Event Bus", "to": "Flink Stream Processing"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Video Upload & Transcoding",
                "CDN & Adaptive Delivery",
                "For You Page (FYP) Recommendation",
                "User Interest & Interaction Graph",
                "Social Features (Follow, Like, Comment)",
                "Live Streaming",
                "Real-Time Analytics (Flink + ByteHouse)",
            ]
        },
        "key_insights": [
            "For You Page (FYP) recommendation uses a two-tower deep learning model: one tower for user interests, one for video content.",
            "Watch completion rate is the single strongest FYP signal; even one extra second of watch time shifts recommendations.",
            "Video pre-loading: next 3 videos in the predicted queue are pre-fetched while current video plays.",
            "Transcoding produces 10+ quality levels; mobile clients request the highest quality sustainable over current bandwidth.",
            "Real-time Flink jobs update the user interest graph within 3 seconds of an interaction.",
            "Live gifts (virtual currency) processed via a separate high-throughput payment micro-service with idempotency keys.",
            "ByteHouse (ClickHouse fork) handles 100B+ rows for creator analytics with sub-second query times.",
        ],
        "sources": [
            "bytedance.com/en/technology",
            "highscalability.com/tiktok",
            "medium.com/bytedance-engineering",
        ],
    },

    # ── 17. Dropbox ────────────────────────────────────────────────────────────
    {
        "system_name": "dropbox",
        "title": "Dropbox Cloud Storage & Sync Architecture",
        "diagram_json": {
            "nodes": [
                "Desktop / Mobile Client", "Notification Server (SSE)",
                "Metadata Server (Edgestore)", "Block Server",
                "Amazon S3 (Block Storage)", "Magic Pocket (In-house Storage)",
                "Sync Engine (Client-side)", "Block Deduplication (SHA-256)",
                "Bandwidth Scheduler", "Collaboration Service",
                "Search (Nautilus)", "CDN",
            ],
            "edges": [
                {"from": "Desktop / Mobile Client", "to": "Sync Engine (Client-side)"},
                {"from": "Sync Engine (Client-side)", "to": "Block Server"},
                {"from": "Block Server", "to": "Block Deduplication (SHA-256)"},
                {"from": "Block Deduplication (SHA-256)", "to": "Amazon S3 (Block Storage)"},
                {"from": "Desktop / Mobile Client", "to": "Notification Server (SSE)"},
                {"from": "Notification Server (SSE)", "to": "Metadata Server (Edgestore)"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Block-Level File Chunking & Deduplication",
                "Metadata Server (Edgestore)",
                "S3 to Magic Pocket Migration",
                "Sync Engine & Delta Sync",
                "LAN Sync (P2P between devices on same network)",
                "Collaboration & Shared Folders",
                "Search (Nautilus)",
            ]
        },
        "key_insights": [
            "Files split into 4MB blocks; each block SHA-256 hashed and deduplicated globally — identical files across all users stored once.",
            "Delta sync: only changed blocks uploaded on file modification, not the entire file.",
            "LAN sync uses mDNS to discover peers on the same network; transfers blocks directly without going to S3.",
            "Magic Pocket: Dropbox moved from S3 to in-house exabyte-scale storage (2016), saving hundreds of millions/year.",
            "Edgestore is a distributed metadata store built on MySQL with a custom sharding layer (similar to Vitess).",
            "Notification server uses long-polling SSE to push 'cursor changed' events to clients; clients then fetch delta.",
            "Bandwidth throttling: Dropbox's sync client detects idle vs active periods and adjusts upload speed accordingly.",
        ],
        "sources": [
            "dropbox.tech",
            "highscalability.com/dropbox",
            "wired.com/2016/03/epic-story-dropboxs-exodus-amazon-cloud-empire",
        ],
    },

    # ── 18. Zoom ───────────────────────────────────────────────────────────────
    {
        "system_name": "zoom",
        "title": "Zoom Video Conferencing Architecture",
        "diagram_json": {
            "nodes": [
                "Client (Desktop/Mobile/Web)", "Zoom Multimedia Router (MMR)",
                "Meeting Controller", "UDP Media Transmission",
                "TURN Server (Relay)", "Recording Service (S3)",
                "Webinar Service", "Chat Service",
                "Screen Share Service", "Global Data Center Network",
                "AWS / Azure / Oracle Cloud (Burst Capacity)",
                "End-to-End Encryption (AES-256 GCM)",
            ],
            "edges": [
                {"from": "Client (Desktop/Mobile/Web)", "to": "Zoom Multimedia Router (MMR)"},
                {"from": "Zoom Multimedia Router (MMR)", "to": "Meeting Controller"},
                {"from": "Client (Desktop/Mobile/Web)", "to": "UDP Media Transmission"},
                {"from": "UDP Media Transmission", "to": "Zoom Multimedia Router (MMR)"},
                {"from": "Zoom Multimedia Router (MMR)", "to": "Recording Service (S3)"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Media Routing (MMR — Multimedia Router)",
                "UDP-first Media Transport",
                "Meeting Controller & Signalling",
                "End-to-End Encryption",
                "Recording & Transcription",
                "Screen Sharing & Annotation",
                "Webinar vs Meeting Architecture",
                "Burst Capacity (Public Cloud)",
            ]
        },
        "key_insights": [
            "Zoom's MMR (Multimedia Router) routes media at the IP layer without decoding; much cheaper than SFU-style transcoding.",
            "UDP-first with proprietary congestion control; falls back to TCP/TLS when UDP is blocked by firewalls.",
            "During COVID-19, daily meeting participants went from 10M to 300M in 3 months; burst capacity via AWS/Azure absorbed the spike.",
            "AES-256-GCM encryption with rotating meeting keys; E2EE option encrypts media on-device (key not on server).",
            "Virtual background uses AI segmentation (TensorFlow Lite on-device) to separate foreground from background.",
            "Screen sharing encoded as H.264 (low-motion optimised) at 5 fps by default; GPU acceleration on modern clients.",
            "Zoom chose UDP over WebRTC's standardised protocol for tighter control over codec selection and congestion algorithms.",
        ],
        "sources": [
            "zoom.us/blog/engineering",
            "highscalability.com/zoom",
            "blog.zoom.us/a-message-to-our-users",
        ],
    },

    # ── 19. Stripe ─────────────────────────────────────────────────────────────
    {
        "system_name": "stripe",
        "title": "Stripe Payment Processing Architecture",
        "diagram_json": {
            "nodes": [
                "Merchant (Web / Mobile)", "Stripe.js / Stripe SDK",
                "API Gateway (TLS 1.3)", "Payment Intent Service",
                "Card Vaulting (PCI Scope)", "Issuing Bank (Card Networks)",
                "Fraud Detection (Stripe Radar)", "Idempotency Key Store",
                "PostgreSQL (Primary Store)", "Redis (Rate Limiting / Cache)",
                "Kafka (Event Bus)", "Data Warehouse (Redshift)",
                "Payout Service", "Webhook Delivery Service",
            ],
            "edges": [
                {"from": "Merchant (Web / Mobile)", "to": "Stripe.js / Stripe SDK"},
                {"from": "Stripe.js / Stripe SDK", "to": "API Gateway (TLS 1.3)"},
                {"from": "API Gateway (TLS 1.3)", "to": "Payment Intent Service"},
                {"from": "Payment Intent Service", "to": "Fraud Detection (Stripe Radar)"},
                {"from": "Payment Intent Service", "to": "Card Vaulting (PCI Scope)"},
                {"from": "Card Vaulting (PCI Scope)", "to": "Issuing Bank (Card Networks)"},
                {"from": "Payment Intent Service", "to": "Kafka (Event Bus)"},
                {"from": "Kafka (Event Bus)", "to": "Webhook Delivery Service"},
            ],
        },
        "canonical_json": {
            "sections": [
                "PCI-DSS Compliance & Card Vaulting",
                "Payment Intents & Idempotency",
                "Fraud Detection (Stripe Radar / ML)",
                "Card Network Integration (Visa, MC, Amex)",
                "Payout & Settlement",
                "Webhook Delivery (At-Least-Once)",
                "Dispute & Refund Management",
                "Stripe Connect (Platform Payments)",
            ]
        },
        "key_insights": [
            "Idempotency keys (client-generated UUID sent with each POST) prevent duplicate charges on network retries.",
            "Card numbers never touch merchant servers; Stripe.js tokenises PAN client-side and sends only a token.",
            "PCI-DSS Level 1 compliance: card vault runs in an isolated network segment with hardware security modules (HSMs).",
            "Stripe Radar ML model evaluates 1000+ signals in <100ms to assign a fraud risk score before auth request.",
            "Payment Intents API models the full payment lifecycle as a state machine (requires_action → succeeded / failed).",
            "Webhook delivery retries with exponential back-off for up to 3 days; merchants must handle idempotently.",
            "Postgres is the source of truth; Redis used for distributed locking during charge state transitions.",
        ],
        "sources": [
            "stripe.com/blog/engineering",
            "highscalability.com/stripe",
            "increment.com/payments/stripe-api-seven-rules",
        ],
    },

    # ── 20. Elasticsearch / ELK Stack (as a system design) ────────────────────
    {
        "system_name": "elasticsearch",
        "title": "Elasticsearch Distributed Search Architecture",
        "diagram_json": {
            "nodes": [
                "Client / Application", "Load Balancer",
                "Coordinating Node", "Master Node (Cluster State)",
                "Data Nodes (Shards)", "Ingest Node (Pipeline)",
                "Logstash (ETL)", "Kibana (Visualisation)",
                "Beats (Data Shippers)", "Lucene Index (per Shard)",
                "Translog (Write-ahead Log)", "Snapshot (S3 / GCS)",
            ],
            "edges": [
                {"from": "Client / Application", "to": "Load Balancer"},
                {"from": "Load Balancer", "to": "Coordinating Node"},
                {"from": "Coordinating Node", "to": "Data Nodes (Shards)"},
                {"from": "Beats (Data Shippers)", "to": "Logstash (ETL)"},
                {"from": "Logstash (ETL)", "to": "Ingest Node (Pipeline)"},
                {"from": "Ingest Node (Pipeline)", "to": "Data Nodes (Shards)"},
                {"from": "Data Nodes (Shards)", "to": "Snapshot (S3 / GCS)"},
            ],
        },
        "canonical_json": {
            "sections": [
                "Cluster Architecture (Master / Data / Coordinating Nodes)",
                "Index & Shard Design",
                "Inverted Index (Lucene)",
                "Write Path (Translog + Refresh)",
                "Read Path (Scatter-Gather)",
                "Relevance Scoring (BM25 + field boosting)",
                "ELK Stack Integration",
                "Snapshot & Restore",
            ]
        },
        "key_insights": [
            "Each index is divided into primary shards (immutable once set); each primary has configurable replicas for HA.",
            "Coordinating node fans a search query out to all relevant shards (scatter), then merges results (gather).",
            "Write path: document goes to primary shard → Translog (fsync) → in-memory buffer → segment refresh every 1s.",
            "Near-real-time search: newly indexed documents are visible within 1 second (refresh interval) without fsync.",
            "BM25 (probabilistic term frequency + IDF) replaced TF-IDF as the default relevance model in ES 5.0.",
            "Hot-warm-cold architecture: recent indices on NVMe nodes, older indices on HDDs, oldest in frozen (S3-backed) tier.",
            "Mapping explosion anti-pattern: unbounded dynamic field mapping causes heap exhaustion; always define explicit mappings.",
        ],
        "sources": [
            "elastic.co/blog/engineering",
            "highscalability.com/elasticsearch",
            "lucene.apache.org/core/documentation",
        ],
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_document_text(design_data: dict) -> str:
    """Flatten a famous-design record into a rich text blob for embedding.
    Includes title, component nodes, canonical sections, and all key insights
    so the Chroma similarity search surfaces the most relevant chunks."""
    parts = [design_data["title"]]
    nodes = design_data.get("diagram_json", {}).get("nodes", [])
    if nodes:
        parts.append("Components: " + ", ".join(nodes))
    sections = design_data.get("canonical_json", {}).get("sections", [])
    if sections:
        parts.append("Sections: " + ", ".join(sections))
    insights = design_data.get("key_insights", [])
    if insights:
        parts.append("Key Insights:")
        parts.extend(f"  - {i}" for i in insights)
    return "\n".join(parts)


async def _index_chroma(design_data: dict) -> None:
    """Embed + upsert one design into the `famous_designs` Chroma collection.
    Uses upsert (keyed by system_name) so re-runs are safe."""
    if not settings.gemini_api_key:
        print(
            f"  [skip-vector] No GEMINI_API_KEY — '{design_data['system_name']}' "
            "saved to SQL but NOT indexed in ChromaDB."
        )
        return

    document = _build_document_text(design_data)
    try:
        embedding = await gemini_embed(document, task_type="retrieval_document")
    except Exception as e:
        print(f"  [skip-vector] Embedding failed for '{design_data['system_name']}': {e}")
        return

    collection = get_famous_designs_collection()
    collection.upsert(
        ids=[design_data["system_name"]],
        embeddings=[embedding],
        documents=[document],
        metadatas=[{
            "system": design_data["system_name"],
            "title": design_data["title"],
        }],
    )
    print(
        f"  [vector-ok] '{design_data['system_name']}' indexed in ChromaDB "
        f"({settings.chroma_persist_dir})"
    )


async def seed() -> None:
    """Idempotent seed: inserts missing rows in SQL + upserts all vectors in Chroma."""
    async with AsyncSessionLocal() as db:
        # ── SQL inserts ────────────────────────────────────────────────────────
        print(f"\n📦  Seeding {len(FAMOUS_DESIGNS)} famous designs into SQL...\n")
        for design_data in FAMOUS_DESIGNS:
            result = await db.execute(
                select(FamousDesign).where(FamousDesign.system_name == design_data["system_name"])
            )
            exists = result.scalar_one_or_none()

            # Build a clean dict excluding keys that are not model columns
            model_fields = {
                "system_name", "title", "diagram_json",
                "canonical_json", "key_insights", "sources",
            }
            db_data = {k: v for k, v in design_data.items() if k in model_fields}

            if not exists:
                print(f"  [+] Inserting '{design_data['system_name']}'...")
                design = FamousDesign(**db_data)
                design.last_updated = datetime.datetime.now(datetime.timezone.utc)
                db.add(design)
            else:
                # Update all fields so re-runs refresh stale data
                print(f"  [~] Updating '{design_data['system_name']}'...")
                for field, value in db_data.items():
                    setattr(exists, field, value)
                exists.last_updated = datetime.datetime.now(datetime.timezone.utc)

        try:
            await db.commit()
            print(f"\n✅  SQL seed complete ({len(FAMOUS_DESIGNS)} designs).")
        except Exception as e:
            await db.rollback()
            print(f"\n❌  SQL seed failed: {e}")
            raise

        # ── ChromaDB upserts ───────────────────────────────────────────────────
        print(f"\n🔍  Indexing {len(FAMOUS_DESIGNS)} designs into ChromaDB...\n")
        for design_data in FAMOUS_DESIGNS:
            await _index_chroma(design_data)
        print(f"\n✅  ChromaDB indexing complete.")


if __name__ == "__main__":
    asyncio.run(seed())

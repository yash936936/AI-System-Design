"""
MCQ Templates Service (Phase B)
================================
Provides MCQ templates for HLD and LLD design flows.
"""
from typing import Dict, Any


def get_hld_template() -> Dict[str, Any]:
    """HLD MCQ template."""
    return {
        "design_type": "HLD",
        "version": "1.0",
        "categories": [
            {
                "id": "functional_reqs",
                "label": "Functional Requirements",
                "question": "What are the core features this system must support?",
                "type": "multi_select",
                "options": [
                    {"id": "user_auth", "label": "User Authentication & Profiles"},
                    {"id": "content_creation", "label": "Content Creation (posts/media)"},
                    {"id": "feed_timeline", "label": "Feed/Timeline"},
                    {"id": "search", "label": "Search Functionality"},
                    {"id": "notifications", "label": "Notifications"},
                    {"id": "messaging", "label": "Real-time Messaging"},
                    {"id": "recommendations", "label": "Recommendations/ML"},
                    {"id": "analytics", "label": "Analytics & Reporting"},
                ],
                "allow_free_text": True,
                "free_text_placeholder": "Add custom requirement...",
            },
            {
                "id": "scale",
                "label": "Scale & Traffic",
                "question": "What scale should the system handle?",
                "type": "single_select",
                "options": [
                    {"id": "small", "label": "Small (<100K DAU)"},
                    {"id": "medium", "label": "Medium (100K-10M DAU)"},
                    {"id": "large", "label": "Large (10M-100M DAU)", "recommended": True},
                    {"id": "massive", "label": "Massive (100M+ DAU)"},
                ],
                "allow_free_text": False,
                "free_text_placeholder": "",
            },
            {
                "id": "read_write_ratio",
                "label": "Read/Write Ratio",
                "question": "What is the expected read to write ratio?",
                "type": "single_select",
                "options": [
                    {"id": "read_heavy", "label": "Read-heavy (100:1)", "recommended": True},
                    {"id": "balanced", "label": "Balanced (10:1)"},
                    {"id": "write_heavy", "label": "Write-heavy (1:1)"},
                ],
                "allow_free_text": False,
                "free_text_placeholder": "",
            },
            {
                "id": "availability",
                "label": "Availability Target",
                "question": "What availability level is required?",
                "type": "single_select",
                "options": [
                    {"id": "99.9", "label": "99.9% (8.7h downtime/year)"},
                    {"id": "99.99", "label": "99.99% (52min downtime/year)", "recommended": True},
                    {"id": "99.999", "label": "99.999% (5min downtime/year)"},
                ],
                "allow_free_text": False,
                "free_text_placeholder": "",
            },
            {
                "id": "consistency",
                "label": "Consistency Model",
                "question": "What consistency model is acceptable?",
                "type": "single_select",
                "options": [
                    {"id": "eventual", "label": "Eventual Consistency", "recommended": True},
                    {"id": "strong", "label": "Strong Consistency"},
                    {"id": "causal", "label": "Causal Consistency"},
                ],
                "allow_free_text": False,
                "free_text_placeholder": "",
            },
            {
                "id": "bottleneck_focus",
                "label": "Bottleneck Focus Areas",
                "question": "Which areas are most likely to bottleneck?",
                "type": "multi_select",
                "options": [
                    {"id": "database", "label": "Database Load"},
                    {"id": "network", "label": "Network Bandwidth"},
                    {"id": "compute", "label": "Compute Resources"},
                    {"id": "storage", "label": "Storage I/O"},
                    {"id": "cache", "label": "Cache Misses"},
                    {"id": "queue", "label": "Message Queue Backlog"},
                ],
                "allow_free_text": True,
                "free_text_placeholder": "Add custom bottleneck...",
            },
        ],
    }


def get_lld_template() -> Dict[str, Any]:
    """LLD MCQ template."""
    return {
        "design_type": "LLD",
        "version": "1.0",
        "categories": [
            {
                "id": "component_focus",
                "label": "Component Focus",
                "question": "Which component needs detailed design?",
                "type": "single_select",
                "options": [
                    {"id": "cache", "label": "Cache System (LRU/LFU)"},
                    {"id": "rate_limiter", "label": "Rate Limiter"},
                    {"id": "url_shortener", "label": "URL Shortener"},
                    {"id": "search", "label": "Search Engine"},
                    {"id": "notification", "label": "Notification Service"},
                    {"id": "key_value", "label": "Key-Value Store"},
                ],
                "allow_free_text": True,
                "free_text_placeholder": "Specify component...",
            },
            {
                "id": "data_structures",
                "label": "Key Data Structures",
                "question": "Which data structures are relevant?",
                "type": "multi_select",
                "options": [
                    {"id": "hash_map", "label": "Hash Map"},
                    {"id": "linked_list", "label": "Linked List"},
                    {"id": "doubly_linked", "label": "Doubly Linked List"},
                    {"id": "binary_tree", "label": "Binary Tree"},
                    {"id": "heap", "label": "Heap/Priority Queue"},
                    {"id": "trie", "label": "Trie"},
                    {"id": "bloom_filter", "label": "Bloom Filter"},
                ],
                "allow_free_text": False,
                "free_text_placeholder": "",
            },
            {
                "id": "concurrency",
                "label": "Concurrency Model",
                "question": "How should concurrency be handled?",
                "type": "single_select",
                "options": [
                    {"id": "mutex", "label": "Mutex/Locks"},
                    {"id": "rw_lock", "label": "Read-Write Locks"},
                    {"id": "atomic", "label": "Atomic Operations"},
                    {"id": "actor", "label": "Actor Model"},
                    {"id": "message_passing", "label": "Message Passing"},
                ],
                "allow_free_text": False,
                "free_text_placeholder": "",
            },
            {
                "id": "api_style",
                "label": "API Style",
                "question": "What API style should be used?",
                "type": "single_select",
                "options": [
                    {"id": "rest", "label": "REST", "recommended": True},
                    {"id": "grpc", "label": "gRPC"},
                    {"id": "graphql", "label": "GraphQL"},
                ],
                "allow_free_text": False,
                "free_text_placeholder": "",
            },
        ],
    }


def get_template(design_type: str) -> Dict[str, Any]:
    """Get MCQ template for a design type."""
    design_type_upper = design_type.upper()
    
    if design_type_upper == "HLD":
        return get_hld_template()
    elif design_type_upper == "LLD":
        return get_lld_template()
    else:
        raise ValueError(f"Unknown design type: {design_type}")
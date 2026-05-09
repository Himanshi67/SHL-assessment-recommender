import re
from typing import List, Dict, Tuple

ROLE_HINTS = {
    "developer",
    "engineer",
    "manager",
    "sales",
    "analyst",
    "java",
    "python",
    "dotnet",
    ".net",
    "finance",
    "accountant",
    "support",
    "graduate",
    "executive",
    "supervisor",
    "leader",
    "leadership",
    "lead",
    "director",
    "cx",
    "cxo",
    "cxos",
    "role",
    "hiring",
    "hire",
}

# small synonyms map to normalize common product name variants
SYNONYMS = {
    "opq32r": "opq",
    "opq32": "opq",
    "opq": "opq",
    "svar": "svar",
    "spoken english": "spoken english",
}

PREFERENCE_HINTS = {
    "technical",
    "coding",
    "skills",
    "aptitude",
    "ability",
    "personality",
    "behavior",
    "behaviour",
    "cognitive",
    "psychometric",
}

SENIORITY_HINTS = {
    "entry",
    "entry-level",
    "junior",
    "mid",
    "mid-level",
    "graduate",
    "manager",
    "supervisor",
    "director",
    "executive",
}

REFINEMENT_HINTS = {"also", "add", "include", "actually", "instead", "along", "plus"}

STOPWORDS = {
    "i",
    "am",
    "a",
    "an",
    "the",
    "for",
    "of",
    "to",
    "and",
    "or",
    "with",
    "need",
    "want",
    "looking",
    "hire",
    "hiring",
    "someone",
    "who",
    "please",
    "me",
    "we",
    "our",
    "is",
    "this",
    "that",
    "what",
}


def normalize_text(text: str) -> str:
    # normalize whitespace, lower-case, and split hyphenated words to aid matching
    t = text.lower().replace("-", " ")
    t = re.sub(r"\s+", " ", t).strip()
    # apply synonyms replacements to help canonicalize product name variants
    for k, v in SYNONYMS.items():
        t = t.replace(k, v)
    return t


def tokenize(text: str) -> List[str]:
    text = normalize_text(text)
    # avoid capturing trailing punctuation like periods so tokens match ROLE_HINTS
    return re.findall(r"[a-zA-Z0-9\+#-]+", text)


def token_set(text: str) -> set:
    return {t for t in tokenize(text) if t not in STOPWORDS}


def extract_latest_user_message(messages: List[dict]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "").strip()
    return ""


def get_user_messages(messages: List[dict]) -> List[str]:
    return [m.get("content", "").strip() for m in messages if m.get("role") == "user"]


def combine_user_context(messages: List[dict]) -> str:
    return " ".join(get_user_messages(messages)).strip()


def is_contact_center_context(text: str) -> bool:
    t = normalize_text(text)
    keywords = [
        "contact centre",
        "contact center",
        "call centre",
        "call center",
        "inbound calls",
        "customer service",
    ]
    return any(k in t for k in keywords)


def has_language_context(text: str) -> bool:
    t = normalize_text(text)
    languages = [
        "english",
        "spanish",
        "french",
        "german",
        "dutch",
        "italian",
        "portuguese",
        "arabic",
        "hindi",
        "bilingual",
    ]
    return any(lang in t for lang in languages)


def has_english_variant_context(text: str) -> bool:
    t = normalize_text(text)
    variants = ["us", "uk", "australian", "indian", "english usa", "english us"]
    return any(v in t for v in variants)


def should_ask_clarification(messages: List[dict]) -> bool:
    full_context = combine_user_context(messages)

    if not full_context:
        return True

    if not has_role_context(full_context):
        return True

    # Role-specific clarification first
    if is_contact_center_context(full_context):
        if not has_language_context(full_context):
            return True
        if "english" in full_context.lower() and not has_english_variant_context(
            full_context
        ):
            return True

    # Generic clarification fallback
    if not has_seniority_context(full_context) and not has_preference_context(
        full_context
    ):
        return True

    return False


def get_clarifying_question(messages: List[dict]) -> str:
    full_context = combine_user_context(messages)
    t = full_context.lower()

    if not has_role_context(full_context):
        return "Happy to help — what role are you hiring for?"

    # Role-specific questions first
    if is_contact_center_context(full_context):
        if not has_language_context(full_context):
            return "Before I shape the stack, what language are the calls in?"
        if "english" in t and not has_english_variant_context(full_context):
            return "SHL has multiple English spoken-language variants in the catalog. Which fits your operation: US, UK, Australian, or Indian?"

    # Generic fallback
    if not has_seniority_context(full_context) and not has_preference_context(
        full_context
    ):
        return "Got it. What seniority level is the role, and do you want technical, aptitude, or personality assessments?"

    if not has_seniority_context(full_context):
        return "What seniority level is this role — entry-level, mid-level, or manager/senior?"

    if not has_preference_context(full_context):
        return "Should I focus on technical skills tests, or also include aptitude or personality measures?"

    return "Could you share a bit more about the role requirements?"


def has_role_context(text: str) -> bool:
    tokens = token_set(text)
    return any(t in ROLE_HINTS for t in tokens)


def has_preference_context(text: str) -> bool:
    tokens = token_set(text)
    return any(t in PREFERENCE_HINTS for t in tokens)


def has_seniority_context(text: str) -> bool:
    tokens = token_set(text)
    return any(t in SENIORITY_HINTS for t in tokens)


def is_refinement_message(text: str) -> bool:
    tokens = token_set(text)
    return any(t in REFINEMENT_HINTS for t in tokens)


def detect_requested_seniority(text: str) -> str:
    t = normalize_text(text)

    if "entry-level" in t or "entry level" in t or "junior" in t:
        return "entry"
    if (
        "mid-level" in t
        or "mid level" in t
        or "mid-professional" in t
        or re.search(r"\bmid\b", t)
    ):
        return "mid"
    if "graduate" in t:
        return "graduate"
    if "front line manager" in t:
        return "manager"
    if "manager" in t:
        return "manager"
    if "supervisor" in t:
        return "supervisor"
    if "director" in t:
        return "director"
    if "executive" in t:
        return "executive"
    return ""


def level_matches(requested_level: str, job_levels_text: str) -> bool:
    jl = normalize_text(job_levels_text)

    if not requested_level:
        return True

    mapping = {
        "entry": ["entry level", "entry"],
        "mid": ["mid professional", "mid level", "mid"],
        "graduate": ["graduate"],
        "manager": ["manager", "front line manager"],
        "supervisor": ["supervisor"],
        "director": ["director"],
        "executive": ["executive"],
    }

    allowed_levels = mapping.get(requested_level, [])
    return any(level in jl for level in allowed_levels)


def conflicting_name_level(requested_level: str, name_text: str) -> bool:
    n = normalize_text(name_text)

    if requested_level == "entry":
        return "advanced level" in n or "advanced-level" in n

    return False


# def should_ask_clarification(messages: List[dict]) -> bool:
#     full_context = combine_user_context(messages)

#     if not full_context:
#         return True

#     if not has_role_context(full_context):
#         return True

#     if not has_seniority_context(full_context) and not has_preference_context(
#         full_context
#     ):
#         return True
    
#     return False


def is_compare_request(text: str) -> bool:
    text = normalize_text(text)
    compare_phrases = ["difference between", "compare", "vs", "versus"]
    return any(p in text for p in compare_phrases)


def find_items_by_name(text: str, catalog: List[Dict], top_k: int = 2) -> List[Dict]:
    q_tokens = token_set(text)
    scored: List[Tuple[int, Dict]] = []

    for item in catalog:
        name_tokens = token_set(str(item.get("name", "")))
        overlap = len(q_tokens & name_tokens)
        if overlap > 0:
            scored.append((overlap, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored[:top_k]]


def build_comparison_reply(items: List[Dict]) -> str:
    if len(items) < 2:
        return "I could not confidently identify both SHL assessments to compare from the catalog."

    a, b = items[0], items[1]

    a_name = a.get("name", "First assessment")
    b_name = b.get("name", "Second assessment")
    a_type = a.get("test_type", "") or a.get("tags", "specific assessment areas")
    b_type = b.get("test_type", "") or b.get("tags", "specific assessment areas")
    a_duration = a.get("duration", "") or "not specified"
    b_duration = b.get("duration", "") or "not specified"

    return (
        f"{a_name} is mainly used for {a_type.lower()}, while {b_name} is used for {b_type.lower()}. "
        f"If your goal is to compare them practically, the main difference is the kind of signal each one adds to hiring decisions. "
        f"In terms of duration, {a_name} takes {a_duration} and {b_name} takes {b_duration}."
    )


def score_catalog_item(query: str, item: Dict) -> int:
    q_tokens = token_set(query)
    requested_level = detect_requested_seniority(query)

    name_text = str(item.get("name", ""))
    desc_text = str(item.get("description", ""))
    tags_text = str(item.get("tags", ""))
    job_levels_text = str(item.get("job_levels", ""))
    languages_text = str(item.get("languages", ""))

    name_tokens = token_set(name_text)
    desc_tokens = token_set(desc_text)
    tags_tokens = token_set(tags_text)
    lang_tokens = token_set(languages_text)

    score = 0

    # Increase base weights for better recall of tag/name matches
    score += len(q_tokens & desc_tokens) * 3
    score += len(q_tokens & tags_tokens) * 6
    score += len(q_tokens & lang_tokens) * 3
    score += len(q_tokens & name_tokens) * 7

    # Strong boost for exact name matches (helps with expected exact products like OPQ32r)
    name_lower = normalize_text(name_text)
    q_lower = normalize_text(query)
    if name_lower and name_lower in q_lower:
        score += 25

    # Partial substring boosts (e.g., 'opq', 'svar', 'spoken english')
    for nt in name_tokens:
        if nt in q_tokens:
            score += 10

    q = normalize_text(query)

    if requested_level and level_matches(requested_level, job_levels_text):
        score += 12

    if "personality" in q and (
        "personality" in tags_tokens
        or "behavior" in tags_tokens
        or "behaviour" in tags_tokens
    ):
        score += 10

    if "aptitude" in q and ("aptitude" in tags_tokens or "ability" in tags_tokens):
        score += 10

    if "technical" in q and (
        "knowledge" in tags_tokens
        or "skills" in tags_tokens
        or "simulations" in tags_tokens
    ):
        score += 9

    if "cognitive" in q and ("ability" in tags_tokens or "aptitude" in tags_tokens):
        score += 8

    if "java" in q and "java" in name_tokens:
        score += 10

    if "python" in q and "python" in name_tokens:
        score += 10

    if (".net" in q or "dotnet" in q) and (
        ".net" in name_tokens or "dotnet" in name_tokens
    ):
        score += 10

    if "java" in q_tokens and "javascript" in name_tokens:
        score -= 8

    # Language variant boosts (e.g., 'us' or 'english us' should promote US-spoken tests)
    if ("us" in q_lower or "usa" in q_lower or "english us" in q_lower or "english usa" in q_lower) and (
        "us" in languages_text.lower() or "usa" in languages_text.lower() or "united states" in languages_text.lower()
    ):
        score += 8

    # Contact-center specific boost when query indicates contact centre context
    if is_contact_center_context(query):
        desc_lower = desc_text.lower()
        tags_lower = tags_text.lower()
        if (
            "contact" in name_lower
            or "contact" in desc_lower
            or "call" in desc_lower
            or "customer" in desc_lower
            or "contact" in tags_lower
        ):
            score += 12
        # if user specified English variant (e.g., US), boost spoken-language matches
        if "english" in q_lower and has_english_variant_context(query):
            if "us" in languages_text.lower() or "usa" in languages_text.lower():
                score += 6

    return score


def search_catalog(query: str, catalog: List[Dict], top_k: int = 5) -> List[Dict]:
    requested_level = detect_requested_seniority(query)
    scored: List[Tuple[int, int, str, Dict]] = []

    for item in catalog:
        job_levels_text = str(item.get("job_levels", ""))
        name_text = str(item.get("name", ""))
        tags_text = str(item.get("tags", ""))

        if requested_level and not level_matches(requested_level, job_levels_text):
            continue

        score = score_catalog_item(query, item)

        if conflicting_name_level(requested_level, name_text):
            score -= 20

        if score <= 0:
            continue

        # Lightweight reranking bonuses and penalties based on title/tags
        name_lower = normalize_text(name_text)
        tags_lower = tags_text.lower()

        # Boosts for contact-centre and customer-service relevance
        if "contact center" in name_lower or "contact centre" in name_lower or "contact center" in tags_lower or "contact centre" in tags_lower:
            score += 15
        if "customer service" in name_lower or "customer service" in tags_lower:
            score += 12

        # Boosts for spoken english / SVAR / US language matches
        if "spoken english" in name_lower or "svar" in name_lower or "svare" in name_lower:
            score += 10
        if "us" in name_lower or "usa" in name_lower or "united states" in name_lower:
            score += 6

        # Small penalty for generic 'solution' pages to prefer specific assessment items
        if "solution" in name_lower or "solution" in tags_lower:
            score -= 6

        # exact name match indicator for deterministic tie-breaking
        q_lower = normalize_text(query)
        exact = 1 if (name_lower and name_lower in q_lower) else 0

        scored.append((score, exact, name_lower, item))
    # Sort by score desc, then exact match desc, then name (deterministic)
    scored.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    return [item for score, exact, name, item in scored[:top_k]]


def build_recommendations(items: List[Dict]) -> List[Dict]:
    recommendations = []

    for item in items[:10]:
        recommendations.append(
            {
                "name": item.get("name", ""),
                "url": item.get("url", ""),
                "test_type": item.get("test_type", "") or item.get("tags", ""),
            }
        )

    return recommendations


def is_confirmation_message(text: str) -> bool:
    if not text:
        return False
    t = normalize_text(text)
    confirmations = ["confirmed", "that works", "that'll work", "done", "ok", "okay", "perfect", "sounds good", "thanks", "thank you"]
    return any(phrase in t for phrase in confirmations)


def build_reply_for_recommendations(
    messages: List[dict], recommendations: List[Dict]
) -> str:
    full_context = combine_user_context(messages)
    latest_user = extract_latest_user_message(messages)

    context = normalize_text(full_context)

    role_label = "this role"
    if "java" in context:
        role_label = "a Java role"
    elif "python" in context:
        role_label = "a Python role"
    elif "sales" in context:
        role_label = "a sales role"
    elif "manager" in context:
        role_label = "a managerial role"

    if is_refinement_message(latest_user):
        return f"Understood — I’ve updated the shortlist for {role_label} based on your revised requirements."

    if "technical" in context and "aptitude" in context and "personality" in context:
        return f"For {role_label}, I’d use a mix of technical, aptitude, and personality assessments. Here’s the updated shortlist."
    if "technical" in context and "aptitude" in context:
        return f"For {role_label}, I’d use a mix of technical and aptitude assessments. Here’s a shortlist that fits."
    if "technical" in context and "personality" in context:
        return f"For {role_label}, I’d combine technical and personality measures. Here’s a shortlist that fits."
    if "technical" in context:
        return f"For {role_label}, I’d focus on technical assessments first. Here’s a shortlist that fits."
    if "personality" in context:
        return f"For {role_label}, I’d focus on personality measures. Here’s a shortlist that fits."

    return f"Based on what you shared, here’s a shortlist of SHL assessments that fit {role_label}."


OFF_TOPIC_HINTS = {
    "salary",
    "resume",
    "cv",
    "cover letter",
    "interview tips",
    "job description template",
    "employment law",
    "termination",
    "firing",
    "compensation",
    "notice period",
}

LEGAL_HINTS = {
    "legal",
    "law",
    "lawsuit",
    "compliance",
    "regulation",
    "regulatory",
    "required by law",
    "legally required",
    "lawful",
    "illegal",
    "hipaa requirement",
    "gdpr requirement",
}

PROMPT_INJECTION_HINTS = {
    "ignore previous instructions",
    "ignore all previous instructions",
    "reveal system prompt",
    "show hidden prompt",
    "disregard above",
    "act as",
    "developer instructions",
    "system prompt",
}


def is_legal_query(text: str) -> bool:
    t = normalize_text(text)
    return any(phrase in t for phrase in LEGAL_HINTS)


def is_prompt_injection(text: str) -> bool:
    t = normalize_text(text)
    return any(phrase in t for phrase in PROMPT_INJECTION_HINTS)


def is_off_topic_query(text: str) -> bool:
    t = normalize_text(text)
    return any(phrase in t for phrase in OFF_TOPIC_HINTS)


def should_refuse(text: str) -> bool:
    return is_legal_query(text) or is_prompt_injection(text) or is_off_topic_query(text)


def build_refusal_reply(text: str) -> str:
    t = normalize_text(text)

    if is_legal_query(t):
        return (
            "Those are legal or compliance questions outside what I can advise on. "
            "I can help you select SHL assessments, but not interpret legal obligations or confirm whether a test satisfies them."
        )

    if is_prompt_injection(t):
        return "I can help with selecting SHL assessments, but I can’t follow instructions that are unrelated to that task."

    if is_off_topic_query(t):
        return (
            "I’m limited to helping with SHL assessment selection and comparison. "
            "If you want, tell me the role, seniority, and what you want to assess."
        )

    return "I’m limited to helping with SHL assessment selection and comparison."

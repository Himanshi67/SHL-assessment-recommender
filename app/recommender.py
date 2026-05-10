import logging
import re
from typing import Dict, List, Tuple

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

SYNONYMS = {
    "opq32r": "opq",
    "opq32": "opq",
    "opq": "opq",
    "svar": "svar",
    "spoken english": "spoken english",
}

ALIAS_MAP = {
    "opq": "occupational personality questionnaire opq32r",
    "gsa": "global skills assessment",
    "contact center": "contact center call simulation",
    "contact centre": "contact center call simulation",
    "coding": "smart interview live coding",
    "svar": "svar - spoken english",
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

SHL_URL_PREFIX = "https://www.shl.com/"

logger = logging.getLogger("shl_recommender.recommender")


def normalize_text(text: str) -> str:
    t = text.lower().replace("-", " ")
    t = re.sub(r"\s+", " ", t).strip()
    for key, value in SYNONYMS.items():
        t = t.replace(key, value)
    return t


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9\+#-]+", normalize_text(text))


def token_set(text: str) -> set:
    return {token for token in tokenize(text) if token not in STOPWORDS}


def extract_latest_user_message(messages: List[dict]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return str(message.get("content", "")).strip()
    return ""


def get_user_messages(messages: List[dict]) -> List[str]:
    return [str(m.get("content", "")).strip() for m in messages if m.get("role") == "user"]


def combine_user_context(messages: List[dict]) -> str:
    return " ".join(get_user_messages(messages)).strip()


def combine_message_context(messages: List[dict]) -> str:
    parts = [str(m.get("content", "")).strip() for m in messages if str(m.get("content", "")).strip()]
    return " ".join(parts).strip()


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
    return any(keyword in t for keyword in keywords)


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
    return any(variant in t for variant in variants)


def has_role_context(text: str) -> bool:
    return any(token in ROLE_HINTS for token in token_set(text))


def has_preference_context(text: str) -> bool:
    return any(token in PREFERENCE_HINTS for token in token_set(text))


def has_seniority_context(text: str) -> bool:
    return any(token in SENIORITY_HINTS for token in token_set(text))


def is_refinement_message(text: str) -> bool:
    return any(token in REFINEMENT_HINTS for token in token_set(text))


def should_ask_clarification(messages: List[dict]) -> bool:
    full_context = combine_user_context(messages)

    if not full_context:
        logger.debug("should_ask_clarification: empty full_context -> True")
        return True

    if not has_role_context(full_context):
        logger.debug("should_ask_clarification: role missing -> True")
        return True

    if is_contact_center_context(full_context):
        if not has_language_context(full_context):
            logger.debug("should_ask_clarification: contact-center and language missing -> True")
            return True
        if "english" in full_context.lower() and not has_english_variant_context(full_context):
            logger.debug("should_ask_clarification: english variant missing -> True")
            return True

    if not has_seniority_context(full_context) and not has_preference_context(full_context):
        logger.debug("should_ask_clarification: seniority & preference missing -> True")
        return True

    logger.debug("should_ask_clarification: all slots present -> False")
    return False


def get_clarifying_question(messages: List[dict]) -> str:
    full_context = combine_user_context(messages)
    full_context_lower = full_context.lower()

    if not has_role_context(full_context):
        return "Happy to help - what role are you hiring for?"

    if is_contact_center_context(full_context):
        if not has_language_context(full_context):
            return "Before I shape the stack, what language are the calls in?"
        if "english" in full_context_lower and not has_english_variant_context(full_context):
            return (
                "SHL has multiple English spoken-language variants in the catalog. "
                "Which fits your operation: US, UK, Australian, or Indian?"
            )

    if not has_seniority_context(full_context) and not has_preference_context(full_context):
        return (
            "Got it. What seniority level is the role, and do you want technical, "
            "aptitude, or personality assessments?"
        )

    if not has_seniority_context(full_context):
        return "What seniority level is this role - entry-level, mid-level, or manager/senior?"

    if not has_preference_context(full_context):
        return "Should I focus on technical skills tests, or also include aptitude or personality measures?"

    return "Could you share a bit more about the role requirements?"


def detect_requested_seniority(text: str) -> str:
    t = normalize_text(text)
    if "entry-level" in t or "entry level" in t or "junior" in t:
        return "entry"
    if "mid-level" in t or "mid level" in t or "mid-professional" in t or re.search(r"\bmid\b", t):
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
    if not requested_level:
        return True

    jl = normalize_text(job_levels_text)
    mapping = {
        "entry": ["entry level", "entry"],
        "mid": ["mid professional", "mid level", "mid"],
        "graduate": ["graduate"],
        "manager": ["manager", "front line manager"],
        "supervisor": ["supervisor"],
        "director": ["director"],
        "executive": ["executive"],
    }
    return any(level in jl for level in mapping.get(requested_level, []))


def conflicting_name_level(requested_level: str, name_text: str) -> bool:
    if requested_level != "entry":
        return False
    name_lower = normalize_text(name_text)
    return "advanced level" in name_lower or "advanced-level" in name_lower


def is_compare_request(text: str) -> bool:
    t = normalize_text(text)
    return any(phrase in t for phrase in ["difference between", "compare", "vs", "versus"])


def find_items_by_name(text: str, catalog: List[Dict], top_k: int = 2) -> List[Dict]:
    q_tokens = token_set(text)
    q_lower = normalize_text(text)
    scored: List[Tuple[int, Dict]] = []

    for item in catalog:
        name = str(item.get("name", ""))
        name_lower = normalize_text(name)
        name_tokens = token_set(name)
        score = len(q_tokens & name_tokens)

        if name_lower and name_lower in q_lower:
            score += 100

        for alias, canonical in ALIAS_MAP.items():
            if alias in q_lower and canonical in name_lower:
                score += 80
            if alias in q_lower and alias in name_lower:
                score += 60

        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda row: row[0], reverse=True)
    return [item for _, item in scored[:top_k]]


def build_comparison_reply(items: List[Dict]) -> str:
    if len(items) < 2:
        return "I could not confidently identify both SHL assessments to compare from the catalog."

    first, second = items[0], items[1]
    first_name = first.get("name", "First assessment")
    second_name = second.get("name", "Second assessment")
    first_type = first.get("test_type", "") or first.get("tags", "specific assessment areas")
    second_type = second.get("test_type", "") or second.get("tags", "specific assessment areas")
    first_duration = first.get("duration", "") or "not specified"
    second_duration = second.get("duration", "") or "not specified"

    return (
        f"{first_name} is mainly used for {str(first_type).lower()}, while {second_name} "
        f"is used for {str(second_type).lower()}. If your goal is to compare them practically, "
        f"the main difference is the kind of signal each one adds to hiring decisions. In terms "
        f"of duration, {first_name} takes {first_duration} and {second_name} takes {second_duration}."
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
    score += len(q_tokens & desc_tokens) * 3
    score += len(q_tokens & tags_tokens) * 6
    score += len(q_tokens & lang_tokens) * 3
    score += len(q_tokens & name_tokens) * 7

    name_lower = normalize_text(name_text)
    q_lower = normalize_text(query)
    if name_lower and name_lower in q_lower:
        score += 40

    for alias, canonical in ALIAS_MAP.items():
        if alias in q_lower and canonical in name_lower:
            score += 60

    for name_token in name_tokens:
        if name_token in q_tokens:
            score += 12

    if requested_level and level_matches(requested_level, job_levels_text):
        score += 12

    if "personality" in q_lower and {"personality", "behavior", "behaviour"} & tags_tokens:
        score += 10
    if "aptitude" in q_lower and {"aptitude", "ability"} & tags_tokens:
        score += 10
    if "technical" in q_lower and {"knowledge", "skills", "simulations"} & tags_tokens:
        score += 9
    if "cognitive" in q_lower and {"ability", "aptitude"} & tags_tokens:
        score += 8
    if "java" in q_lower and "java" in name_tokens:
        score += 10
    if "python" in q_lower and "python" in name_tokens:
        score += 10
    if (".net" in q_lower or "dotnet" in q_lower) and (".net" in name_tokens or "dotnet" in name_tokens):
        score += 10
    if "java" in q_tokens and "javascript" in name_tokens:
        score -= 8

    if (
        "us" in q_lower
        or "usa" in q_lower
        or "english us" in q_lower
        or "english usa" in q_lower
    ) and (
        "us" in languages_text.lower()
        or "usa" in languages_text.lower()
        or "united states" in languages_text.lower()
    ):
        score += 8

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
        if "english" in q_lower and has_english_variant_context(query):
            if "us" in languages_text.lower() or "usa" in languages_text.lower():
                score += 6

    return score


def search_catalog(query: str, catalog: List[Dict], top_k: int = 5) -> List[Dict]:
    requested_level = detect_requested_seniority(query)
    scored: List[Tuple[int, int, str, Dict]] = []
    q_lower = normalize_text(query)

    for item in catalog:
        job_levels_text = str(item.get("job_levels", ""))
        name_text = str(item.get("name", ""))
        tags_text = str(item.get("tags", ""))
        name_lower = normalize_text(name_text)

        alias_matched = False
        for alias, canonical in ALIAS_MAP.items():
            if alias in q_lower and canonical in name_lower:
                scored.append((9999, 1, name_lower, item))
                alias_matched = True
                break
        if alias_matched:
            continue

        if requested_level and not level_matches(requested_level, job_levels_text):
            continue

        score = score_catalog_item(query, item)
        if conflicting_name_level(requested_level, name_text):
            score -= 20
        if score <= 0:
            continue

        tags_lower = tags_text.lower()
        if (
            "contact center" in name_lower
            or "contact centre" in name_lower
            or "contact center" in tags_lower
            or "contact centre" in tags_lower
        ):
            score += 15
        if "customer service" in name_lower or "customer service" in tags_lower:
            score += 12
        if "spoken english" in name_lower or "svar" in name_lower or "svare" in name_lower:
            score += 10
        if "us" in name_lower or "usa" in name_lower or "united states" in name_lower:
            score += 6
        if "solution" in name_lower or "solution" in tags_lower:
            if not (name_lower and name_lower in q_lower):
                score -= 20

        exact = 1 if (name_lower and name_lower in q_lower) else 0
        scored.append((score, exact, name_lower, item))

    scored.sort(key=lambda row: (row[0], row[1], row[2]), reverse=True)
    return [item for _, _, _, item in scored[:top_k]]


def is_valid_shl_catalog_url(url: str) -> bool:
    return isinstance(url, str) and url.startswith(SHL_URL_PREFIX)


def build_recommendations(items: List[Dict], max_items: int = 10) -> List[Dict]:
    recommendations: List[Dict] = []
    seen_urls = set()

    for item in items:
        url = str(item.get("url", "")).strip()
        if not is_valid_shl_catalog_url(url):
            continue

        normalized_url = url.lower()
        if normalized_url in seen_urls:
            continue

        name = str(item.get("name", "")).strip()
        if not name:
            continue

        test_type = str(item.get("test_type", "")).strip() or str(item.get("tags", "")).strip()
        if not test_type:
            test_type = "Assessment"

        recommendations.append({"name": name, "url": url, "test_type": test_type})
        seen_urls.add(normalized_url)

        if len(recommendations) >= max_items:
            break

    return recommendations


def validate_recommendations(recommendations: List[Dict]) -> bool:
    count = len(recommendations)
    if count != 0 and not (1 <= count <= 10):
        return False

    seen_urls = set()
    for rec in recommendations:
        name = str(rec.get("name", "")).strip()
        test_type = str(rec.get("test_type", "")).strip()
        url = str(rec.get("url", "")).strip()

        if not name or not test_type or not is_valid_shl_catalog_url(url):
            return False

        normalized_url = url.lower()
        if normalized_url in seen_urls:
            return False
        seen_urls.add(normalized_url)

    return True


def is_confirmation_message(text: str) -> bool:
    if not text:
        return False
    t = normalize_text(text)
    if "?" in text:
        return False
    if is_refinement_message(t) or is_compare_request(t):
        return False
    if any(token in t for token in [" but ", " also ", " and ", " instead ", " add ", " include ", " compare "]):
        return False

    confirmations = {
        "confirmed",
        "that covers it",
        "that covers it all",
        "that works",
        "that'll work",
        "done",
        "ok",
        "okay",
        "perfect",
        "sounds good",
        "thanks",
        "thank you",
    }
    cleaned = re.sub(r"[^a-z0-9'\s]", "", t).strip()
    return cleaned in confirmations


def build_reply_for_recommendations(messages: List[dict], recommendations: List[Dict]) -> str:
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
        return f"Understood - I have updated the shortlist for {role_label} based on your revised requirements."
    if "technical" in context and "aptitude" in context and "personality" in context:
        return f"For {role_label}, I would use a mix of technical, aptitude, and personality assessments. Here is the updated shortlist."
    if "technical" in context and "aptitude" in context:
        return f"For {role_label}, I would use a mix of technical and aptitude assessments. Here is a shortlist that fits."
    if "technical" in context and "personality" in context:
        return f"For {role_label}, I would combine technical and personality measures. Here is a shortlist that fits."
    if "technical" in context:
        return f"For {role_label}, I would focus on technical assessments first. Here is a shortlist that fits."
    if "personality" in context:
        return f"For {role_label}, I would focus on personality measures. Here is a shortlist that fits."
    return f"Based on what you shared, here is a shortlist of SHL assessments that fit {role_label}."


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
            "I can help you select SHL assessments, but not interpret legal obligations "
            "or confirm whether a test satisfies them."
        )
    if is_prompt_injection(t):
        return (
            "I can help with selecting SHL assessments, but I cannot follow instructions "
            "that are unrelated to that task."
        )
    if is_off_topic_query(t):
        return (
            "I am limited to helping with SHL assessment selection and comparison. "
            "If you want, tell me the role, seniority, and what you want to assess."
        )
    return "I am limited to helping with SHL assessment selection and comparison."

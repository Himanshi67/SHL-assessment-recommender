import logging
from fastapi import APIRouter
from app.schemas import ChatRequest, ChatResponse, Recommendation
from app.catalog_loader import load_clean_catalog
from app.recommender import (
    extract_latest_user_message,
    combine_user_context,
    should_ask_clarification,
    get_clarifying_question,
    is_compare_request,
    find_items_by_name,
    build_comparison_reply,
    search_catalog,
    build_recommendations,
    build_reply_for_recommendations,
    should_refuse,
    build_refusal_reply,
    has_role_context,
    has_seniority_context,
    has_preference_context,
    has_language_context,
    has_english_variant_context,
    is_contact_center_context,
)
from app.prompts import DEFAULT_PROMPT, RECOMMEND_PROMPT_TEMPLATE

router = APIRouter()
logger = logging.getLogger("shl_recommender.router")


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    catalog = load_clean_catalog()
    messages = [message.model_dump() for message in payload.messages]

    latest_user_message = extract_latest_user_message(messages)
    full_user_context = combine_user_context(messages)

    # Build the LLM prompt we would send (and log it). This ensures the prompt
    # explicitly instructs the model to review the full conversation history
    # and not ask questions already answered.
    try:
        messages_text = "\n".join(f"{m.get('role')}: {m.get('content')}" for m in messages)
        final_prompt = RECOMMEND_PROMPT_TEMPLATE.format(messages=messages_text, query=full_user_context, k=5)
    except Exception:
        final_prompt = DEFAULT_PROMPT + "\nUser: " + full_user_context

    logger.debug("LLM prompt: %s", final_prompt)

    if should_refuse(latest_user_message):
        return ChatResponse(
            reply=build_refusal_reply(latest_user_message),
            recommendations=[],
            end_of_conversation=False,
        )

    if is_compare_request(latest_user_message):
        compare_items = find_items_by_name(latest_user_message, catalog, top_k=2)
        comparison_reply = build_comparison_reply(compare_items)

        return ChatResponse(reply=comparison_reply, recommendations=[], end_of_conversation=False)

    # Decide whether to ask a clarification or to run retrieval. We prefer
    # retrieval when we already have role + at least one constraint (seniority,
    # language, or preference). This avoids re-asking information the user has
    # already provided.
    clarifying_needed = should_ask_clarification(messages)

    role_present = has_role_context(full_user_context)
    seniority_present = has_seniority_context(full_user_context)
    preference_present = has_preference_context(full_user_context)
    language_present = has_language_context(full_user_context)
    english_variant_present = has_english_variant_context(full_user_context)

    can_search = False
    if role_present and (seniority_present or preference_present):
        can_search = True
    if is_contact_center_context(full_user_context) and language_present and english_variant_present:
        can_search = True

    if clarifying_needed and not can_search:
        return ChatResponse(
            reply=get_clarifying_question(messages),
            recommendations=[],
            end_of_conversation=False,
        )

    # Use the combined user context (all user messages) as the search query so the
    # engine is stateless and always considers the full conversation history.
    # Debug: log the final query used for retrieval to aid troubleshooting.
    # Enrich the query with domain-specific keywords to improve retrieval for
    # contact-centre and language-specific requests.
    enriched_query = full_user_context.lower()
    if "contact centre" in enriched_query or "contact center" in enriched_query:
        enriched_query += " contact center customer service inbound calls call simulation"

    if "english" in enriched_query and (" us" in enriched_query or "us" in enriched_query or "usa" in enriched_query):
        enriched_query += " spoken english usa svar us"

    logger.debug("search_query: %s", enriched_query)
    matches = search_catalog(enriched_query, catalog, top_k=5)
    recommendations = build_recommendations(matches)

    if not recommendations:
        return ChatResponse(
            reply=(
                "I could not find a strong SHL catalog match yet. Please share the role, "
                "seniority, and any must-have skills."
            ),
            recommendations=[],
            end_of_conversation=False,
        )

    # When we have a shortlist, return it but only mark end_of_conversation=True
    # if the latest user message clearly indicates completion (confirmation).
    from app.recommender import is_confirmation_message

    confirmed = is_confirmation_message(latest_user_message)

    return ChatResponse(
        reply=build_reply_for_recommendations(messages, recommendations),
        recommendations=[Recommendation(**rec) for rec in recommendations],
        end_of_conversation=bool(confirmed),
    )

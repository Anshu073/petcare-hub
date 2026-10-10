import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MODELS = ["gemini-flash-lite-latest", "gemini-flash-latest"]


def _post_gemini(body, timeout):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[AI Helper] GEMINI_API_KEY is missing in environment variables")
        return None

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    for model in MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        try:
            response = requests.post(url, headers=headers, json=body, timeout=timeout)
        except requests.exceptions.RequestException as e:
            print(f"[AI Helper] {model} failed: {e}")
            continue

        if response.status_code == 200:
            return response.json()
        print(f"[AI Helper] {model} error {response.status_code}: {response.text[:200]}")

    return None


def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def get_sentiment(comment_text):
    fallback = {"sentiment": None, "reason": None}

    if not comment_text or not comment_text.strip():
        return fallback

    try:
        body = {
            "system_instruction": {
                "parts": [{"text": "You are a sentiment classifier. The input comment may be in any language (English, Hindi, Hinglish, etc). Always respond in English regardless of input language. Reply ONLY with valid JSON in this exact shape, nothing else: {\"sentiment\": \"positive\" or \"neutral\" or \"negative\", \"reason\": \"short reason under 12 words\"}"}]
            },
            "contents": [
                {"parts": [{"text": comment_text}]}
            ],
            "generationConfig": {"responseMimeType": "application/json"}
        }

        data = _post_gemini(body, 8)
        if not data:
            return fallback

        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = _extract_json(raw_text)

        sentiment = str(result.get("sentiment", "")).lower()
        if sentiment not in ("positive", "neutral", "negative"):
            return fallback

        return {"sentiment": sentiment, "reason": result.get("reason")}

    except requests.exceptions.RequestException as e:
        print(f"[AI Helper] Network/API error: {e}")
        return fallback
    except (KeyError, json.JSONDecodeError, IndexError, TypeError, AttributeError) as e:
        print(f"[AI Helper] Unexpected response format: {e}")
        return fallback


def get_chat_reply(user_message, conversation_history):
    fallback = "Sorry, I'm having trouble responding right now. Please try again in a moment."

    if not user_message or not user_message.strip():
        return fallback

    try:
        system_text = (
            "You are the friendly customer support assistant for PetCareHub, "
            "a pet care platform where customers can book vet appointments, "
            "order pet products/food, and get products delivered.\n\n"
            "LANGUAGE RULE (MOST IMPORTANT): Look at the customer's LATEST message and reply in the same language and style. "
            "English message -> reply in English. "
            "Hindi in Devanagari script -> reply in Hindi (Devanagari). "
            "Hinglish (Hindi written in English letters, e.g. 'pet adoption provide krte ho?' or 'mera order kab aayega') "
            "-> reply in Hinglish (Hindi in English letters). NEVER reply in English to a Hinglish message.\n\n"
            "FORMAT RULE: Reply in plain text only. Do not use markdown, asterisks, "
            "bullet symbols or bold.\n\n"
            "PLATFORM KNOWLEDGE:\n"
            "- Product orders (pet food, toys, accessories) are paid ONLINE ONLY via Razorpay. "
            "There is no cash-on-delivery for products.\n"
            "- Vet appointments can be paid in TWO ways: 'Online' (upfront via Razorpay) or "
            "'Pay at Clinic' (cash, paid in person at the appointment).\n"
            "- PetCareHub itself does NOT list or sell pets for adoption. Its Adoption page is a "
            "partnership page with our welfare partner Adoption Home Ahmedabad (owner: Naitik Bhatt). "
            "The page has links to their website and Instagram, where users can see rescued pets and "
            "contact them to adopt, plus our No Objection Certificate and Appreciation Letter from them. "
            "The adoption process is handled by Adoption Home Ahmedabad, not by PetCareHub. "
            "Never invent adoption fees, process steps or pet availability; tell users to check "
            "the partner's website or Instagram from the Adoption page.\n"
            "- STRIKE SYSTEM (applies ONLY to 'Pay at Clinic' vet appointments, never to products "
            "or online-paid appointments): if a customer books a 'Pay at Clinic' appointment and "
            "doesn't show up (marked absent by the vet), they get 1 strike. After 3 strikes, their "
            "account is cash-blocked — they can no longer choose 'Pay at Clinic' and must pay online "
            "for all future vet appointments. If a customer asks why they can't select 'Pay at Clinic' "
            "anymore, this strike system is the reason.\n"
            "- ORDER CANCELLATION (shop products): a customer can cancel an order only BEFORE it is assigned "
            "to a delivery boy. Once it is assigned, cancellation is not possible. An order can contain items "
            "from different vendors and each vendor's items are cancelled separately, only until that vendor's "
            "items are assigned. After a valid cancellation the refund is processed within 5-7 business days.\n"
            "- APPOINTMENT CANCELLATION: customers can NOT cancel an appointment themselves. Appointments get "
            "cancelled automatically in these cases: (1) the vet is offline and the appointment is within 3 hours, "
            "(2) the vet does not respond to the request until 30 minutes before the slot, "
            "(3) the customer does not complete payment within about 30 minutes after the vet accepts. "
            "A vet can also reject a request. Cancelled appointments show in 'My Appointments'.\n"
            "- APPOINTMENT REFUNDS: if an online-paid appointment gets cancelled, the amount is credited back to the "
            "original payment method within 2-3 working days. If a customer paid online and does not attend "
            "(marked absent), there is NO refund. Cash ('Pay at Clinic') appointments have nothing to refund.\n"
            "- If asked about any policy, fee, timing or rule that is NOT listed above, do NOT guess or invent it. "
            "Say you are not sure and ask the customer to check 'My Orders', 'My Appointments' or the Contact & FAQ page.\n\n"
            "Keep replies short (2-4 sentences), friendly, and helpful. "
            "If you don't know something specific about the user's account/order, "
            "tell them to check 'My Orders' or 'My Appointments' in their profile, "
            "or contact support directly.\n\n"
            "FINAL REMINDER: reply in the same language style as the customer's latest message "
            "(Hinglish message = Hinglish reply)."
        )

        contents = []
        for turn in conversation_history:
            contents.append({
                "role": turn["role"],
                "parts": [{"text": turn["text"]}]
            })
        contents.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })

        body = {
            "system_instruction": {"parts": [{"text": system_text}]},
            "contents": contents
        }

        data = _post_gemini(body, 12)
        if not data:
            return fallback

        reply_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return reply_text.strip()

    except requests.exceptions.RequestException as e:
        print(f"[AI Helper] Chatbot network error: {e}")
        return fallback
    except (KeyError, IndexError, TypeError) as e:
        print(f"[AI Helper] Chatbot unexpected response: {e}")
        return fallback
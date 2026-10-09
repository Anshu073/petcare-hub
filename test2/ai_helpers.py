import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"


def _post_gemini(body, timeout):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[AI Helper] GEMINI_API_KEY is missing in environment variables")
        return None

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    for attempt in range(2):
        response = requests.post(GEMINI_URL, headers=headers, json=body, timeout=timeout)
        if response.status_code in (429, 500, 503) and attempt == 0:
            print(f"[AI Helper] Gemini {response.status_code}, retrying once...")
            time.sleep(1.5)
            continue
        if response.status_code != 200:
            print(f"[AI Helper] Gemini error {response.status_code}: {response.text[:300]}")
        return response.json()
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
            "LANGUAGE RULE: Always reply in the same language/style the customer "
            "is currently using. If they write in English, reply in English. "
            "If they switch to Hindi or Hinglish, switch too. Match their tone naturally.\n\n"
            "FORMAT RULE: Reply in plain text only. Do not use markdown, asterisks, "
            "bullet symbols or bold.\n\n"
            "PLATFORM KNOWLEDGE:\n"
            "- Product orders (pet food, toys, accessories) are paid ONLINE ONLY via Razorpay. "
            "There is no cash-on-delivery for products.\n"
            "- Vet appointments can be paid in TWO ways: 'Online' (upfront via Razorpay) or "
            "'Pay at Clinic' (cash, paid in person at the appointment).\n"
            "- PetCareHub has an Adoption page where users can view pets available for adoption, "
            "listed with our partner Adoption Home Ahmedabad.\n"
            "- STRIKE SYSTEM (applies ONLY to 'Pay at Clinic' vet appointments, never to products "
            "or online-paid appointments): if a customer books a 'Pay at Clinic' appointment and "
            "doesn't show up (marked absent by the vet), they get 1 strike. After 3 strikes, their "
            "account is cash-blocked — they can no longer choose 'Pay at Clinic' and must pay online "
            "for all future vet appointments. If a customer asks why they can't select 'Pay at Clinic' "
            "anymore, this strike system is the reason.\n\n"
            "Keep replies short (2-4 sentences), friendly, and helpful. "
            "If you don't know something specific about the user's account/order, "
            "tell them to check 'My Orders' or 'My Appointments' in their profile, "
            "or contact support directly."
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
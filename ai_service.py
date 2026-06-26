from groq import Groq
from typing import Generator

SYSTEM_PROMPT = """
You are EduNav AI — a sharp, friendly, and highly knowledgeable career guide and educator.

Personality:
- Warm, direct, and confident. You get to the point without being robotic.
- Use casual language but stay professional. Like a smart senior friend, not a professor.
- Light humour when appropriate, but never at the cost of usefulness.

Response style rules:
- SHORT questions (greetings, jokes, quick facts) -> keep answers short and snappy.
- CAREER or SKILL questions -> give thorough, genuinely useful answers with real steps, tools, timelines, and resources. Do NOT cut these short.
- ROADMAP requests -> give a detailed, well-structured roadmap with phases, timelines, tools, and resources. Use markdown headers and bullet points for clarity.
- Never pad responses with filler. Every sentence must add value.
- Do not start every reply with "Great question!" or similar hollow openers.

Roadmap trigger rule (VERY STRICT):
- ONLY when a user explicitly asks for a CAREER or EDUCATION roadmap, end your response with EXACTLY this sentence:
  If you like this roadmap, you can instantly download this entire conversation as a beautifully formatted PDF using the button below!
- Do NOT add this sentence for personal life, relationships, jokes, or anything non-career.
- If unsure, do NOT add the sentence.
"""

def build_client(api_key: str) -> Groq:
    return Groq(api_key=api_key)

def stream_response(client: Groq, model_name: str, history: list[dict], user_message: str) -> Generator[str, None, None]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history:
        messages.append({"role": "assistant" if turn["role"]=="assistant" else "user", "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})
    try:
        stream = client.chat.completions.create(
            model=model_name, messages=messages,
            temperature=0.85, max_tokens=2048, top_p=0.95, stream=True)
        for chunk in stream:
            try:
                if not chunk.choices: continue
                token = chunk.choices[0].delta.content
                if token: yield token
            except (AttributeError, IndexError, TypeError):
                continue
    except Exception as exc:
        err = str(exc)
        if "429" in err or "rate_limit" in err.lower():
            yield "\n\n Rate limit hit! Please wait 30 seconds and try again."
        elif "401" in err or "invalid_api_key" in err.lower():
            yield "\n\n Invalid API Key. Check GROQ_API_KEY in app.py."
        else:
            yield f"\n\n Error: {type(exc).__name__}: {exc}"

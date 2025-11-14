# utils/reflection.py
import os

def reflect(user_msg: str, context_messages=None) -> str:
    """Return Ghost Malone's reply. Uses OpenAI if OPENAI_API_KEY is set; else echoes."""
    api_key = os.getenv("OPENAI_API_KEY")
    system_prompt = (
        "You are Ghost Malone — a calm, humorous listener. "
        "Be sincere, brief (<80 words), and reflective."
    )
    if not api_key:
        return f"👻 (dev) I hear you: {user_msg}"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        msgs = [{"role": "system", "content": system_prompt}]
        if context_messages:
            msgs.extend(context_messages[-6:])  # last 3 exchanges (user/assistant)
        msgs.append({"role": "user", "content": user_msg})
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=msgs,
            max_tokens=200,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"👻 (dev) Error talking to model: {e}\nBut I still hear you: {user_msg}"

import time
from servers.emotion_server import analyze as emo_tool, _analyze
from servers.memory_server import remember_event, recall, reflect, recall_facts, search, delete_by_id, list_items

def t(msg):
    # Use tool (decorated) or fallback to _analyze
    try:
        emo = emo_tool(msg)  # fastmcp tool wrapper is callable
    except Exception:
        emo = _analyze(msg)
    evt = {
        "id": f"evt-{int(time.time()*1000)}",
        "ts": int(time.time()),
        "role": "user",
        "text": msg,
        "emotion": emo,
        "sincerity": 80,
    }
    print("remember_event:", remember_event(evt, promote=True))

if __name__ == "__main__":
    t("I am REALLY happy!!! ❤️")
    t("not happy about this, kinda anxious")
    print("recall:", recall(k=3))
    print("reflect:", reflect())
    print("facts:", recall_facts())
    print("search episodes:", search("happy", tier="episodes", k=5))
    # Try delete-by-id on the newest STM item
    items = list_items("stm", k=1)["items"]
    if items:
        last_id = items[-1]["id"]
        print("delete:", delete_by_id(last_id))

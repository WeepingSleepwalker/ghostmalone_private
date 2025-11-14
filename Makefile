# Makefile — Ghost Malone Hackathon

PYTHON := python
export PYTHONPATH := .

test:
	@echo "🔍 Running Ghost Malone smoke tests..."
	@$(PYTHON) -m pip install -q fastmcp gradio || true
	@$(PYTHON) -m tests.smoke_test
	@echo "\n✅ Tests complete."

emotion:
	@echo "💡 Emotion server quick check"
	@$(PYTHON) -c "from servers.emotion_server import _analyze; \
print(_analyze('I am really happy!!! ❤️')); \
print(_analyze('not happy about this, kinda anxious'))"

memory:
	@echo "💾 Memory server quick check"
	@$(PYTHON) -c "import time; \
from servers.memory_server import remember_event, recall; \
from servers.emotion_server import _analyze; \
evt={'id':'evt-test','ts':int(time.time()),'text':'testing calm tone','emotion':_analyze('feeling calm and kind'),'sincerity':88}; \
print(remember_event(evt, promote=True)); \
print(recall(k=2))"

run:
	@echo "🚀 Launching Ghost Malone Gradio app..."
	@$(PYTHON) app.py


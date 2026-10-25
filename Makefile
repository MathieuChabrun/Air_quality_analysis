.PHONY: install run test
install:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
run:
	streamlit run app.py
test:
	python -m pytest tests -q

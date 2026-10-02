"""Rebuild CSV and SQLite analysis outputs from the unchanged original CSV."""

import json
from src.payments import prepare_data, write_outputs

if __name__ == "__main__":
    data = prepare_data()
    write_outputs(data)
    print(json.dumps(data.summary, indent=2, ensure_ascii=True))

"""Validate pilot results against the schema."""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.normalization.schema import validate_app_result

with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'pilot_results.json'), 'r', encoding='utf-8') as f:
    pilot = json.load(f)

print(f"Validating {len(pilot)} pilot results...\n")

all_valid = True
for app in pilot:
    errors = validate_app_result(app)
    if errors:
        all_valid = False
        print(f"[FAIL] {app['app']} (ID {app['id']}):")
        for e in errors:
            print(f"   - {e}")
    else:
        print(f"[OK] {app['app']} (ID {app['id']}): VALID")

print(f"\n{'All valid!' if all_valid else 'Errors found - fix before proceeding.'}")

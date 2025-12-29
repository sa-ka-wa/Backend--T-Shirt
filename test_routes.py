# test_routes.py
from backend_app import create_app

app = create_app()

print("=== Registered Routes ===")
for rule in app.url_map.iter_rules():
    if rule.endpoint.startswith('users.'):
        print(f"{rule.endpoint}: {rule.rule} - {list(rule.methods)}")
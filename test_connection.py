from kite_login import get_kite_instance

kite = get_kite_instance()
profile = kite.profile()
print(f"✅ Logged in as: {profile['user_name']} ({profile['user_id']})")

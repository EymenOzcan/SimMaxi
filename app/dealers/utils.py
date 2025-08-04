
import secrets
import string
from django.apps import apps  # ⛔ circular import'u önlemek için önemli

# 🔐 Dealer için güvenli base62 ID üretici
BASE62_ALPHABET = string.digits + string.ascii_letters

def generate_base62_id(length=8):
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))


# 🚫 DİKKAT: BURADA DealerRole DOĞRUDAN İMPORT EDİLMEMELİ
# from app.dealers.models import DealerRole  ⛔ bunu siliyoruz

# ✅ get_model ile çalışırken importu geciktiriyoruz, böylece circular import olmaz
def get_user_role(user, dealer):
    DealerRole = apps.get_model('dealers', 'DealerRole')
    try:
        return DealerRole.objects.get(user=user, dealer=dealer).role
    except DealerRole.DoesNotExist:
        return None

def is_dealer_admin(user, dealer):
    return get_user_role(user, dealer) == "admin"

def is_dealer_editor(user, dealer):
    return get_user_role(user, dealer) in ["admin", "editor"]
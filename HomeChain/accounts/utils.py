from stellar_sdk import Keypair
import requests
from django.conf import settings
from django.core.files.storage import default_storage
import os
import uuid

def create_stellar_account():
    """Generate and fund a new Stellar account on testnet"""
    try:
        keypair = Keypair.random()
        
        # Fund with Friendbot on testnet
        if settings.STELLAR_NETWORK == 'testnet':
            url = f"https://friendbot.stellar.org?addr={keypair.public_key}"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                print(f"✅ Stellar account created: {keypair.public_key}")
            else:
                print(f"⚠️ Stellar account created but funding failed: {keypair.public_key}")
        
        return {
            'public_key': keypair.public_key,
            'secret_key': keypair.secret,
        }
    except Exception as e:
        print(f"❌ Failed to create Stellar account: {str(e)}")
        # Return placeholder for development
        return {
            'public_key': f'G{uuid.uuid4().hex[:55]}',
            'secret_key': f'S{uuid.uuid4().hex[:55]}',
        }

def get_stellar_balance(public_key):
    """Get XLM balance of a Stellar account"""
    try:
        url = f"https://horizon-testnet.stellar.org/accounts/{public_key}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            balances = data.get('balances', [])
            for balance in balances:
                if balance.get('asset_type') == 'native':
                    return float(balance.get('balance', 0))
        return 0.0
    except:
        return 0.0

def upload_to_storage(file, path_prefix='documents'):
    """Upload file to storage and return path"""
    ext = file.name.split('.')[-1]
    filename = f"{path_prefix}/{uuid.uuid4()}.{ext}"
    saved_path = default_storage.save(filename, file)
    return saved_path

def validate_file_size(file, max_size_mb=10):
    """Validate file size"""
    if file.size > max_size_mb * 1024 * 1024:
        return False, f"File size exceeds {max_size_mb}MB"
    return True, ""

def validate_file_extension(file, allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']):
    """Validate file extension"""
    ext = file.name.split('.')[-1].lower()
    if ext not in allowed_extensions:
        return False, f"File extension not allowed. Allowed: {', '.join(allowed_extensions)}"
    return True, ""
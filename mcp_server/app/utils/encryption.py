from cryptography.fernet import Fernet
import base64
import os
from typing import Optional

# Generate a key or load from environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a key if not provided
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"Generated encryption key: {ENCRYPTION_KEY}")
    print("Add this to your .env file as ENCRYPTION_KEY for production use.")

# Create Fernet cipher
cipher = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

def encrypt_text(text: str) -> str:
    """Encrypt text using Fernet symmetric encryption (AES-128 in CBC mode with PKCS7 padding)."""
    if not text:
        return ""
    
    # Convert text to bytes and encrypt
    text_bytes = text.encode()
    encrypted_bytes = cipher.encrypt(text_bytes)
    
    # Convert encrypted bytes to base64 string for storage
    return base64.b64encode(encrypted_bytes).decode()

def decrypt_text(encrypted_text: str) -> Optional[str]:
    """Decrypt text that was encrypted with Fernet."""
    if not encrypted_text:
        return None
    
    try:
        # Convert base64 string to bytes and decrypt
        encrypted_bytes = base64.b64decode(encrypted_text)
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        
        # Convert decrypted bytes back to string
        return decrypted_bytes.decode()
    except Exception as e:
        print(f"Error decrypting text: {e}")
        return None

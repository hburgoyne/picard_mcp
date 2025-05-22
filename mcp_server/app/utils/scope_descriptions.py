"""
OAuth scope descriptions for user consent page.
"""

# Map of scope names to user-friendly descriptions
SCOPE_DESCRIPTIONS = {
    "memories:read": "Read your memories",
    "memories:write": "Create and update your memories",
    "memories:delete": "Delete your memories",
    "profile:read": "Read your profile information",
    "profile:write": "Update your profile information",
    "offline_access": "Access your data when you're not using the application",
}

def get_scope_descriptions(scopes_string: str) -> list:
    """
    Convert a space-separated scope string into a list of (scope, description) tuples.
    
    Args:
        scopes_string: Space-separated list of scopes
        
    Returns:
        List of (scope, description) tuples
    """
    scopes = scopes_string.split()
    result = []
    
    for scope in scopes:
        description = SCOPE_DESCRIPTIONS.get(scope, f"Access to {scope}")
        result.append((scope, description))
    
    return result

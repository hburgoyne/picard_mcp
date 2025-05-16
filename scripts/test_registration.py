from mcp.server.auth.handlers.register import RegistrationHandler
from mcp.server.auth.provider import OAuthAuthorizationServerProvider
from mcp.server.auth.settings import ClientRegistrationOptions

# Create a test registration handler
handler = RegistrationHandler(
    provider=OAuthAuthorizationServerProvider(),
    options=ClientRegistrationOptions()
)

# Print the expected registration format
print("Expected registration format:")
print(handler.__annotations__)

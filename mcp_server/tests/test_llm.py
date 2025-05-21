import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

@pytest.fixture
def auth_headers():
    """Create authentication headers for test user."""
    # Create access token for test user (this is a simplified version for testing)
    return {"Authorization": "Bearer test_token"}

@patch("app.utils.langchain_utils.query_memories_with_langchain")
def test_query_memories(mock_query, client: TestClient, auth_headers):
    """Test querying memories with LLM."""
    # Mock the LangChain query function
    mock_query.return_value = "This is a test response from the LLM."
    
    # Test the query endpoint
    query_data = {
        "query": "What did I do yesterday?",
        "persona": "default",
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    response = client.post("/llm/query", json=query_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == query_data["query"]
    assert data["persona"] == query_data["persona"]
    assert data["response"] == "This is a test response from the LLM."
    
    # Verify that the mock was called with the correct arguments
    mock_query.assert_called_once()

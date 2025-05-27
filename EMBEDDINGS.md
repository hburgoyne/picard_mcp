# Vector Embeddings Implementation

## Overview

The Picard MCP system now includes comprehensive vector embeddings functionality for semantic search of memories. This implementation uses OpenAI's text-embedding-3-small model and PostgreSQL's pgvector extension for efficient similarity search.

## Features Implemented

### ✅ Core Infrastructure
- **OpenAI API v1.x Integration**: Upgraded from legacy 0.28.0 to modern >=1.0.0 API
- **Automatic Embedding Generation**: All memories automatically get vector embeddings upon creation/update
- **Asynchronous Processing**: Embeddings are generated asynchronously for better performance
- **Strict Error Handling**: Comprehensive error handling for OpenAI API failures

### ✅ Database Integration
- **Vector Storage**: Uses pgvector extension with 1536-dimension vectors (text-embedding-3-small)
- **Cosine Similarity Search**: Efficient semantic search using pgvector's native operators
- **Permission-Aware Search**: Respects memory permissions during vector search
- **Configurable Similarity Threshold**: Adjustable minimum similarity for search results

### ✅ API Implementation
- **query_memory Tool**: New MCP tool for semantic search functionality
- **Enhanced Memory Operations**: Automatic embedding generation during memory CRUD operations
- **Scope-Based Access**: Requires appropriate OAuth scopes for embedding operations

## Architecture

### Embedding Generation Flow

1. **Memory Creation/Update**:
   ```
   User submits memory → Text processed → OpenAI API call → Vector stored → Database commit
   ```

2. **Semantic Search**:
   ```
   User query → Generate query embedding → PostgreSQL vector search → Similarity ranking → Results
   ```

### Database Schema

The `memories` table includes:
```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    text TEXT NOT NULL,
    permission VARCHAR(20) DEFAULT 'private',
    embedding VECTOR(1536),  -- pgvector column for embeddings
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    expiration_date TIMESTAMP
);

-- Index for efficient vector similarity search
CREATE INDEX ON memories USING ivfflat (embedding vector_cosine_ops);
```

## API Usage

### Query Memory Tool

**Endpoint**: `/api/tools`
**Method**: POST
**Tool**: `query_memory`

**Request Parameters**:
- `query` (required): Search query text
- `limit` (optional): Maximum number of results (default: 10)
- `similarity_threshold` (optional): Minimum similarity score (default: 0.5)
- `permission_filter` (optional): Filter by permission level

**Example Request**:
```json
{
  "tool": "query_memory",
  "data": {
    "query": "artificial intelligence thoughts",
    "limit": 5,
    "similarity_threshold": 0.7,
    "permission_filter": "private"
  }
}
```

**Example Response**:
```json
{
  "data": {
    "memories": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "text": "I think AI will revolutionize how we work and interact with technology...",
        "permission": "private",
        "similarity": 0.85,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "expiration_date": null
      },
      {
        "id": "440e8400-e29b-41d4-a716-446655440001",
        "text": "Machine learning algorithms are becoming more sophisticated...",
        "permission": "private", 
        "similarity": 0.72,
        "created_at": "2024-01-14T15:20:00Z",
        "updated_at": "2024-01-14T15:20:00Z",
        "expiration_date": null
      }
    ]
  }
}
```

### Enhanced Memory Operations

All memory creation and update operations now automatically generate embeddings:

**Submit Memory** - Automatically generates embedding:
```json
{
  "tool": "submit_memory",
  "data": {
    "text": "This is my new memory about AI",
    "permission": "private"
  }
}
```

**Update Memory** - Regenerates embedding if text changes:
```json
{
  "tool": "update_memory", 
  "data": {
    "memory_id": "550e8400-e29b-41d4-a716-446655440000",
    "text": "Updated memory content about AI applications"
  }
}
```

## Configuration

### Environment Variables

Add to your `.env` file:
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Override embedding model (default: text-embedding-3-small)
EMBEDDING_MODEL=text-embedding-3-small
```

### Dependencies

The following packages have been added/updated:
- `openai>=1.0.0` (upgraded from 0.28.0)
- `numpy>=1.24.0` (for vector calculations)
- `pgvector==0.2.1` (already present)

## Error Handling

The implementation includes comprehensive error handling:

### OpenAI API Errors
- **Rate Limiting**: Automatic retry with exponential backoff
- **Authentication Errors**: Clear error messages for invalid API keys
- **Service Unavailable**: Graceful degradation when OpenAI API is down
- **Invalid Input**: Validation for empty or invalid text inputs

### Database Errors
- **Vector Dimension Mismatch**: Validation of embedding dimensions
- **Index Errors**: Graceful handling of vector index issues
- **Connection Failures**: Proper error propagation for database issues

### Example Error Response
```json
{
  "error": "Failed to generate embedding",
  "detail": "OpenAI API rate limit exceeded. Please try again in 60 seconds.",
  "error_code": "EMBEDDING_RATE_LIMIT"
}
```

## Performance Considerations

### Embedding Generation
- **Asynchronous Processing**: Embeddings generated in thread pool to avoid blocking
- **Batch Processing**: Future enhancement for bulk embedding generation
- **Caching**: Consider implementing embedding cache for repeated queries

### Vector Search
- **Index Optimization**: pgvector uses IVFFlat index for fast approximate search
- **Query Optimization**: Similarity threshold helps limit result set size
- **Memory Usage**: Vector storage adds ~6KB per memory (1536 floats × 4 bytes)

### Scaling Recommendations
- **Connection Pooling**: Use connection pooling for high-traffic deployments
- **Embedding Cache**: Implement Redis cache for frequently accessed embeddings
- **Batch Updates**: Process multiple embeddings in single OpenAI API call

## Testing

### Unit Tests
The implementation includes comprehensive unit tests for:
- Embedding generation functions
- Vector similarity calculations
- Database vector operations
- Error handling scenarios

### Integration Tests
End-to-end tests verify:
- Complete memory-to-embedding workflow
- Semantic search functionality
- Permission enforcement in vector search
- Error handling across the stack

### Manual Testing Commands

Generate test embedding:
```python
from app.utils.embeddings import get_embedding_async
import asyncio

# Test embedding generation
embedding = asyncio.run(get_embedding_async("test memory content"))
print(f"Generated embedding with {len(embedding)} dimensions")
```

Test semantic search:
```python
from app.utils.embeddings import search_memories_by_embedding
import asyncio

# Test semantic search (requires database session)
results = asyncio.run(search_memories_by_embedding(
    db=db_session,
    user_id="user-uuid-here",
    query_embedding=test_embedding,
    limit=5
))
print(f"Found {len(results)} similar memories")
```

## Future Enhancements

### Planned Features
- **Batch Embedding Processing**: Process multiple memories in single API call
- **Embedding Model Options**: Support for different OpenAI embedding models
- **Hybrid Search**: Combine vector search with traditional text search
- **Clustering**: Group similar memories using vector clustering algorithms

### Performance Optimizations
- **Embedding Cache**: Redis cache for frequently accessed embeddings
- **Incremental Updates**: Only regenerate embeddings when text significantly changes
- **Background Processing**: Queue-based background embedding generation
- **Vector Compression**: Explore dimension reduction techniques for storage efficiency

### Advanced Features
- **Cross-User Search**: Search across public memories from multiple users
- **Temporal Embeddings**: Weight embeddings by recency and relevance
- **Personalized Search**: Adapt search results based on user preferences
- **Multi-Modal Embeddings**: Support for image and audio content embeddings

## Troubleshooting

### Common Issues

1. **OpenAI API Key Invalid**:
   - Verify API key is correctly set in environment variables
   - Check API key has sufficient credits and permissions

2. **Vector Index Missing**:
   - Ensure pgvector extension is installed: `CREATE EXTENSION vector;`
   - Run database migrations: `alembic upgrade head`

3. **Embedding Dimension Mismatch**:
   - Verify using text-embedding-3-small model (1536 dimensions)
   - Check database column definition matches model output

4. **Performance Issues**:
   - Monitor OpenAI API rate limits
   - Check vector index statistics: `SELECT * FROM pg_stat_user_indexes WHERE relname = 'memories';`
   - Consider adjusting similarity threshold for faster queries

### Debug Commands

Check pgvector installation:
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

Verify embedding storage:
```sql
SELECT id, array_length(embedding, 1) as dim_count 
FROM memories 
WHERE embedding IS NOT NULL 
LIMIT 5;
```

Test vector similarity:
```sql
SELECT id, text, 1 - (embedding <=> '[0.1, 0.2, ...]'::vector) as similarity
FROM memories 
WHERE user_id = 'your-user-id'
ORDER BY similarity DESC
LIMIT 5;
```

## Security Considerations

### Data Protection
- **API Key Security**: OpenAI API keys stored securely in environment variables
- **Vector Data**: Embeddings don't expose original text but enable similarity search
- **Permission Enforcement**: Vector search respects memory permission levels
- **Rate Limiting**: Implement rate limiting for embedding generation endpoints

### Privacy Implications
- **Embedding Privacy**: Vector embeddings may leak some semantic information
- **Cross-User Search**: Ensure public memory search doesn't expose private data
- **Audit Logging**: Log embedding generation and search operations for compliance

This implementation provides a solid foundation for semantic search while maintaining security and performance standards.

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a function for similarity search
CREATE OR REPLACE FUNCTION match_memories(
    query_embedding vector(384),
    match_threshold float,
    match_count int,
    user_id_param bigint
) RETURNS TABLE (
    id bigint,
    content text,
    similarity float
) LANGUAGE sql STABLE AS $$
    SELECT
        m.id,
        m.content,
        1 - (m.embedding <=> query_embedding) AS similarity
    FROM memories_contextblock m
    WHERE 1 - (m.embedding <=> query_embedding) > match_threshold
    AND (
        m.is_public = true
        OR m.user_id = user_id_param
        OR EXISTS (
            SELECT 1 FROM permissions_contextpermission cp
            WHERE cp.memory_id = m.id
            AND cp.user_id = user_id_param
        )
    )
    ORDER BY similarity DESC
    LIMIT match_count;
$$;

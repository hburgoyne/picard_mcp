# Picard MCP Server

A Model Context Protocol (MCP) server that provides memory storage and retrieval for authenticated users, with the ability to query an LLM using personas based on public memories.

## Features

- OAuth 2.0 Authentication (Authorization Code flow)
- Memory storage and retrieval for authenticated users
- Permission management for memories (public/private)
- LLM querying using personas based on public memories
- pgvector with PostgreSQL for vector storage
- Docker Compose for local development
- Render deployment configuration

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10+

### Local Development

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in the required values
3. Run `docker-compose up`
4. Access the MCP server at http://localhost:8000

## Deployment

This project includes a `render.yaml` blueprint for deploying to Render.

## License

MIT

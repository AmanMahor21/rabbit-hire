# Rabbit Hire replacement pack

Generated from the supplied project snapshot. This is a conservative production-hardening replacement, not a speculative rewrite.

## Applied fixes
- structured logging bootstrap
- no settings/API-key debug print
- configurable embedding model and dynamic vector dimension
- skill taxonomy uses the same embedding dimension
- safer CORS origin configuration
- SHA-256 point IDs instead of MD5 filename IDs (still filename-stable for compatibility)
- resume tool payload field corrected from experience_years to experience
- mutable Pydantic list defaults changed to default_factory
- obvious candidate/debug dumps removed

## Before deploying
1. Back up PostgreSQL and Qdrant.
2. Set CORS_ORIGINS explicitly.
3. If EMBEDDING_MODEL changes dimension, create/reindex into a new Qdrant collection instead of mutating the live collection.
4. Run Python compile checks and frontend `npm run build`.
5. Run the committed evaluation suite and compare to the existing baseline.

This pack intentionally does not invent authentication/tenant semantics because the supplied snapshot has a login UI but no complete backend auth contract. Security boundaries must be designed with your actual identity provider and organization model.

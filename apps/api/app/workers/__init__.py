"""
Background job processing for Bear Tracks Course Insight Platform.

This module provides Celery-based task processing for:
- Course data scraping from Bear Tracks
- Reddit sentiment analysis
- AI-powered content analysis with Claude
- Vector embeddings generation with OpenAI
- Database persistence with retry logic
"""

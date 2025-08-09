-- Enables gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS health_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    data_source TEXT NOT NULL,
    headline TEXT,
    summary TEXT,
    image_url TEXT,
    link TEXT UNIQUE NOT NULL,
    media_type TEXT,
    media_outlet TEXT,
    media_name TEXT,
    status TEXT DEFAULT 'unverified',
    keywords TEXT[],
    engagement INT
);

CREATE TABLE IF NOT EXISTS keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword TEXT UNIQUE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Extend existing public.mentions (if you already use that table in Supabase)
-- Safe to run multiple times
ALTER TABLE IF EXISTS mentions
ADD COLUMN IF NOT EXISTS location JSONB;




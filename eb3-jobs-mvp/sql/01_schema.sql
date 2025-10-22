
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS employers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL UNIQUE,
  website TEXT,
  contact_email TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eb3_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  employer_id UUID REFERENCES employers(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  country TEXT NOT NULL DEFAULT 'US',
  wage_hourly NUMERIC(6,2),
  status TEXT NOT NULL CHECK (status IN ('FILING_NOW','SOLD_OUT','PAUSED')),
  duties TEXT,
  apply_url TEXT,
  video_url TEXT,
  visa_types TEXT[] DEFAULT ARRAY['EB-3'],
  language_tags TEXT[] DEFAULT ARRAY['en','pt'],
  source_tag TEXT,
  posted_date DATE,
  scraped_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_eb3_jobs_state ON eb3_jobs(state);
CREATE INDEX IF NOT EXISTS idx_eb3_jobs_status ON eb3_jobs(status);
CREATE INDEX IF NOT EXISTS idx_eb3_jobs_posted ON eb3_jobs(posted_date);


INSERT INTO employers (name, website, contact_email) VALUES
 ('ACME Roofing LLC','https://acmeroofing.example','hr@acmeroofing.example')
ON CONFLICT (name) DO NOTHING;

INSERT INTO employers (name, website, contact_email) VALUES
 ('Sunrise Hospitality','https://sunrise.example','talent@sunrise.example')
ON CONFLICT (name) DO NOTHING;

INSERT INTO eb3_jobs (employer_id, title, city, state, wage_hourly, status, duties, apply_url, video_url, posted_date, source_tag)
SELECT id, 'Roofing Helper', 'Phoenix', 'AZ', 22.00, 'FILING_NOW', 'Assist roofers with materials, cleanup, basic tasks.',
       'https://seuportal.example/apply/roofing-helper-az', NULL, CURRENT_DATE - INTERVAL '2 days', 'internal:pilot'
FROM employers WHERE name='ACME Roofing LLC';

INSERT INTO eb3_jobs (employer_id, title, city, state, wage_hourly, status, duties, apply_url, posted_date, source_tag)
SELECT id, 'Housekeeping Attendant', 'Myrtle Beach', 'SC', 15.50, 'SOLD_OUT', 'Room cleaning, linens, common areas upkeep.',
       'https://seuportal.example/apply/housekeeping-sc', CURRENT_DATE - INTERVAL '5 days', 'internal:pilot'
FROM employers WHERE name='Sunrise Hospitality';

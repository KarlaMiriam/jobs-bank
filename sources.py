# sources.py

"""
Todas as fontes que o coletor Python usa. Cada item precisa ter um `type`
que corresponde a um scraper disponível em `scrapers/`.

Campos extras aceitos por tipo:
  greenhouse: slug (obrigatório), company (opcional - override do nome exibido)
  lever: company (obrigatório), include_departments/include_keywords/exclude_keywords (opcional)
  workday: url (obrigatório), company (opcional), pages (opcional - padrão 40)
  mchire/wendys/ihg/hilton-html/walmart/icims: url obrigatório
"""

SOURCES = [
    # -----------------
    # Greenhouse boards focados em operações / cozinha / hotelaria
    # -----------------
    {
        "type": "greenhouse",
        "name": "Sweetgreen (Greenhouse)",
        "slug": "sweetgreen",
        "company": "Sweetgreen",
    },
    {
        "type": "greenhouse",
        "name": "CAVA (Greenhouse)",
        "slug": "cava",
        "company": "CAVA",
    },
    {
        "type": "greenhouse",
        "name": "HelloFresh US (Greenhouse)",
        "slug": "hellofresh",
        "company": "HelloFresh",
    },
    {
        "type": "greenhouse",
        "name": "DIG (Greenhouse)",
        "slug": "dig",
        "company": "DIG",
    },

    # -----------------
    # Lever – focado em marketplace de shift gigs, logística e operações
    # -----------------
    {
        "type": "lever",
        "name": "Instawork (Lever)",
        "company": "instawork",
        "include_keywords": ["warehouse", "cook", "prep", "server", "bartender", "dish", "banquet"],
    },
    {
        "type": "lever",
        "name": "Qwick (Lever)",
        "company": "qwick",
        "include_keywords": ["server", "cook", "bar", "line cook", "dish"],
    },
    {
        "type": "lever",
        "name": "Upshift (Lever)",
        "company": "upshift",
        "include_keywords": ["warehouse", "hotel", "banquet", "cook", "line cook", "dish"],
    },

    # -----------------
    # Workday – boards com bastante housekeeping / food service
    # -----------------
    {
        "type": "workday",
        "name": "Marriott Careers (Workday)",
        "company": "Marriott",
        "url": "https://marriott.wd5.myworkdayjobs.com/MarriottCareers",
        "pages": 8,
    },
    {
        "type": "workday",
        "name": "Compass Group USA (Workday)",
        "company": "Compass Group",
        "url": "https://compassgroupus.wd3.myworkdayjobs.com/CGExternal",
        "pages": 6,
    },
    {
        "type": "workday",
        "name": "Aramark (Workday)",
        "company": "Aramark",
        "url": "https://aramark.wd1.myworkdayjobs.com/aramarkcareers",
        "pages": 6,
    },

    # -----------------
    # McHire – McDonald's (lista inteira paginada)
    # -----------------
    {
        "type": "mchire",
        "name": "McDonald's",
        "url": "https://jobs.mchire.com/jobs",
    },

    # -----------------
    # IHG – links específicos que você passou
    # -----------------
    {
        "type": "ihg",
        "name": "IHG - Room Attendant",
        "url": "https://careers.ihg.com/en/job-details/?jobref=Room+Attendant+-+Housekeeping%7cUS%7c152669#9891",
    },
    {
        "type": "ihg",
        "name": "IHG - Lobby Attendant",
        "url": "https://careers.ihg.com/en/job-details/?jobref=Lobby+Attendant+-+Regent+Santa+Monica+Beach%7cUK%7c151096#12556",
    },
    {
        "type": "ihg",
        "name": "IHG - Housekeeping Supervisor",
        "url": "https://careers.ihg.com/en/job-details/?jobref=Franchise+Hotel+-+Housekeeping+Supervisor%7cen%7cFRAUSSV4291#11935",
    },

    # -----------------
    # Wendy's – crawler automático paginando listagem
    # -----------------
    {
        "type": "wendys",
        "name": "Wendy's - job search (auto)",
        "url": "https://wendys-careers.com/job-search/?pages=5",
    },

    # -----------------
    # Walmart – link fixo enviado
    # -----------------
    {
        "type": "walmart",
        "name": "Walmart - R-2339203",
        "url": "https://careers.walmart.com/us/en/jobs/R-2339203",
    },

    # -----------------
    # Hilton – scraping HTML direto
    # -----------------
    {
        "type": "hilton-html",
        "name": "Hilton - Housekeeping Franchise",
        "url": "https://jobs.hilton.com/us/en/job/P-103169/Housekeeping-Franchise",
    },

    # -----------------
    # iCIMS – Grimmway
    # -----------------
    {
        "type": "icims",
        "name": "Grimmway - Maintenance Mechanic",
        "url": "https://careers-grimmway.icims.com/jobs/20801/maintenance-mechanic/job",
    },
]

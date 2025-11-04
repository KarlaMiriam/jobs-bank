SOURCES = [
    # Greenhouse
    {"type": "greenhouse", "name": "Sweetgreen (Greenhouse)", "slug": "sweetgreen", "company": "Sweetgreen"},
    {"type": "greenhouse", "name": "HelloFresh US (Greenhouse)", "slug": "hellofresh", "company": "HelloFresh"},

    # McDonald's – agora por HTML
   {"type": "mchire", "name": "McDonald's (McHire)",
     "url": "https://jobs.mchire.com/jobs?location_name=United%20States&location_type=4"},

    # Workday (podem falhar, mas não travam o robô)
    {"type": "workday", "name": "Marriott (Workday)", "company": "Marriott", "url": "https://marriott.wd5.myworkdayjobs.com/MarriottCareers"},
    {"type": "workday", "name": "Compass Group (Workday)", "company": "Compass Group", "url": "https://compassgroupus.wd3.myworkdayjobs.com/CGExternal"},
    {"type": "workday", "name": "Aramark (Workday)", "company": "Aramark", "url": "https://aramark.wd1.myworkdayjobs.com/aramarkcareers"},
    {"type": "workday", "name": "Sodexo (Workday)", "company": "Sodexo", "url": "https://sodexo.wd3.myworkdayjobs.com/SodexoCareers"},
    {"type": "workday", "name": "Hyatt (Workday)", "company": "Hyatt", "url": "https://hyatt.wd5.myworkdayjobs.com/HyattCareers"},

    # IHG (podem dar 403, mas a gente trata)
    {"type": "ihg", "name": "IHG - Room Attendant (US)", "url": "https://careers.ihg.com/en/job-details/?jobref=Room+Attendant+-+Housekeeping%7cUS%7c152669#9891"},
    {"type": "ihg", "name": "IHG - Lobby Attendant (Regent)", "url": "https://careers.ihg.com/en/job-details/?jobref=Lobby+Attendant+-+Regent+Santa+Monica+Beach%7cUK%7c151096#12556"},
    {"type": "ihg", "name": "IHG - Housekeeping Supervisor", "url": "https://careers.ihg.com/en/job-details/?jobref=Franchise+Hotel+-+Housekeeping+Supervisor%7cen%7cFRAUSSV4291#11935"},

    # Hilton
    {"type": "hilton-html", "name": "Hilton - Housekeeping Franchise", "url": "https://jobs.hilton.com/us/en/job/P-103169/Housekeeping-Franchise"},

    # Walmart
    {"type": "walmart", "name": "Walmart - R-2339203", "url": "https://careers.walmart.com/us/en/jobs/R-2339203"},

    # iCIMS
    {"type": "icims", "name": "Grimmway - Maintenance Mechanic", "url": "https://careers-grimmway.icims.com/jobs/20801/maintenance-mechanic/job"},

     # Adzuna (EUA)
    # Termos focados em EB-3/subempregos
{"type": "adzuna-bulk", "name": "Adzuna bulk A", "queries": [
  "housekeeper","room attendant","janitor","cleaner","housekeeping",
  "dishwasher","line cook","prep cook","fast food","restaurant crew"
], "pages": 5},

{"type": "adzuna-bulk", "name": "Adzuna bulk B", "queries": [
  "warehouse associate","picker packer","general labor","loader","unloader",
  "maintenance","groundskeeper","laundry attendant"
], "pages": 5},

{"type": "adzuna-bulk", "name": "Adzuna bulk C", "queries": [
  "hotel","front desk","busser","server","barback","cook","food prep"
], "pages": 5},

{"type": "adzuna-bulk", "name": "Adzuna bulk D", "queries": [
  "caregiver","nursing aide","food service worker","cafeteria","buffet attendant"
], "pages": 5},



]

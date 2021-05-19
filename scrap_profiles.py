import sys
import time
import xlsxwriter
from configparser import ConfigParser

from profile_scraper import ProfileScraper
from utils import boolean_to_string_xls, date_to_string_xls, message_to_user, chunks

# Loading of configurations
config = ConfigParser()
config.read('config.ini')

headless_option = len(sys.argv) >= 2 and sys.argv[1] == 'HEADLESS'

entries = []
for entry in open(config.get('profiles_data', 'input_file_name'), "r"):
    entries.append(entry.strip())

if len(entries) == 0:
    print("Please provide an input.")
    sys.exit(0)

if headless_option:
    grouped_entries = chunks(entries, len(entries) // int(config.get('system', 'max_threads')))
else:
    grouped_entries = [entries]

if len(grouped_entries) > 1:
    print(f"Starting {len(grouped_entries)} parallel scrapers.")
else:
    print("Starting scraping...")

scrapers = []
for entries_group in grouped_entries:
    scrapers.append(ProfileScraper(len(scrapers)+1, entries_group, config, headless_option))

for scraper in scrapers:
    scraper.start()

for scraper in scrapers:
    scraper.join()

scraping_results = []
for scraper in scrapers:
    scraping_results.extend(scraper.results)

# Generation of XLS file with profiles data
output_file_name = config.get('profiles_data', 'output_file_name')
if config.get('profiles_data', 'append_timestamp') == 'Y':
    output_file_name_splitted = output_file_name.split('.')
    output_file_name = "".join(output_file_name_splitted[0:-1]) + "_" + str(int(time.time())) + "." + \
                       output_file_name_splitted[-1]

workbook = xlsxwriter.Workbook(output_file_name)
worksheet = workbook.add_worksheet()

# headers = ['Name', 'Headline', 'Location', 'Connection', 'Desc', 'Email', 'Skills', 'Company', 'Industry', 'Job Title', 'City', 'Country',
#            'DATE FIRST JOB EVER', 'DATE FIRST JOB AFTER BEGINNING POLIMI', 'DATE FIRST JOB AFTER ENDING POLIMI',
#            'JOB WITHIN 3 MONTHS', 'JOB WITHIN 5 MONTHS', 'JOB WITHIN 6 MONTHS', 'JOB WHILE STUDYING',
#            'MORE THAN ONE JOB POSITION', 'NOT CURRENTLY EMPLOYED', 'NEVER HAD JOBS']

headers = ['Name', 'Headline', 'Location', 'Connection', 'Desc', 'Email', 'Phone', 'Birthday', 'ConnectedDate', 'Skills']
x = 1
for x in range(4):
    headers.extend(['CompanyName{}'.format(x), 'JobPosition{}'.format(x), 'JobCity{}'.format(x), 'JobCountry{}'.format(x)])
    x += 1
x = 1
for x in range(3):
    headers.extend(['EducationName{}'.format(x), 'DegreeName{}'.format(x), 'Major{}'.format(x), 'Year{}'.format(x)])
    x += 1

# Set the headers of xls file

for i in range(len(scraping_results)):

    scraping_result = scraping_results[i]

    if scraping_result.is_error():
        data = ['Error_' + scraping_result.message] * len(headers)
    else:
        p = scraping_result.profile
        data = [
            p.profile_name,
            p.headline,
            p.location,
            p.connection,
            " ".join(p.profile_desc),
            p.email,
            p.phone,
            p.birthday,
            p.connectedDate,
            ",".join(p.skills)
        ]

        x = 0
        for current_job in p.current_job:
            if x < 4:
                data.append(current_job.company.name)
                data.append(current_job.position)
                if current_job.location == None:
                    data.append(None)
                    data.append(None)
                else:
                    data.append(current_job.location.city)
                    data.append(current_job.location.country)
                x += 1

        x = 0
        for education in p.education:
            if x < 3:
                data.append(education.education_name)
                data.append(education.degree_name)
                data.append(education.major)
                data.append(education.year)
                x += 1
    
    for h in range(len(headers)):
        worksheet.write(0, h, headers[h])

    for j in range(len(data)):
        worksheet.write(i + 1, j, data[j])

workbook.close()

if any(scraper.interrupted for scraper in scrapers):
    message_to_user("The scraping didnt end correctly due to Human Check. The excel file was generated but it will "
                    "contain some entries reporting an error string.", config)
else:
    message_to_user('Scraping successfully ended.', config)

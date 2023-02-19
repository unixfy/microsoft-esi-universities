import requests
import random
import time
# CONFIG

# The Microsoft ESI customer info endpoint, should accept a POST request to check if a domain is an ESI customer
MICROSOFT_ESI_CUSTOMERINFO_ENDPOINT = 'https://api.prod.esi.microsoft.com/api/profile/customerinfo'

# The EDU domain list API endpoint, should take a GET request and return results in
# schema defined here: https://github.com/Hipo/university-domains-list
EDU_DOMAIN_LIST_ENDPOINT = 'http://universities.hipolabs.com/search?country=united%20states'

# Email address prefix (e.g., if set to example, then we will test example@example.com) to test against Microsoft ESI endpoint
EMAIL_PREFIX = '2411427809'

def get_edu_domains_list():
    """
    Grabs and parses a Hipo Labs universities list, returns a list of edu domains
    """
    try:
        # Hit the edu domain list endpoint with a GET request
        raw_universities_list = requests.get(EDU_DOMAIN_LIST_ENDPOINT)
        raw_universities_list_json = raw_universities_list.json()

        if raw_universities_list.ok == True:
            # We will do some processing to just get a list of edu domains for easier processing

            # Store all our EDU domains
            edu_domains_list = []

            # iterate over every university in the EDU endpoint response
            for university in raw_universities_list_json:
                # We need to iterate over the "domains" entry in the dict for each university, which is presented as a list
                for domain in university["domains"]:
                 edu_domains_list.append(domain)

            # Strip duplicates when we return
            return list(set(edu_domains_list))
            
    except requests.exceptions.RequestException as e:
        raise e

def check_esi_eligibility_domains():
    """
    Takes a list of domains and checks them for ESI eligibility. Returns a list of eligible domains.
    """
    domain_list = get_edu_domains_list()

    # Store eligible domains
    eligible_domains_result = []

    # In the future, I should probably make this async to really improve the performance :-)
    for i, domain in enumerate(domain_list):
        # Add a debug message for convenience purpose
        print(f"Now checking {domain}, {i} / {len(domain_list)}")

        # Hit the customer info endpoint
        esi_eligiblity_check = requests.post(MICROSOFT_ESI_CUSTOMERINFO_ENDPOINT, json={
            "emailAddress": f"{EMAIL_PREFIX}@{domain}"
        })
        esi_eligiblity_check_json = esi_eligiblity_check.json()

        # We will get a 404 response if not eligible; in that case, we will just skip this iteration of the loop
        if esi_eligiblity_check.status_code == 404:
            continue

        # Otherwise we should get a status code of 200
        if esi_eligiblity_check.status_code == 200 and esi_eligiblity_check.ok == True:
            # Add the domain to our results
            eligible_domains_result.append({
                "domain": domain,
                "AADEnabled": esi_eligiblity_check_json["isAad"],
                "companyName": esi_eligiblity_check_json["companyName"],
                "esi": esi_eligiblity_check_json["esi"]
            })

        # If the request fails, then we will log the error description into our results
        elif esi_eligiblity_check.ok == False:
            eligible_domains_result.append({
                "domain": domain,
                "errorDescription": esi_eligiblity_check_json["description"]
            })

        # Wait a few seconds to prevent slamming the API too much
        time.sleep(random.randint(1, 3))
            
    return eligible_domains_result

print(check_esi_eligibility_domains())


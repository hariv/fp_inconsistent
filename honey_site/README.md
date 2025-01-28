# Honey site

This repository contains source code to deploy the honey site on heroku.

###  Since this honey site makes use of bot detection services, you would have to obtain API keys from different services and replace placeholders in the locations listed below:
- DataDome key: All html files within `static_sites/news_site/`
- FouAnalytics key: All html files within `static_sites/news_site`
- MaxMind key: `util/requests.py`

### Creating multiple versions:
- Create a text file, `versions.txt` at the root directory of this repository where each line contains a random string of size 10. 
- Create a json file, `ga_version_map.json` which contains version names as keys and tags obtained from Google Analytics as values. The number of keys should match the number of versions to ensure that each version has a unique tag.
- Deploying the honey site will automatically result in `<domain_name>/<version_name>/news_site` being deployed with Google Analytics and Bot detection included.

### IP Addresses
- The honey site does not store IP addresses.
- However, it uses GeoLite2 to store ASNs and Timezones from IP addresses.
- Please download `.mmdb` files from MaxMind within `util/` and update the placeholder within `util/requests.py`

### Database tables
Please create the following tables with the described columns:

**requests**
- *client_addr* of type varchar
- endpoint* of type varchar  
- *req_body* of type text
- *req_headers* of type text
- *req_id* of type int4  
- *req_ts* of type timestamp  
- *req_type* of type varchar

**datadome_responses**
- *allow* of type varchar
- *dd_resp_id* of type int4
- *req_id* of type int4
- *resp_headers* of type text

**botd_responses**
- *bot_kind* of type varchar
- *botd_resp_id* of type int4
- *is_bot* of type varchar
- *req_id*  of type int4

**improper_requests**
- *endpoint* of type varchar
- *req_body* of type text
- *req_headers* of type text
- *req_id* of type int4
- *req_ts* of type timestamp
- *req_type* of type varchar
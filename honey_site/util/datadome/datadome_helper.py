import json
import requests
from urllib.parse import quote_plus, urlsplit
from http.cookies import SimpleCookie

class DataDomeHelper:
    # static variables
    datadome_url = "https://api.datadome.co/validate-request/"
    datadome_headers = {
            "ContentType": "application/x-www-form-urlencoded",
            "User-Agent": "ReadMe-API-Explorer",
            "content-type": "application/x-www-form-urlencoded"
    }
    
    datadome_key = quote_plus("datadome_key")
    request_module_name = quote_plus("registered_module_name")
    module_version = quote_plus("1.0")
    server_name = quote_plus("full_url")
    https_prefix = "https://"
    protocol = quote_plus("HTTPS")
    method = quote_plus("POST")
    header_props_file = "./util/datadome/headers.json"
    
    def __init__(self):
        self.server_hostname = None
        self.request = None
        self.load_header_props_map()

    def load_header_props_map(self):
        with open(DataDomeHelper.header_props_file) as f:
            self.header_props_map = json.load(f)

    def extract_original_client_ip_and_port(self, headers):
        self.ip = headers["X-Forwarded-For"] if "X-Forwarded-For" in headers else None
        self.port = headers["X-Forwarded-Port"] if "X-Forwarded-Port" in headers else None

    def extract_post_parameters(self, request_body, version_name_size):
        self.post_param_len = str(len(request_body))
        source_page = request_body["sourcePage"] if "sourcePage" in request_body else None
        
        if source_page:
            split_source_page_url = urlsplit(source_page)
            # this is the base url
            if split_source_page_url.netloc == self.server_name:
                source_page = source_page.replace(self.https_prefix, "")
                self.server_hostname = source_page[:len(self.server_name) + version_name_size + 1]
                # path
                self.request = source_page.replace(self.server_hostname, "")
            else:
                self.server_hostname = split_source_page_url.netloc
                self.request = split_source_page_url.path
                
    def set_request_time(self, timestamp):
        self.request_time = int(timestamp)
        
    def extract_client_id(self, cookie_str):
        cookie = SimpleCookie(cookie_str)
        if "datadome" in cookie:
            return quote_plus(cookie["datadome"].value)
        return None
    
    def parse_headers(self, headers):
        header_keys = headers.keys()
        self.request_headers_list = quote_plus(",".join(header_keys))

        self.request_header_props = headers
        # Cookies
        cookie_str = headers['Cookie'] if 'Cookie' in headers else ""
        self.cookies_len = str(len(cookie_str)) if cookie_str else str(0)
        self.client_id = self.extract_client_id(cookie_str)
        
        self.authorization_len = (
            str(len(headers['Authorization'])) if 'Authorization' in headers else str(0))

    def append_header_prop(self, payload, key, val):
        appended_payload = (
            ("&" + val + "=" + quote_plus(
                self.request_header_props[key])) if key in self.request_header_props else "")
        return appended_payload

    def validate_request(self):
        datadome_response = requests.post(DataDomeHelper.datadome_url, data=self.payload,
                                          headers=DataDomeHelper.datadome_headers)
        return datadome_response
    
    def generate_payload(self):
        self.payload = ("RequestModuleName=" + DataDomeHelper.request_module_name +
                        "&ModuleVersion=" + DataDomeHelper.module_version + "&ServerName=" +
                        DataDomeHelper.server_name + "&Protocol=" + DataDomeHelper.protocol +
                        "&Method=" + DataDomeHelper.method + "&Key=" + DataDomeHelper.datadome_key)

        self.payload += ("&ServerHostname=" + self.server_hostname) if self.server_hostname else ""
        self.payload += ("&Request=" + self.request) if self.request else ""
        self.payload += ("&IP=" + self.ip) if self.ip else ""
        self.payload += ("&Port=" + self.port) if self.port else ""
        
        self.payload += "&HeadersList=" + self.request_headers_list
        
        for key, val in self.header_props_map.items():
            self.payload += self.append_header_prop(self.payload, key, val)

        self.payload += "&CookiesLen=" + self.cookies_len
        self.payload += "&AuthorizationLen=" + self.authorization_len
        self.payload += "&PostParamLen=" + self.post_param_len
        self.payload += ("&ClientID=" + self.client_id) if self.client_id else ""
        self.payload += "&TimeRequest=" + str(self.request_time)
        

import os
import sys
import json
import time
import json
import string
import random
import psycopg2

from urllib.parse import urlparse
from util.requests import Request
from util.botd.botd_helper import BotDHelper
from util.improper_requests import ImproperRequest
from util.datadome.datadome_helper import DataDomeHelper
from util.datadome.datadome_responses import DataDomeResponse
from http.server import BaseHTTPRequestHandler, HTTPServer

import logging

hostname = "localhost"
if 'PORT' not in os.environ:
    os.environ['PORT'] = '34567'
    
port = os.environ['PORT']

class StaticServer(BaseHTTPRequestHandler):
    def __init__(self, *args):
        self.static_sites_path = "static_sites"
        self.news_site_path = "news-site"
        self.ga_placeholder_string = "ga-placeholder"
        self.not_found_file = "404.html"
        self.index_file = "index.html"
        self.versions_file = "versions.txt"
        self.ga_map_file = "ga_version_map.json"
        self.robots_txt_file = "robots.txt"
        self.version_name_size = 10
        self.version_names = self.load_version_names()
        self.load_ga_version_map()
        self.init_mime_type_map()
        BaseHTTPRequestHandler.__init__(self, *args)

    def load_ga_version_map(self):
        with open(self.ga_map_file) as f:
            self.ga_version_map = json.load(f)
            
    def init_mime_type_map(self):
        self.mime_type_map = {}
        self.mime_type_map[".jpg"] = "image/jpeg"
        self.mime_type_map[".jpeg"] = "image/jpeg"
        self.mime_type_map[".png"] = "image/png"
        self.mime_type_map[".html"] = "text/html"
        self.mime_type_map[".css"] = "text/css"
        self.mime_type_map[".js"] = "text/javascript"
        self.mime_type_map[".txt"] = "text/plain"
        
    def load_version_names(self):
        with open(self.versions_file) as f:
            version_names = f.read().splitlines()
        return version_names

    def send_content_headers(self, content_type):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header("Content-Type", content_type)
        self.end_headers()
        
    def read_file(self, file_path, binary=False):
        with open(file_path, 'rb' if binary else 'r') as f:
            content = f.read()
        return content

    def is_valid_request_version(self, request_version):
        return request_version in self.version_names

    def fetch_robots_txt(self):
        return self.read_file(self.robots_txt_file)
    
    def fetch_image_content(self, path, request_version):        
        if self.is_valid_request_version(request_version):
            path = path.replace("/" + request_version, "")

            if path.endswith(".jpg") or path.endswith(".jpeg") or path.endswith(".png"):
                image_file = os.path.join(self.static_sites_path, self.news_site_path, path[1:])
            
                if os.path.exists(image_file):
                    _, image_extension = os.path.splitext(image_file)
                    self.send_content_headers(self.mime_type_map[image_extension])
                    return self.read_file(image_file, binary=True)
    
    def fetch_static_content(self, path, request_version):
        is_valid_request = False
        
        if self.is_valid_request_version(request_version):
            path = path.replace("/" + request_version, "")
            resource_file = os.path.join(self.static_sites_path, self.news_site_path, path[1:])
            _, resource_extension = os.path.splitext(resource_file)
            
            if os.path.exists(resource_file) and os.path.isfile(resource_file):
                is_valid_request = True
                if path.endswith(".html"):
                    self.send_content_headers(self.mime_type_map[resource_extension])
                    
                    html_content = self.read_file(resource_file)
                    html_content = html_content.replace(self.ga_placeholder_string,
                                                        self.ga_version_map[request_version])
                    return html_content, is_valid_request
                
                self.send_content_headers(self.mime_type_map[resource_extension])
                return self.read_file(resource_file), is_valid_request
        
            if os.path.basename(path) == "news_site":
                is_valid_request = True
                html_content = self.read_file(os.path.join(self.static_sites_path,
                                                           self.news_site_path, self.index_file))
                html_content = html_content.replace(self.ga_placeholder_string,
                                                    self.ga_version_map[request_version])
                
                self.send_content_headers(self.mime_type_map[".html"])
                return html_content, is_valid_request

        self.send_content_headers(self.mime_type_map[".html"])
        return self.read_file(os.path.join(self.static_sites_path,
                                           self.not_found_file)), is_valid_request

    def log_improper_request_helper(self, path, req_type, req_headers, req_body):
        improper_request = ImproperRequest()
        req_id = improper_request.log_improper_request(path, req_type, req_headers, req_body);
        improper_request.close_connection()
        return req_id
    
    def log_request_helper(self, path, req_type, req_headers, req_body):
        request = Request()
        req_id = request.log_request(path, req_type, req_headers,
                                     req_body)
        request.close_connection()
        return req_id

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Origin', '*')                
        self.send_header('Access-Control-Allow-Methods', '*')
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def generate_random_string(self):
        random_size = 10
        return ''.join(random.choices(string.ascii_uppercase +
                                      string.digits, k=random_size))
    def do_POST(self):        
        self.send_response(200)
        
        if (self.path == "/fingerprint" or self.path == "/fp" or
            self.path == "/mouse_movement" or self.path == "/mm"):
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
                req_id = self.log_request_helper(str(self.path),
                                                 "POST", str(self.headers), str(post_data))

                if self.path == "/fingerprint" or self.path == "/fp":
                    botd_helper = BotDHelper(req_id)
                    botd_helper.log_botd_decision(str(self.headers), post_data['botResult'])
                    botd_helper.close_connection()
                
                    datadome_helper = DataDomeHelper()
                    datadome_helper.extract_original_client_ip_and_port(self.headers)
                    datadome_helper.extract_post_parameters(post_data, self.version_name_size)
                    datadome_helper.set_request_time(time.time())
                    datadome_helper.parse_headers(self.headers)
                    datadome_helper.generate_payload()
                
                    datadome_response = DataDomeResponse(req_id, datadome_helper.validate_request())
                    datadome_response.log_datadome_response(str(self.headers))
                    
                    datadome_response.close_connection()
                    datadome_response_header_list = datadome_response.get_datadome_headers_list()
                
                    for h in datadome_response_header_list:
                        if datadome_response.is_header_present(h):
                            self.send_header(h, datadome_response.get_header(h))
            except:
                req_id = self.log_improper_request_helper(
                    str(self.path), "POST",str(self.headers),
                    self.rfile.read(content_length).decode('utf-8'))
                print("post data improper for request with data " +
                      self.rfile.read(content_length).decode('utf-8') + " for endpoint " +
                      self.path)
                self.send_header('Access-Control-Allow-Credentials', 'true')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write("Success".encode())
            
        else:
            if 'Content-Length' in self.headers:
                content_length = int(self.headers['Content-Length'])
                req_id = self.log_improper_request_helper(
                    str(self.path), "POST", str(self.headers),
                    self.rfile.read(content_length).decode('utf-8'))
                error_message = "post request to endpoint " + self.path + " with data " +
                self.rfile.read(content_length).decode('utf-8') + " with headers " +
                str(self.headers)
                
            else:
                req_id = self.log_improper_request_helper(str(self.path), "POST",
                                                          str(self.headers), "")
                error_message = ("post request to endpoint " + self.path + " with headers " +
                                 str(self.headers))
                
            print(error_message)
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write("Success".encode())

        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write("Success".encode())

    def do_HEAD(self):
        req_id = self.log_improper_request_helper(str(self.path), "HEAD", str(self.headers), "")
        content = self.fetch_robots_txt()
        self.send_content_headers(self.mime_type_map[".txt"])
        self.wfile.write(bytes(content, encoding='utf8'))
        
    def do_GET(self):
        request_version = self.path[:self.version_name_size + 1]
        
        content = self.fetch_image_content(self.path, request_version[1:])
        
        if content:
            self.wfile.write(content)
        else:
            content, is_valid_request = self.fetch_static_content(self.path, request_version[1:])
            if is_valid_request:
                req_id = self.log_request_helper(str(self.path),
                                                 "GET", str(self.headers), "")
            else:
                req_id = self.log_improper_request_helper(str(self.path),
                                                          "GET", str(self.headers), "")
            self.wfile.write(bytes(content, encoding='utf8'))
        
if __name__ == '__main__':
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    
    logging.basicConfig(level=logging.INFO)
    server = HTTPServer(('', int(port)), StaticServer)
    print("Server running on port " + str(port))

    server.serve_forever()

import os
import psycopg2

class DataDomeResponse:
    
    def __init__(self, req_id, resp_obj):
        self.db_url = os.environ['DATABASE_URL']
        self.conn = psycopg2.connect(self.db_url, sslmode='require')
        self.allow = self.check_allow(resp_obj)
        self.datadome_resp_headers = resp_obj.headers
        self.req_id = req_id
        
    def get_datadome_headers_list(self):
        if 'X-DataDome-headers' in self.datadome_resp_headers:
            return self.datadome_resp_headers['X-DataDome-headers'].split(' ')
        return []
    
    def is_header_present(self, header_name):
        return header_name in self.datadome_resp_headers

    def get_header(self, header_name):
        return self.datadome_resp_headers[header_name]
    
    def check_allow(self, resp_obj):
        return (resp_obj.status_code == 200 or ('X-DataDomeResponse' in resp_obj.headers and
                                                resp_obj.status_code !=
                                                resp_obj.headers['X-DataDomeResponse']))

    def log_datadome_response(self, req_headers):
        log_datadome_response_query = """INSERT INTO public.datadome_responses (req_id,
        resp_headers, allow) VALUES (%s, %s, %s)"""
        cursor = self.conn.cursor()
        cursor.execute(log_datadome_response_query, (self.req_id, str(self.datadome_resp_headers),
                                                     str(self.allow)))
        self.conn.commit()
        cursor.close()

    def close_connection(self):
        if self.conn.closed != 0:
            self.conn.close()

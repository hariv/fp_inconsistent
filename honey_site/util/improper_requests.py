import os
import hashlib
import psycopg2

class ImproperRequest:
    
    def __init__(self):
        self.db_url = os.environ['DATABASE_URL']
        self.conn = psycopg2.connect(self.db_url, sslmode='require')
        self.IP_HEADER = 'X-Forwarded-For'
        self.HEADER_DELIMITER = ': '

    def hash_ip(self, ip_val):
        hash_object = hashlib.sha256(ip_val.encode())
        return hash_object.hexdigest()

    def anonymize_ip(self, req_headers):
        headers_list = req_headers.split('\n')

        for idx, header_key_val in enumerate(headers_list):
            if self.IP_HEADER in header_key_val:
                ip_idx = idx
                ip_val = header_key_val.split(self.HEADER_DELIMITER)[1]
                break
            
        headers_list[ip_idx] = self.IP_HEADER + self.HEADER_DELIMITER + self.hash_ip(ip_val)

        return '\n'.join(headers_list)
        
    def log_improper_request(self, endpoint, req_type, req_headers, req_body):
        log_improper_request_query = """INSERT INTO public.improper_requests (endpoint, req_type,
        req_headers, req_body, req_ts) VALUES (%s, %s, %s, %s,
        CURRENT_TIMESTAMP(5)) RETURNING req_id"""
        cursor = self.conn.cursor()
        cursor.execute(log_improper_request_query, (endpoint, req_type, req_headers, req_body))
        req_id = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        return req_id

    def close_connection(self):
        if self.conn.closed != 0:
            self.conn.close()

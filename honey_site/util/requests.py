import os
import asyncio
import hashlib
import psycopg2
import geoip2
from minfraud import AsyncClient

class Request:    
    def __init__(self):        
        self.db_url = os.environ['DATABASE_URL']
        self.conn = psycopg2.connect(self.db_url, sslmode='require')
        self.IP_HEADER = 'X-Forwarded-For'
        self.HEADER_DELIMITER = ': '
        self.TIMEZONE_HEADER = 'Timezone'
        self.ASN_NAME_HEADER = 'ASN_NAME'
        self.ASN_NUMBER_HEADER = 'ASN_NUMBER'
        self.IP_RISK_HEADER = 'RISK_HEADER'
        self.UNKNOWN_STR = 'unknown'
        
        self.location_db = geoip2.database.reader('GeoLite2_location.mmdb')
        self.asn_db = geoip2.database.reader('GeoLite2_asn.mmdb')
 
        self.maxmind_client = AsyncClient(maxmind_id, 'maxmind_key')
        
        
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

        try:
            location_response = self.location_db.city(ip_val)
            asn_response = self.asn_db.asn(ip_val)
            headers_list.insert(0, self.TIMEZONE_HEADER + self.HEADER_DELIMITER +
                                location_response.location.time_zone)
            headers_list.insert(0, self.ASN_NAME_HEADER + self.HEADER_DELIMITER +
                                asn_response.autonomous_system_organization)
            headers_list.insert(0, self.ASN_NUMBER_HEADER + self.HEADER_DELIMITER +
                                asn_response.autonomous_system_number)

        except AddressNotFoundError:
            headers_list.insert(0, self.TIMEZONE_HEADER + self.HEADER_DELIMITER + self.UNKNOWN_STR)
            headers_list.insert(0, self.ASN_NAME_HEADER + self.HEADER_DELIMITER + self.UNKNOWN_STR)
            headers_list.insert(0, self.ASN_NUMBER_HEADER + self.HEADER_DELIMITER +
                                self.UNKNOWN_STR)
            
        finally:
            self.location_db.close()
            self.asn_db.close()

        maxmind_response = await self.maxmind_client.score({'device': {'ip_address': ip_val}})

        headers_list.insert(0, self.IP_RISK_HEADER + self.HEADER_DELIMITER +
                            str(maxmind_response.ip_address.risk))

        return '\n'.join(headers_list)
            
    def log_request(self, endpoint, req_type, req_headers, req_body):
        req_headers = asyncio.run(anonymize_ip(req_headers))
        
        log_request_query = """INSERT INTO public.requests (endpoint,
        req_type, req_headers, req_body, req_ts) VALUES (%s, %s, %s, %s,
        CURRENT_TIMESTAMP(5)) RETURNING req_id"""
            
        cursor = self.conn.cursor()
        cursor.execute(log_request_query, (endpoint, req_type, req_headers, req_body))
        req_id = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        return req_id

    def close_connection(self):
        if self.conn.closed != 0:
            self.conn.close()

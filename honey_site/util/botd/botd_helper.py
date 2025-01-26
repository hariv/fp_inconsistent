import os
import psycopg2

class BotDHelper:
    
    def __init__(self, req_id):
        self.db_url = os.environ['DATABASE_URL']
        self.conn = psycopg2.connect(self.db_url, sslmode='require')
        self.req_id = req_id
        
    def log_botd_decision(self, req_headers, botd_object):
        bot_kind = "NA"
        if botd_object["bot"] and "botKind" in botd_object:
            bot_kind = botd_object["botKind"]

        log_botd_response_query = """INSERT INTO public.botd_responses (req_id, is_bot,
        bot_kind) VALUES (%s, %s, %s)"""
        cursor = self.conn.cursor()
        cursor.execute(log_botd_response_query, (self.req_id, str(botd_object["bot"]),
                                                 str(bot_kind)))
        self.conn.commit()
        cursor.close()

    def close_connection(self):
        if self.conn.closed != 0:
            self.conn.close()

#unitest functions 
import unittest
import json
import os
class ConnectDBTest(unittest.TestCase):
    def test_data_base_db(self):
        config_json = json.load(open(os.path.realpath('./config.json')))
        if (config_json['database_uri']):
            self.assertTrue(True)
        pass

import dotenv
import os
import json


class ENVIRONMENT:
    def __init__(self):
        project_dir = os.path.join(os.path.dirname(__file__), os.pardir)
        dotenv_path = os.path.join(project_dir, '.env')
        dotenv.load_dotenv(dotenv_path)
        self.domain = os.getenv("DOMAIN") or '0.0.0.0'
        # self.port = os.getenv("PORT") or 443
        self.port = 443
        self.prefix = os.getenv("PREFIX") or '/api'

    def get_instance(self):
        if not hasattr(self, "_instance"):
            self._instance = ENVIRONMENT()
        return self._instance

    def getDomain(self):
        return self.domain

    def getPort(self):
        return self.port

    def getPrefix(self):
        return self.prefix


domain = ENVIRONMENT().get_instance().getDomain()
port = ENVIRONMENT().get_instance().getPort()
prefix = ENVIRONMENT().get_instance().getPrefix()


def build_swagger_config_json():
    config_file_path = 'app/static/swagger/config.json'

    with open(config_file_path, 'r') as file:
        config_data = json.load(file)

    config_data['servers'] = [
        {"url": f"http://localhost:{port}{prefix}"},
        # {"url": f"https://{domain}:{port}{prefix}"}
        {"url": f"https://agrieco-connect-backend.vercel.app{prefix}"}
    ]

    new_config_file_path = 'app/static/swagger/config.json'

    with open(new_config_file_path, 'w') as new_file:
        json.dump(config_data, new_file, indent=2)

import os

class Settings:
    PROJECT_NAME: str = "LyuX Control API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Sécurité & GLPI
    GLPI_API_URL: str = os.getenv("GLPI_API_URL", "http://glpi/apirest.php")
    GLPI_USER_TOKEN: str = os.getenv("GLPI_USER_TOKEN", "mock_glpi_token")
    
    # Domaine LyuX
    LYUX_DOMAIN: str = os.getenv("LYUX_DOMAIN", "lyux.lan")

settings = Settings()

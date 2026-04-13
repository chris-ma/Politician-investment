import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    APH_MEMBERS_URL: str = os.getenv(
        "APH_MEMBERS_URL",
        "https://www.aph.gov.au/Parliamentary_Business/Disclosures/Register_of_Members_Interests",
    )
    APH_SENATORS_URL: str = os.getenv(
        "APH_SENATORS_URL",
        "https://www.aph.gov.au/Parliamentary_Business/Disclosures/Register_of_Senators_Interests",
    )
    APH_BASE_URL: str = os.getenv("APH_BASE_URL", "https://www.aph.gov.au")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    # Secret token for the one-time /api/admin/seed endpoint.
    # Set this in Vercel → Settings → Environment Variables.
    ADMIN_SECRET: str = os.getenv("ADMIN_SECRET", "")


settings = Settings()

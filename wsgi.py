from dotenv import load_dotenv #noqa
load_dotenv()

from app import create_app

app = create_app()

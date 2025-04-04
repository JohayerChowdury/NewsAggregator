import os
from dotenv import load_dotenv
from src.app import create_app, config

# Load environment variables
load_dotenv()

app = create_app()

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)

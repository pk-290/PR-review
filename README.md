# PR Review Assistant

An intelligent Pull Request review system that uses AI to analyze and review code changes. This tool helps streamline the code review process by automatically analyzing pull requests and providing detailed feedback.

## Features

- Ratelimiter for gemini call
- Automated PR analysis using Gemini LLM
- Tools used :Radon library to compute cyclomatic complexity,
             Python's ast module to detect deeply nested control flows, 
             custom logic to check for long functions,
             Pylint for style and naming
- Integration with GitHub for PR management
- Asynchronous task processing with Celery
- RESTful API built with FastAPI
- Docker containerization for easy deployment
- Logging and exceptional handling

## Upcoming Updates

 If time allows would work on integrating this tool into an agentic workflow using LangGraph, enabling agents to reason, plan, and invoke these analysis tools autonomously. This will allow for multi-step, intelligent code review and refactoring suggestions powered by LLMs and custom logic.

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- GitHub account and access token
- Google AI API key (for AI-powered analysis)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/pk290/pr-review.git
cd pr-review
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```env
REDIS_HOST="redis_server"
REDIS_PORT=6379
REDIS_URL="redis://redis:6379/0"
CELERY_BROKER_URL="redis://redis:6379/0"
CELERY_RESULT_BACKEND="redis://redis:6379/0"
GITHUB_TOKEN=your_github_token
GOOGLE_API_KEY=your_google_ai_api_key
```

## Running the Application

### Using Docker (Recommended)

1. Build and start the containers:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

### Running Locally

1. Start Redis (required for Celery):
```bash
docker run -d -p 6379:6379 redis:7
```

2. Start the FastAPI application:
```bash
uvicorn app.main:app --reload
```

3. In a separate terminal, start the Celery worker:
For windows use 
```bash
celery -A app.tasks worker -l info --pool=threads --concurrency=4
````
```bash
celery -A app.tasks worker --loglevel=info
```


## Testing

Run the test suite using pytest:
```bash
pytest
```


## Project Structure

```
pr-review/
├── app/                    # Main application code
├── tests.py/              # Test files
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Python dependencies
├── pytest.ini            # Pytest configuration
└── README.md             # This file
```


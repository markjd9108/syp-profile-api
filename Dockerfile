FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser
RUN playwright install chromium

# Copy application files
COPY generate_html_profile.py .
COPY lead_engine.py .
# Working Style (V3) layer modules
COPY working_style.py .
COPY working_style_content.py .
COPY working_style_html.py .
COPY generate_manager_report.py .
# Dynamic Leadership Insight Report (team layer)
COPY generate_leader_report.py .
COPY team_lead_engine.py .
COPY api_server.py .

# Copy HTML profile templates
COPY templates/ ./templates/

# Static take-home assets (Resource Pack, Leadership Field Guide)
COPY assets/ ./assets/


EXPOSE 8000

CMD ["python3", "api_server.py"]

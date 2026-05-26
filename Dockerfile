FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser
RUN playwright install chromium

# Copy application files
COPY generate_html_profile.py .
COPY generate_manager_report.py .
COPY api_server.py .

# Copy HTML profile templates
COPY templates/ ./templates/

# Copy brand assets
COPY tpl_logo_inverse.png .

EXPOSE 8000

CMD ["python3", "api_server.py"]

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY generate_syp_profiles_improved.py .
COPY api_server.py .

# Copy brand assets (logo)
COPY "SYP Brand Assets/Logos/SYP Logo+Wordmark Black PNG.png" "./SYP Brand Assets/Logos/SYP Logo+Wordmark Black PNG.png"

# Pre-generate white logo at build time
RUN python3 -c "from generate_syp_profiles_improved import ensure_white_logo; ensure_white_logo()"

EXPOSE 8000

CMD ["python3", "api_server.py"]

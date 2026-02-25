# Deployment Guide

This guide covers deploying the AI Tech News Multi-Agent Aggregator Dashboard to a production server.

## Option 1: Deploy on a Linux VPS (Recommended)

This is the most straightforward approach for a personal or small-team deployment.

### 1. Provision a Server

A small VPS with 1-2 GB RAM is sufficient. Recommended providers include DigitalOcean, Linode, or AWS EC2 (t3.micro).

### 2. Install Dependencies on the Server

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git
```

### 3. Clone and Set Up the Project

```bash
git clone <your-repository-url> /opt/ai_news_dashboard
cd /opt/ai_news_dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Add your API key
```

### 4. Create a systemd Service

Create a service file to run the Streamlit app as a background process:

```bash
sudo nano /etc/systemd/system/ai-news-dashboard.service
```

Paste the following content:

```ini
[Unit]
Description=AI News Dashboard
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/ai_news_dashboard
ExecStart=/opt/ai_news_dashboard/venv/bin/streamlit run app/dashboard.py --server.port 8501 --server.headless true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-news-dashboard
sudo systemctl start ai-news-dashboard
```

### 5. Configure a Reverse Proxy (Optional but Recommended)

Use Nginx to serve the app on port 80/443 with SSL.

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

Create an Nginx config at `/etc/nginx/sites-available/ai-news`:

```nginx
server {
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Enable the site and get an SSL certificate:

```bash
sudo ln -s /etc/nginx/sites-available/ai-news /etc/nginx/sites-enabled/
sudo certbot --nginx -d your-domain.com
sudo systemctl restart nginx
```

## Option 2: Deploy with Docker

A `Dockerfile` can be created for containerized deployment.

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:

```bash
docker build -t ai-news-dashboard .
docker run -p 8501:8501 --env-file .env ai-news-dashboard
```

## Option 3: Deploy on Streamlit Community Cloud

For a zero-infrastructure option, you can deploy directly to [Streamlit Community Cloud](https://streamlit.io/cloud).

1. Push your project to a public GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and connect your GitHub account.
3. Select your repository and set `app/dashboard.py` as the main file.
4. Add your `OPENAI_API_KEY` in the "Secrets" section of the Streamlit Cloud settings.

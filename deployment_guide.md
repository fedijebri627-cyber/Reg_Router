# Reg-Router Deployment Guide

This guide covers how to deploy the Reg-Router API to a production Linux server (Ubuntu recommended) using Docker Engine.

## 1. Prerequisites
-   A Linux server (AWS EC2, DigitalOcean Droplet, etc.) with **Ubuntu 22.04 LTS**.
-   **Docker** and **Docker Compose** installed.
-   Access to an SMTP provider (SendGrid, AWS SES) and Stripe Production keys.

## 2. Server Setup

### Install Docker
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
```

## 3. Application Deployment

### Step A: Clone the Repository
```bash
git clone https://github.com/your-repo/reg-router.git
cd reg-router
```

### Step B: Configure Environment
Create a production `.env` file:
```bash
cp .env.example .env
nano .env
```
**Critical Settings to Change:**
*   `POSTGRES_PASSWORD`: Set a strong random password.
*   `STRIPE_SECRET_KEY`: Use your **Live** key (`sk_live_...`).
*   `SMTP_PASSWORD`: Your email provider API key.
*   `SENTRY_DSN`: Your production Sentry URL.
*   `BACKEND_CORS_ORIGINS`: Set to your frontend domain (e.g., `["https://invest.yourdomain.com"]`).

### Step C: Start Services
Use the production compose file which enables **Gunicorn** (high performance) instead of Uvicorn (dev).

```bash
# Build and start in daemon mode
sudo docker-compose -f docker-compose.prod.yml up -d --build
```

### Step D: Run Database Migrations
The application is now running, but the database is empty.

```bash
# Run Alembic migrations inside the container
sudo docker-compose -f docker-compose.prod.yml exec web alembic upgrade head
```

## 4. Setting Up HTTPS (SSL)
The application runs on port `8000` via HTTP. **Do not expose this directly.** Use Nginx as a reverse proxy with Let's Encrypt.

### Install Nginx & Certbot
```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### Configure Nginx
Edit `/etc/nginx/sites-available/reg-router`:
```nginx
server {
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/reg-router /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### Get Free SSL Cert
```bash
sudo certbot --nginx -d api.yourdomain.com
```

## 5. Updates & Maintenance
To deploy a new version:
```bash
git pull                   # Get new code
sudo docker-compose -f docker-compose.prod.yml up -d --build  # Rebuild containers
sudo docker-compose -f docker-compose.prod.yml exec web alembic upgrade head # Run migrations
```

## 6. Monitoring
-   **Logs**: `sudo docker-compose -f docker-compose.prod.yml logs -f`
-   **Error Tracking**: Check your Sentry dashboard.
-   **Database Backups**:
    ```bash
    sudo docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres regrouter > backup.sql
    ```

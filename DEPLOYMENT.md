# Deployment Guide

This guide covers deploying the AI Agent Platform in production.

## Prerequisites

- Docker and Docker Compose installed
- Domain name (for HTTPS)
- SSL certificates
- OpenAI API key

## Quick Start with Docker

1. **Clone the repository**
```bash
git clone <repository-url>
cd ai-agent-platform
```

2. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your:
- `OPENAI_API_KEY`
- `SECRET_KEY` (generate a secure random key)

3. **Build and run with Docker Compose**
```bash
docker-compose up -d
```

The platform will be available at:
- Frontend: http://localhost
- Backend API: http://localhost/api
- API Docs: http://localhost/api/docs

## Production Deployment

### 1. Environment Configuration

Create a production `.env` file:
```env
# OpenAI Configuration
OPENAI_API_KEY=your-production-key

# Security - Generate with: openssl rand -hex 32
SECRET_KEY=your-secure-secret-key

# Database (use PostgreSQL for production)
DATABASE_URL=postgresql://user:pass@db:5432/agentplatform

# Domain
DOMAIN=your-domain.com
```

### 2. SSL/HTTPS Setup

1. Obtain SSL certificates (e.g., from Let's Encrypt)
2. Place certificates in `./ssl/` directory:
   - `cert.pem`
   - `key.pem`

3. Update `nginx.conf` to enable HTTPS (uncomment the HTTPS server block)

### 3. Database Configuration

For production, use PostgreSQL instead of SQLite:

1. Add PostgreSQL to `docker-compose.yml`:
```yaml
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: agentplatform
      POSTGRES_USER: agentuser
      POSTGRES_PASSWORD: securepassword
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

2. Update backend to use PostgreSQL:
```bash
pip install psycopg2-binary
```

### 4. Security Hardening

1. **Update CORS settings** in `api_agents.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

2. **Configure rate limiting** based on your needs in `nginx.conf`

3. **Set secure headers** (already configured in middleware)

4. **Enable firewall rules**:
```bash
# Allow only necessary ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable
```

### 5. Monitoring and Logging

1. **Add logging volume** to `docker-compose.yml`:
```yaml
volumes:
  - ./logs:/app/logs
```

2. **Configure log rotation**:
```bash
# /etc/logrotate.d/agent-platform
/path/to/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

3. **Set up monitoring** (optional):
- Prometheus + Grafana
- Sentry for error tracking
- Uptime monitoring service

### 6. Backup Strategy

1. **Database backups**:
```bash
# Create backup script
#!/bin/bash
docker exec postgres pg_dump -U agentuser agentplatform > backup_$(date +%Y%m%d).sql
```

2. **Schedule automatic backups**:
```bash
# Add to crontab
0 2 * * * /path/to/backup_script.sh
```

### 7. Scaling Considerations

For high traffic:

1. **Use a load balancer** (e.g., HAProxy, AWS ALB)

2. **Scale backend instances**:
```yaml
  backend:
    deploy:
      replicas: 3
```

3. **Add Redis for caching**:
```yaml
  redis:
    image: redis:alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

4. **Use CDN for static assets** (e.g., CloudFlare, AWS CloudFront)

## Cloud Platform Deployment

### AWS Deployment

1. **Use ECS or EKS** for container orchestration
2. **RDS** for PostgreSQL
3. **ElastiCache** for Redis
4. **ALB** for load balancing
5. **CloudFront** for CDN

### Google Cloud Deployment

1. **Cloud Run** or **GKE** for containers
2. **Cloud SQL** for PostgreSQL
3. **Memorystore** for Redis
4. **Cloud Load Balancing**
5. **Cloud CDN**

### Azure Deployment

1. **Container Instances** or **AKS**
2. **Azure Database for PostgreSQL**
3. **Azure Cache for Redis**
4. **Application Gateway**
5. **Azure CDN**

## Maintenance

### Regular Updates

1. **Update dependencies**:
```bash
# Backend
cd backend && pip install --upgrade -r requirements.txt

# Frontend
cd frontend && npm update
```

2. **Update Docker images**:
```bash
docker-compose pull
docker-compose up -d
```

### Health Checks

The platform includes health check endpoints:
- Backend: `/health`
- Monitor these endpoints with your monitoring service

### Troubleshooting

1. **Check logs**:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

2. **Common issues**:
- **API key errors**: Verify OPENAI_API_KEY is set correctly
- **Connection errors**: Check network configuration and firewall rules
- **Performance issues**: Monitor resource usage and scale accordingly

## Security Best Practices

1. **Regular security updates**
2. **Use strong passwords and keys**
3. **Enable 2FA for admin accounts**
4. **Regular security audits**
5. **Keep backups in secure, separate location**
6. **Monitor for suspicious activity**

## Support

For issues and questions:
1. Check the logs first
2. Review the documentation
3. Submit issues on GitHub
4. Contact support (if applicable)
# Deployment Guide - Technician Support Chatbot

## Quick Start (Development)

1. **Clone and setup**:
   ```bash
   cd technician_chatbot
   python setup.py  # Runs automated setup
   ```

2. **Configure environment**:
   ```bash
   # Edit .env file with your settings
   nano .env
   ```

3. **Initialize and run**:
   ```bash
   source venv/bin/activate  # Windows: venv\Scripts\activate
   flask init-db-command
   flask train-models
   python run.py
   ```

## Production Deployment

### Option 1: Docker (Recommended)

1. **Create Dockerfile**:
   ```dockerfile
   FROM python:3.9-slim

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt

   COPY . .
   EXPOSE 5000

   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
   ```

2. **Build and run**:
   ```bash
   docker build -t technician-chatbot .
   docker run -p 5000:5000 --env-file .env technician-chatbot
   ```

### Option 2: Traditional Server

1. **Setup production server** (Ubuntu/CentOS):
   ```bash
   # Install dependencies
   sudo apt update
   sudo apt install python3 python3-pip nginx mongodb

   # Setup application
   git clone <repository>
   cd technician_chatbot
   python3 setup.py
   ```

2. **Configure services**:
   ```bash
   # Create systemd service
   sudo nano /etc/systemd/system/technician-chatbot.service

   # Configure Nginx reverse proxy
   sudo nano /etc/nginx/sites-available/technician-chatbot
   ```

### Option 3: Cloud Platforms

**Heroku**:
```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
heroku create technician-chatbot
heroku config:set PERPLEXITY_API_KEY=your-key
git push heroku main
```

**AWS/GCP/Azure**:
- Use containerized deployment with Docker
- Configure managed MongoDB service
- Set up load balancer and SSL

## Environment Configuration

### Required Variables
```bash
# Core Application
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key
DEBUG=False

# Database
MONGO_URI=mongodb://user:password@host:port/database

# AI Services  
PERPLEXITY_API_KEY=your-perplexity-pro-api-key

# Admin Access
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-admin-password
```

### Optional Variables
```bash
# Performance Tuning
MAX_RESPONSE_LENGTH=500
INTENT_CONFIDENCE_THRESHOLD=0.7

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/technician-chatbot.log
```

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Set secure SECRET_KEY
- [ ] Configure MongoDB authentication
- [ ] Enable rate limiting
- [ ] Set up proper logging
- [ ] Configure firewall rules
- [ ] Use environment variables for secrets
- [ ] Enable backup strategy

## Monitoring & Maintenance

### Health Checks
```bash
# Application health
curl http://localhost:5000/health

# Chat system health  
curl http://localhost:5000/api/chat/health
```

### Log Monitoring
```bash
# Application logs
tail -f /var/log/technician-chatbot.log

# Nginx logs (if used)
tail -f /var/log/nginx/access.log
```

### Performance Monitoring
- Monitor response times via admin dashboard
- Track API usage and costs
- Monitor database performance
- Set up alerts for errors

### Backup Strategy
- Regular MongoDB backups
- Backup trained models and vector indices
- Version control for configuration changes
- Document recovery procedures

## Scaling Considerations

### Horizontal Scaling
- Use multiple application instances behind load balancer
- Implement session storage in Redis/MongoDB
- Use CDN for static assets
- Consider microservices architecture

### Performance Optimization
- Enable caching for frequent queries
- Optimize database queries and indexes
- Use connection pooling
- Implement request queuing for high load

## Troubleshooting

### Common Issues
1. **MongoDB Connection**: Check connection string and credentials
2. **API Errors**: Verify Perplexity API key and quota
3. **Model Loading**: Ensure models directory has correct permissions
4. **CSS Not Loading**: Run Tailwind build command
5. **High Response Times**: Check API usage and database performance

### Debug Mode
```bash
# Enable debug logging
export FLASK_ENV=development
export DEBUG=True

# Run with verbose output
python run.py --debug
```

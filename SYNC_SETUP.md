# STL 311+ Automated Daily Sync Setup Guide

This guide explains how to set up automatic daily synchronization of St. Louis 311 data.

## 🔄 Overview

The STL 311+ system supports multiple methods for automatically updating service requests:

1. **Built-in Scheduler** - Python-based background scheduler
2. **Manual Command-Line Sync** - On-demand sync via scripts
3. **API-triggered Sync** - Sync via REST API endpoints
4. **System Cron/Task Scheduler** - OS-level scheduling

## 📋 Prerequisites

1. **API Key**: Get your St. Louis 311 API key
2. **Environment Setup**: Configure `.env` file
3. **Dependencies**: Install required packages

```bash
# Install schedule library
pip install schedule==1.2.0

# Or if using Docker
docker-compose up -d --build
```

## 🐳 Docker Compose Setup (Recommended)

### 1. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API key
STL311_API_KEY=your_actual_api_key_here
```

### 2. Start Services
```bash
# Start all services
docker-compose up -d

# Initialize database
docker exec stl311_flask python migrate_database.py
```

### 3. Enable Automatic Scheduler
```bash
# Start the built-in scheduler via API
curl -X POST http://localhost:5000/api/scheduler/start

# Or start scheduler automatically by setting in .env:
SCHEDULER_AUTO_START=true
```

### 4. Verify Setup
```bash
# Check scheduler status
curl http://localhost:5000/api/scheduler/status

# Test API connection
docker exec stl311_flask python daily_sync.py test

# Get current sync statistics
docker exec stl311_flask python daily_sync.py stats
```

## 💻 Manual Command-Line Sync

### Available Commands

```bash
# Sync yesterday's data
python daily_sync.py yesterday

# Sync specific date range
python daily_sync.py date-range --start-date 2025-08-10 --end-date 2025-08-12

# Sync last N days
python daily_sync.py last-days --days 7

# Test API connection
python daily_sync.py test

# Get sync statistics
python daily_sync.py stats
```

### Docker Commands

```bash
# Sync yesterday's data (Docker)
docker exec stl311_flask python daily_sync.py yesterday

# Sync date range (Docker)
docker exec stl311_flask python daily_sync.py date-range --start-date 2025-08-10 --end-date 2025-08-12

# Test connection (Docker)
docker exec stl311_flask python daily_sync.py test
```

## 🌐 API Endpoints for Sync

### Scheduler Control
```bash
# Start automatic scheduler
POST /api/scheduler/start

# Stop automatic scheduler  
POST /api/scheduler/stop

# Get scheduler status
GET /api/scheduler/status
```

### Manual Sync Triggers
```bash
# Sync yesterday's data
POST /api/sync/yesterday

# Sync date range
POST /api/sync/date-range
Content-Type: application/json
{
  "start_date": "2025-08-10",
  "end_date": "2025-08-12"
}

# Original sync endpoint (existing)
POST /api/sync
Content-Type: application/json
{
  "days_back": 1,
  "force_sync": false
}
```

## ⏰ System-Level Scheduling

### Windows Task Scheduler

1. **Open Task Scheduler** (Windows + R, type `taskschd.msc`)
2. **Create Basic Task**:
   - Name: "STL 311+ Daily Sync"
   - Trigger: Daily at 2:00 AM
   - Action: Start a program
   - Program: `C:\Users\mills\geo_dev\stl311_plus\daily_sync.bat`

### Linux/Mac Cron Job

```bash
# Edit crontab
crontab -e

# Add daily sync at 2 AM
0 2 * * * /path/to/stl311_plus/daily_sync.sh >> /var/log/stl311_sync.log 2>&1
```

### Docker Cron Alternative

```bash
# Add to docker-compose.yml
services:
  scheduler:
    image: stl311_flask
    container_name: stl311_scheduler
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/stl311_db
    command: python daily_sync.py yesterday
    depends_on:
      - postgres
    networks:
      - stl311_network
    profiles:
      - cron
```

Run with: `docker-compose --profile cron up -d scheduler`

## 🔧 Configuration Options

### Environment Variables (.env)
```bash
# Scheduler timing
DAILY_SYNC_TIME=02:00          # Daily sync time (24hr format)
CLEANUP_TIME=03:00             # Daily cleanup time  
SCHEDULER_AUTO_START=false     # Start scheduler on app startup

# API configuration
STL311_API_KEY=your_key        # Required for API access
```

### Scheduler Settings (services/scheduler.py)
```python
# Customize in DataScheduler class
self.daily_sync_time = "02:00"    # Sync time
self.cleanup_time = "03:00"       # Cleanup time  
self.max_retry_attempts = 3       # Retry attempts
self.retry_delay = 300            # Retry delay (seconds)
```

## 📊 Monitoring and Logs

### Log Files
```bash
# Application logs
logs/stl311.log              # Main application log
logs/daily_sync.log          # Daily sync specific log
stl311_flask.log            # Flask application log
```

### API Monitoring
```bash
# Health check
GET /api/health

# Scheduler status  
GET /api/scheduler/status

# Service request stats
GET /api/stats
```

### Database Monitoring
```sql
-- Check recent sync activity
SELECT source, COUNT(*) as count, MAX(date_requested) as latest
FROM service_requests 
GROUP BY source;

-- Check update history
SELECT * FROM service_request_updates 
WHERE updated_by = 'system'
ORDER BY update_date DESC 
LIMIT 10;
```

## 🚨 Troubleshooting

### Common Issues

1. **API Key Issues**
```bash
# Test API connection
python daily_sync.py test
# Expected: ✅ API connection successful
```

2. **Database Connection Issues**
```bash
# Check database health
curl http://localhost:5000/api/health
# Expected: {"database": "connected"}
```

3. **Scheduler Not Running**
```bash
# Check scheduler status
curl http://localhost:5000/api/scheduler/status

# Start scheduler if stopped
curl -X POST http://localhost:5000/api/scheduler/start
```

4. **Missing Dependencies**
```bash
# Install missing packages
pip install -r requirements.txt

# Or rebuild Docker container
docker-compose up -d --build
```

### Log Analysis
```bash
# View recent sync logs
tail -f logs/daily_sync.log

# Search for errors
grep -i error logs/stl311.log

# Monitor scheduler activity  
grep "scheduler" logs/stl311.log
```

## 📈 Performance Optimization

### For Large Datasets
```python
# Increase API page size (api_client.py)
'page_size': 1000  # Maximum allowed

# Adjust retry settings (scheduler.py)  
self.max_retry_attempts = 5
self.retry_delay = 600  # 10 minutes
```

### For Frequent Updates
```bash
# Run more frequent syncs (every 6 hours)
0 */6 * * * /path/to/daily_sync.sh

# Or adjust scheduler for hourly updates
schedule.every().hour.do(self.hourly_sync_job)
```

## 🔐 Security Considerations

1. **API Key Protection**: Store in `.env`, never commit to git
2. **Database Access**: Use read-only user for sync operations  
3. **Log Rotation**: Configure log rotation to prevent disk fill
4. **Network Security**: Restrict database access to app containers

## 📝 Example Daily Workflow

1. **2:00 AM** - Scheduler fetches yesterday's St. Louis 311 data
2. **2:05 AM** - Data processed and validated  
3. **2:10 AM** - Database updated with new/changed requests
4. **2:15 AM** - GeoServer layers refreshed
5. **3:00 AM** - Cleanup job removes old logs
6. **Hourly** - Health checks ensure API connectivity

This ensures your STL 311+ portal stays current with the latest city data automatically!

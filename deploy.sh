#!/bin/bash
# Deploy script for Space Guardian (Phase 0)

set -e

# Configuration
PROJECT_ID="${1:-your-project-id}"
REGION="${2:-asia-northeast1}"

echo "🚀 Deploying Space Guardian to GCP..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Set project
gcloud config set project $PROJECT_ID

# Build and push containers
echo "📦 Building containers..."

# Data Ingest Job
cd cloud_run/data_ingest_job
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/space-guardian-repo/data-ingest-job:latest
cd ../..

# Detection Job
cd batch_jobs/detection_job
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/space-guardian-repo/detection-job:latest
cd ../..

# LINE Bot
cd cloud_run/line_bot
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/space-guardian-repo/line-bot:latest
cd ../..

# Dashboard
cd cloud_run/simple_dashboard
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/space-guardian-repo/dashboard:latest
cd ../..

# Deploy Cloud Run Jobs
echo "☁️ Deploying Cloud Run Jobs..."

gcloud run jobs create data-ingest-job \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/space-guardian-repo/data-ingest-job:latest \
  --region $REGION \
  --set-env-vars PROJECT_ID=$PROJECT_ID \
  --service-account space-guardian-runner@${PROJECT_ID}.iam.gserviceaccount.com \
  --max-retries 3

gcloud run jobs create detection-job \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/space-guardian-repo/detection-job:latest \
  --region $REGION \
  --set-env-vars PROJECT_ID=$PROJECT_ID \
  --service-account space-guardian-runner@${PROJECT_ID}.iam.gserviceaccount.com \
  --max-retries 3

# Deploy Cloud Run Services
echo "🌐 Deploying Cloud Run Services..."

gcloud run deploy line-bot \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/space-guardian-repo/line-bot:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --service-account space-guardian-runner@${PROJECT_ID}.iam.gserviceaccount.com

gcloud run deploy dashboard \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/space-guardian-repo/dashboard:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --service-account space-guardian-runner@${PROJECT_ID}.iam.gserviceaccount.com

echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Set LINE credentials as environment variables in Cloud Run 'line-bot' service"
echo "2. Get the LINE bot URL and set it in detection-job's LINE_NOTIFY_URL"
echo "3. Test the data-ingest-job manually: gcloud run jobs execute data-ingest-job --region $REGION"

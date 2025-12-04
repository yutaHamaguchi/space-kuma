provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudscheduler.googleapis.com",
    "firestore.googleapis.com",
    "storage.googleapis.com",
    "artifactregistry.googleapis.com",
  ])
  
  service            = each.value
  disable_on_destroy = false
}

# GCS Buckets
resource "google_storage_bucket" "raw_data" {
  name          = "${var.project_id}-raw-data"
  location      = var.region
  force_destroy = true
  
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "results" {
  name          = "${var.project_id}-results"
  location      = var.region
  force_destroy = true
  
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# Upload sample data
resource "google_storage_bucket_object" "sample_image" {
  name   = "samples/sample_sar.tif"
  bucket = google_storage_bucket.raw_data.name
  source = "${path.module}/../samples/sample_sar.tif"
}

# Artifact Registry
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "space-guardian-repo"
  description   = "Docker repository for Space Guardian"
  format        = "DOCKER"
}

# Firestore
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "space-guardian-runner"
  display_name = "Space Guardian Cloud Run Service Account"
}

# Grant permissions
resource "google_project_iam_member" "cloud_run_permissions" {
  for_each = toset([
    "roles/datastore.user",
    "roles/storage.objectAdmin",
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Scheduler Job (triggers data ingest every 10 minutes)
resource "google_cloud_scheduler_job" "data_ingest_trigger" {
  name             = "data-ingest-trigger"
  description      = "Trigger data ingest job every 10 minutes"
  schedule         = "*/10 * * * *"
  time_zone        = "Asia/Tokyo"
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/data-ingest-job:run"
    
    oauth_token {
      service_account_email = google_service_account.cloud_run_sa.email
    }
  }

  depends_on = [google_project_service.required_apis]
}

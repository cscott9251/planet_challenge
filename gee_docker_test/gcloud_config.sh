#!/bin/bash

set -e 

echo "Running gcloud initialisation for Planet..."

echo "Service Account user login..."
gcloud auth application-default login

PROJECT_ID="uhi-postgis-proj3"

gcloud auth application-default set-quota-project ${PROJECT_ID}

echo "Setting active project to one with Planet Service Account enabled..."
gcloud config set project ${PROJECT_ID}

echo "Authenticating Planet Service Account with associated JSON file..."
gcloud auth activate-service-account planet@uhi-postgis-proj3.iam.gserviceaccount.com --key-file="uhi-postgis-proj3-214e01e3433e.json"

echo "Activating weather API..."
gcloud services enable --project ${PROJECT_ID} "weather.googleapis.com"





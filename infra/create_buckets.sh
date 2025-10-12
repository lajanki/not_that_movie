#!/bin/bash

set -e

ENV=${ENV:-dev}

gcloud storage buckets create \
	gs://${ENV}_not_that_movie \
	--project webhost-common \
	--location europe-north1

# Set lifecycle rule
gcloud storage buckets \
	update \
	gs://${ENV}_not_that_movie \
	--lifecycle-file=./lifecycle_rule.json

# Make objects public
gcloud storage buckets \
	add-iam-policy-binding \
	gs://${ENV}_not_that_movie \
	--member=allUsers \
	--role=roles/storage.objectViewer


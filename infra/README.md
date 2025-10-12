This folder contains manually maintained deployment commands for auxilary infrastucture. These include:
 * A **public** Cloud Storage bucket for storing the generated content.
   ```shell
   ./create_buckets.sh
   ```
 * Cloud Monitoring alert policy on the number of objects in the bucket
   ```shell
   gcloud alpha monitoring policies create --policy-from-file="low_object_count_policy.json"
   ```
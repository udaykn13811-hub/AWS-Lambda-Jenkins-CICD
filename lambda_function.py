
import boto3
import csv
import io
import urllib.parse
import os

s3 = boto3.client("s3")

OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]

def lambda_handler(event, context):

    for record in event["Records"]:

        source_bucket = record["s3"]["bucket"]["name"]

        source_key = urllib.parse.unquote_plus(
            record["s3"]["object"]["key"]
        )

        print(f"Processing: {source_key}")

        response = s3.get_object(
            Bucket=source_bucket,
            Key=source_key
        )

        content = response["Body"].read().decode("utf-8")

        reader = csv.DictReader(io.StringIO(content))

        output = io.StringIO()

        fieldnames = ["name", "email"]

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames
        )

        writer.writeheader()

        processed_count = 0

        for row in reader:

            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip().lower()

            if name and email and "@" in email:

                writer.writerow({
                    "name": name,
                    "email": email
                })

                processed_count += 1

        output_key = f"processed/{source_key}"

        s3.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=output_key,
            Body=output.getvalue().encode("utf-8"),
            ContentType="text/csv"
        )

        print(f"Processed records: {processed_count}")
        print(f"Output: {output_key}")

    return {
        "statusCode": 200,
        "body": "CSV processing completed"
    }


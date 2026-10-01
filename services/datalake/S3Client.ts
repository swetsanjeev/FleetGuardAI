import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

export const s3 = new S3Client({ region: process.env.AWS_REGION ?? "us-east-1" });

export async function uploadParquet(bucket: string, key: string, body: Buffer) {
  await s3.send(new PutObjectCommand({ Bucket: bucket, Key: key, Body: body, ContentType: "application/vnd.apache.parquet" }));
}

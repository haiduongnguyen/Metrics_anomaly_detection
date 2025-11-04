import argparse
import boto3
from botocore.exceptions import NoCredentialsError
import os
import glob
import sys

# defaults
# DEFAULT_BUCKET = "vpbank-anomaly-storage-cold-storage"
# DEFAULT_BUCKET = "vpbank-hackathon"
DEFAULT_BUCKET = "vpbank-hackathon-opstimus"
DEFAULT_REGION = "ap-southeast-1"
DEFAULT_S3_FOLDER = "raw/"

def upload_file_to_s3(s3_client, bucket, local_file_path, s3_folder=DEFAULT_S3_FOLDER):
    try:
        if not os.path.isfile(local_file_path):
            print(f"❌ Skipping (not a file): {local_file_path}")
            return False

        file_name = os.path.basename(local_file_path)
        s3_key = f"{s3_folder}{file_name}"
        s3_client.upload_file(local_file_path, bucket, s3_key)
        print(f"✅ Uploaded {file_name} to s3://{bucket}/{s3_key}")
        return True

    except FileNotFoundError:
        print(f"❌ File not found: {local_file_path}")
    except NoCredentialsError:
        print("❌ AWS credentials not available. Please configure them.")
    except Exception as e:
        print(f"⚠️ Upload failed ({local_file_path}): {e}")
    return False

def gather_paths(inputs, recursive=False):
    files = []
    for p in inputs:
        # expand glob patterns
        if any(ch in p for ch in ["*", "?", "["]):
            matches = glob.glob(p, recursive=recursive)
            files.extend(matches)
            continue

        if os.path.isdir(p):
            if recursive:
                for root, _, filenames in os.walk(p):
                    for f in filenames:
                        files.append(os.path.join(root, f))
            else:
                for f in os.listdir(p):
                    fp = os.path.join(p, f)
                    if os.path.isfile(fp):
                        files.append(fp)
            continue

        # plain file path
        files.append(p)
    # deduplicate while preserving order
    seen = set()
    out = []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out

def main(argv):
    parser = argparse.ArgumentParser(description="Upload one or more local files to S3.")
    parser.add_argument("--paths", nargs="+", help="Local file(s), directory(ies), or glob(s) to upload")
    parser.add_argument("--bucket", "-b", default=DEFAULT_BUCKET, help="S3 bucket name")
    parser.add_argument("--region", "-r", default=DEFAULT_REGION, help="AWS region")
    parser.add_argument("--s3-folder", "-f", default=DEFAULT_S3_FOLDER, help="S3 folder/key prefix")
    parser.add_argument("--recursive", action="store_true", help="Recursively upload files in directories")
    args = parser.parse_args(argv)

    s3 = boto3.client("s3", region_name=args.region)

    paths = gather_paths(args.paths, recursive=args.recursive)
    if not paths:
        print("❌ No files found to upload.")
        return 1

    success = 0
    for p in paths:
        if upload_file_to_s3(s3, args.bucket, p, args.s3_folder):
            success += 1

    print(f"\nFinished. Uploaded {success}/{len(paths)} files.")
    return 0 if success == len(paths) else 2

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

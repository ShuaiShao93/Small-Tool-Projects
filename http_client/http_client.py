import requests
import argparse
import json

parser = argparse.ArgumentParser(description="HTTP Client")
parser.add_argument("--url", help="URL to make request to")
parser.add_argument("--method", choices=["POST", "PUT"], help="HTTP method to use")
parser.add_argument("--data", help="Data to send with request, e.g. 'key1:value1,key2:value2'")
parser.add_argument(
    "--headers",
    help='Headers to send with request, e.g. "Content-Type:application/json,X-My-Header:123"',
)


if __name__ == "__main__":
    args = parser.parse_args()

    headers = {k: v for k, v in [h.split(":") for h in args.headers.split(",")]} if args.headers else None

    if args.method == "POST":
        data = {k: v for k, v in [d.split(":") for d in args.data.split(",")]}
        r = requests.post(args.url, headers=headers, data=data)
    elif args.method == "PUT":
        r = requests.put(args.url, headers=headers)
    else:
        raise Exception(f"Unsupported method: {args.method}")
    if r.status_code == requests.codes.ok:
        print(json.dumps(r.json()))
    else:
        raise Exception(f"{r.text}\nHEADER: {r.request.headers}\nBODY: {r.request.body}")
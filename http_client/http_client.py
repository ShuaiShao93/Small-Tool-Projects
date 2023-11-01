import requests
import argparse

parser = argparse.ArgumentParser(description="HTTP Client")
parser.add_argument("--url", help="URL to make request to")
parser.add_argument("--method", choices=["PUT"], help="HTTP method to use")
parser.add_argument(
    "--headers",
    help='Headers to send with request, e.g. "Content-Type:application/json,X-My-Header:123"',
)


if __name__ == "__main__":
    args = parser.parse_args()

    if args.method == "PUT":
        headers = {k: v for k, v in [h.split(":") for h in args.headers.split(",")]}
        print(headers)
        r = requests.put(args.url, headers=headers)
        if r.status_code == requests.codes.ok:
            print(r.json())
        else:
            raise Exception(r.text)

#!/usr/bin/env python3
"""Check connectivity to configured DEEPSEEK_BASE_URL using httpx."""
import os
import sys
import traceback
from dotenv import load_dotenv
import httpx


def main():
    load_dotenv()
    url = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    print('Testing URL:', url)
    try:
        r = httpx.get(url, timeout=15.0)
        print('STATUS', r.status_code)
        print('HEADERS:', dict(r.headers))
        text = (r.text or '')[:1000]
        print('BODY PREVIEW:', text)

        # If we have an API key available, try again with Authorization header
        key = os.environ.get('DEEPSEEK_API_KEY')
        if key:
            print('\nTesting with Authorization header...')
            headers = {'Authorization': f'Bearer {key}'}
            r2 = httpx.get(url, headers=headers, timeout=15.0)
            print('WITH-KEY STATUS', r2.status_code)
            print('WITH-KEY HEADERS:', dict(r2.headers))
            print('WITH-KEY BODY PREVIEW:', (r2.text or '')[:1000])
        else:
            print('\nNo DEEPSEEK_API_KEY found in environment; skipping auth test')

        return 0
    except Exception:
        print('EXCEPTION:')
        traceback.print_exc()
        return 2


if __name__ == '__main__':
    sys.exit(main())

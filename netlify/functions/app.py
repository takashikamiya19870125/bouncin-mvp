#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Netlify Functions用のエントリーポイント
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 環境変数でデータディレクトリを設定
os.environ['DATA_DIR'] = str(project_root / 'data')

from app import app

def handler(event, context):
    """Netlify Functions handler"""
    # WSGIアプリケーションをサーバーレス環境で実行
    try:
        from werkzeug.serving import make_server
        from werkzeug.wrappers import Request, Response
        
        # イベントからリクエストを作成
        environ = {
            'REQUEST_METHOD': event.get('httpMethod', 'GET'),
            'PATH_INFO': event.get('path', '/'),
            'QUERY_STRING': event.get('queryStringParameters', ''),
            'CONTENT_TYPE': event.get('headers', {}).get('content-type', ''),
            'CONTENT_LENGTH': str(len(event.get('body', ''))),
            'wsgi.input': event.get('body', ''),
            'wsgi.url_scheme': 'https',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '443',
        }
        
        # ヘッダーを追加
        for key, value in event.get('headers', {}).items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                environ[f'HTTP_{key}'] = value
        
        # WSGIアプリケーションを実行
        response_data = []
        
        def start_response(status, headers):
            response_data.append((status, headers))
        
        result = app(environ, start_response)
        
        # レスポンスを構築
        status, headers = response_data[0]
        body = b''.join(result).decode('utf-8')
        
        return {
            'statusCode': int(status.split()[0]),
            'headers': dict(headers),
            'body': body
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }
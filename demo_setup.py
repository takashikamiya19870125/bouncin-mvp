#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bouncinデモデータ生成スクリプト
レビューアーがすぐに機能を体験できるよう、サンプルデータを生成します。
"""

import json
import os
import datetime
import uuid
import hashlib
from typing import Dict

DATA_DIR = 'data'

def hash_password(password: str) -> str:
    """パスワードをハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_demo_data():
    """デモ用データを生成"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 1. サンプルユーザーを作成
    persons = [
        {
            'id': 'manager-001',
            'name': '田中 太郎',
            'email': 'manager@demo.com',
            'department': '開発部',
            'password': hash_password('demo123'),
            'created_at': datetime.datetime.now().isoformat()
        },
        {
            'id': 'member-001',
            'name': '佐藤 花子',
            'email': 'member@demo.com',
            'department': '開発部',
            'password': hash_password('demo123'),
            'created_at': datetime.datetime.now().isoformat()
        }
    ]
    
    # 2. 関係を作成
    relationships = [
        {
            'id': 'rel-001',
            'manager_id': 'manager-001',
            'subordinate_id': 'member-001',
            'active': True,
            'created_at': datetime.datetime.now().isoformat()
        }
    ]
    
    # 3. サンプル準備データを作成
    preparations = [
        {
            'id': 'prep-001',
            'relationship_id': 'rel-001',
            'subordinate_id': 'member-001',
            'mood': '普通',
            'topics': ['新機能の開発進捗について', 'チーム内のコミュニケーション改善'],
            'consultation': 'TypeScriptの学習方法について相談したいです。効率的な学習リソースや実践的な進め方を教えてください。',
            'feedback': '最近のプロジェクトで責任のある作業を任せてもらえて成長を感じています。',
            'share_feedback': True,
            'created_at': datetime.datetime.now().isoformat(),
            'type': 'subordinate_preparation'
        }
    ]
    
    # 4. サンプル会議記録を作成
    past_date = datetime.datetime.now() - datetime.timedelta(days=7)
    meetings = [
        {
            'id': 'meeting-001',
            'relationship_id': 'rel-001',
            'date': past_date.isoformat(),
            'categories': ['目標・業績の進捗', '業務上の困りごと'],
            'key_points': [
                '新機能の開発が予定通り進んでいる',
                'TypeScriptの学習に興味を持っている',
                'チーム内のコミュニケーションを改善したい'
            ],
            'follow_up': 'TypeScriptの学習リソースを共有する',
            'manager_learning': '部下の学習意欲が高いことを確認。適切なサポートを提供していきたい。',
            'created_at': past_date.isoformat()
        }
    ]
    
    # 5. JSONファイルに保存
    with open(os.path.join(DATA_DIR, 'persons.json'), 'w', encoding='utf-8') as f:
        json.dump(persons, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(DATA_DIR, 'relationships.json'), 'w', encoding='utf-8') as f:
        json.dump(relationships, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(DATA_DIR, 'preparations.json'), 'w', encoding='utf-8') as f:
        json.dump(preparations, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(DATA_DIR, 'meetings.json'), 'w', encoding='utf-8') as f:
        json.dump(meetings, f, ensure_ascii=False, indent=2)
    
    print("🎉 デモデータの生成が完了しました！")
    print("\n📝 デモアカウント情報:")
    print("【上司アカウント】")
    print("  メール: manager@demo.com")
    print("  パスワード: demo123")
    print("  名前: 田中 太郎")
    print("\n【部下アカウント】")
    print("  メール: member@demo.com") 
    print("  パスワード: demo123")
    print("  名前: 佐藤 花子")
    print("\n🚀 以下のコマンドでアプリケーションを起動してください:")
    print("  python app.py")
    print("\n💡 ブラウザで http://127.0.0.1:5003 にアクセスして体験開始！")

if __name__ == '__main__':
    create_demo_data()
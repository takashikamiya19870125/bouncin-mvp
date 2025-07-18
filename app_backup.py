#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1on1アシスタント MVP
構造化クイック入力 → 過去内容表示 → アジェンダ生成
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import datetime
import os
from typing import Dict, List, Any
import uuid

app = Flask(__name__)
app.secret_key = 'one-on-one-assistant-mvp-secret-key'

# データファイルパス
DATA_DIR = 'data'
MEETINGS_FILE = os.path.join(DATA_DIR, 'meetings.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

# データディレクトリ作成
os.makedirs(DATA_DIR, exist_ok=True)

class DataManager:
    """データ管理クラス"""
    
    @staticmethod
    def load_json(file_path: str) -> List[Dict]:
        """JSONファイルからデータを読み込み"""
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    @staticmethod
    def save_json(file_path: str, data: List[Dict]) -> bool:
        """JSONファイルにデータを保存"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"データ保存エラー: {e}")
            return False

class UserManager:
    """ユーザー管理クラス"""
    
    @staticmethod
    def get_users() -> List[Dict]:
        """全ユーザー取得"""
        return DataManager.load_json(USERS_FILE)
    
    @staticmethod
    def add_user(name: str, role: str) -> str:
        """ユーザー追加"""
        users = UserManager.get_users()
        user_id = str(uuid.uuid4())
        user = {
            'id': user_id,
            'name': name,
            'role': role,  # 'manager' or 'subordinate'
            'created_at': datetime.datetime.now().isoformat()
        }
        users.append(user)
        DataManager.save_json(USERS_FILE, users)
        return user_id

class MeetingManager:
    """ミーティング管理クラス"""
    
    @staticmethod
    def get_meetings() -> List[Dict]:
        """全ミーティング取得"""
        return DataManager.load_json(MEETINGS_FILE)
    
    @staticmethod
    def get_meetings_by_pair(manager_id: str, subordinate_id: str) -> List[Dict]:
        """ペア別ミーティング取得（時系列順）"""
        meetings = MeetingManager.get_meetings()
        pair_meetings = [m for m in meetings 
                        if m.get('manager_id') == manager_id and m.get('subordinate_id') == subordinate_id]
        # 日付順にソート
        return sorted(pair_meetings, key=lambda x: x.get('date', ''), reverse=True)
    
    @staticmethod
    def save_meeting_summary(manager_id: str, subordinate_id: str, 
                           categories: List[str], key_points: List[str], 
                           follow_up: str = '') -> str:
        """ミーティング終了時の構造化データ保存"""
        meetings = MeetingManager.get_meetings()
        meeting_id = str(uuid.uuid4())
        meeting = {
            'id': meeting_id,
            'manager_id': manager_id,
            'subordinate_id': subordinate_id,
            'date': datetime.datetime.now().isoformat(),
            'categories': categories,
            'key_points': key_points,
            'follow_up': follow_up,
            'created_at': datetime.datetime.now().isoformat()
        }
        meetings.append(meeting)
        DataManager.save_json(MEETINGS_FILE, meetings)
        return meeting_id

class AgendaGenerator:
    """アジェンダ生成クラス"""
    
    @staticmethod
    def generate_agenda(previous_meeting: Dict) -> List[str]:
        """前回内容に基づくアジェンダ生成"""
        agenda = []
        
        # フォローアップ項目があれば最優先
        if previous_meeting.get('follow_up'):
            agenda.append(f"前回の継続: {previous_meeting['follow_up']}")
        
        # カテゴリ別の定型質問
        categories = previous_meeting.get('categories', [])
        
        if '目標・業績の進捗' in categories:
            agenda.append("目標の進捗状況はいかがですか？")
        
        if '業務上の困りごと' in categories:
            agenda.append("前回の困りごとは解決しましたか？")
        
        if 'チーム・人間関係' in categories:
            agenda.append("チーム内での変化はありましたか？")
        
        if 'スキル・成長相談' in categories:
            agenda.append("スキルアップの進捗を教えてください")
        
        if 'キャリア・将来の話' in categories:
            agenda.append("将来のキャリアについて話しましょう")
        
        if 'ワークライフバランス' in categories:
            agenda.append("最近の働き方で気になることは？")
        
        # 基本的な質問を追加
        agenda.append("新しい相談や課題はありますか？")
        agenda.append("今日特に話したいことはありますか？")
        
        return agenda[:5]  # 最大5個

# ルート設定
@app.route('/')
def index():
    """メインページ（役割選択）"""
    return render_template('role_selection.html')

@app.route('/manager/dashboard')
def manager_dashboard():
    """上司用ダッシュボード"""
    managers = [u for u in UserManager.get_users() if u['role'] == 'manager']
    subordinates = [u for u in UserManager.get_users() if u['role'] == 'subordinate']
    return render_template('manager/dashboard.html', managers=managers, subordinates=subordinates)

@app.route('/subordinate/dashboard')
def subordinate_dashboard():
    """部下用ダッシュボード"""
    managers = [u for u in UserManager.get_users() if u['role'] == 'manager']
    subordinates = [u for u in UserManager.get_users() if u['role'] == 'subordinate']
    return render_template('subordinate/dashboard.html', managers=managers, subordinates=subordinates)

@app.route('/manager/prepare')
def manager_prepare():
    """上司用事前準備ページ"""
    manager_id = request.args.get('manager_id')
    subordinate_id = request.args.get('subordinate_id')
    
    if not manager_id or not subordinate_id:
        flash('ユーザーIDが指定されていません', 'error')
        return redirect(url_for('manager_dashboard'))
    
    # 過去のミーティング取得
    meetings = MeetingManager.get_meetings_by_pair(manager_id, subordinate_id)
    previous_meeting = meetings[0] if meetings else None
    
    # アジェンダ生成
    agenda = []
    if previous_meeting:
        agenda = AgendaGenerator.generate_agenda(previous_meeting)
    else:
        # 初回ミーティングの場合
        agenda = [
            "お互いの自己紹介と期待値の共有",
            "現在の業務状況と感じている課題",
            "目標設定と今後の方向性について", 
            "困っていることや相談したいこと",
            "1on1で話したいことや改善したいこと"
        ]
    
    return render_template('manager/prepare.html',
                         manager_id=manager_id,
                         subordinate_id=subordinate_id,
                         previous_meeting=previous_meeting,
                         agenda=agenda)

@app.route('/manager/review')
def manager_review():
    """上司用振り返りページ（ミーティング終了記録）"""
    manager_id = request.args.get('manager_id')
    subordinate_id = request.args.get('subordinate_id')
    
    if not manager_id or not subordinate_id:
        flash('ユーザーIDが指定されていません', 'error')
        return redirect(url_for('manager_dashboard'))
    
    return render_template('manager/review.html',
                         manager_id=manager_id,
                         subordinate_id=subordinate_id)

@app.route('/subordinate/prepare')
def subordinate_prepare():
    """部下用事前準備ページ"""
    subordinate_id = request.args.get('subordinate_id')
    manager_id = request.args.get('manager_id')
    
    if not subordinate_id or not manager_id:
        flash('ユーザーIDが指定されていません', 'error')
        return redirect(url_for('subordinate_dashboard'))
    
    # 過去のミーティング取得
    meetings = MeetingManager.get_meetings_by_pair(manager_id, subordinate_id)
    previous_meeting = meetings[0] if meetings else None
    
    return render_template('subordinate/prepare.html',
                         subordinate_id=subordinate_id,
                         manager_id=manager_id,
                         previous_meeting=previous_meeting)

@app.route('/subordinate/reflection')
def subordinate_reflection():
    """部下用振り返りページ"""
    subordinate_id = request.args.get('subordinate_id')
    manager_id = request.args.get('manager_id')
    
    if not subordinate_id or not manager_id:
        flash('ユーザーIDが指定されていません', 'error')
        return redirect(url_for('subordinate_dashboard'))
    
    return render_template('subordinate/reflection.html',
                         subordinate_id=subordinate_id,
                         manager_id=manager_id)

@app.route('/meeting/start')
def meeting_start():
    """ミーティング開始ページ（過去内容表示＋アジェンダ生成）"""
    manager_id = request.args.get('manager_id')
    subordinate_id = request.args.get('subordinate_id')
    
    if not manager_id or not subordinate_id:
        flash('ユーザーIDが指定されていません', 'error')
        return redirect(url_for('index'))
    
    # 過去のミーティング取得
    meetings = MeetingManager.get_meetings_by_pair(manager_id, subordinate_id)
    previous_meeting = meetings[0] if meetings else None
    
    # アジェンダ生成
    agenda = []
    if previous_meeting:
        agenda = AgendaGenerator.generate_agenda(previous_meeting)
    else:
        # 初回ミーティングの場合
        agenda = [
            "お互いの自己紹介をしましょう",
            "現在の業務状況を教えてください",
            "目標や期待を共有しましょう", 
            "困っていることや相談したいことはありますか？",
            "1on1で話したいことを教えてください"
        ]
    
    return render_template('meeting_start.html',
                         manager_id=manager_id,
                         subordinate_id=subordinate_id,
                         previous_meeting=previous_meeting,
                         agenda=agenda)

@app.route('/meeting/end')
def meeting_end():
    """ミーティング終了ページ（構造化クイック入力）"""
    manager_id = request.args.get('manager_id')
    subordinate_id = request.args.get('subordinate_id')
    
    if not manager_id or not subordinate_id:
        flash('ユーザーIDが指定されていません', 'error')
        return redirect(url_for('index'))
    
    return render_template('meeting_end.html',
                         manager_id=manager_id,
                         subordinate_id=subordinate_id)

@app.route('/api/save_meeting', methods=['POST'])
def save_meeting():
    """ミーティング内容保存API"""
    data = request.get_json()
    
    manager_id = data.get('manager_id')
    subordinate_id = data.get('subordinate_id')
    categories = data.get('categories', [])
    key_points = data.get('key_points', [])
    follow_up = data.get('follow_up', '')
    
    if not manager_id or not subordinate_id:
        return jsonify({'success': False, 'error': 'Required fields missing'})
    
    meeting_id = MeetingManager.save_meeting_summary(
        manager_id, subordinate_id, categories, key_points, follow_up
    )
    
    return jsonify({'success': True, 'meeting_id': meeting_id})

@app.route('/api/save_preparation', methods=['POST'])
def save_preparation():
    """部下の事前準備データ保存API"""
    data = request.get_json()
    
    subordinate_id = data.get('subordinate_id')
    manager_id = data.get('manager_id')
    mood = data.get('mood')
    topics = data.get('topics', [])
    
    if not subordinate_id or not manager_id or not mood:
        return jsonify({'success': False, 'error': '必須項目が不足しています'})
    
    # 簡単な成功レスポンス（実際のデータ保存は省略）
    return jsonify({'success': True, 'message': '準備データを保存しました'})

@app.route('/api/save_subordinate_reflection', methods=['POST'])
def save_subordinate_reflection():
    """部下の振り返りデータ保存API"""
    data = request.get_json()
    
    subordinate_id = data.get('subordinate_id')
    manager_id = data.get('manager_id')
    satisfaction = data.get('satisfaction')
    gains = data.get('gains', [])
    
    if not subordinate_id or not manager_id or not satisfaction:
        return jsonify({'success': False, 'error': '必須項目が不足しています'})
    
    # 簡単な成功レスポンス（実際のデータ保存は省略）
    return jsonify({'success': True, 'message': '振り返りデータを保存しました'})

@app.route('/api/add_user', methods=['POST'])
def add_user():
    """ユーザー追加API"""
    data = request.get_json()
    name = data.get('name')
    role = data.get('role')
    
    if not name or not role:
        return jsonify({'success': False, 'error': 'Name and role required'})
    
    user_id = UserManager.add_user(name, role)
    return jsonify({'success': True, 'user_id': user_id})

if __name__ == '__main__':
    app.run(debug=True, port=5003)
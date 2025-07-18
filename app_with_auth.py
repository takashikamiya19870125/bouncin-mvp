#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1on1アシスタント MVP with Authentication
個人認証による現実的な組織構造対応
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import json
import datetime
import os
from typing import Dict, List, Any
import uuid
import hashlib
from functools import wraps

app = Flask(__name__)
app.secret_key = 'one-on-one-assistant-mvp-auth-secret-key'

# データファイルパス
DATA_DIR = 'data'
PERSONS_FILE = os.path.join(DATA_DIR, 'persons.json')
RELATIONSHIPS_FILE = os.path.join(DATA_DIR, 'relationships.json')
MEETINGS_FILE = os.path.join(DATA_DIR, 'meetings.json')

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

class PersonManager:
    """個人管理クラス"""
    
    @staticmethod
    def get_persons() -> List[Dict]:
        """全個人情報取得"""
        return DataManager.load_json(PERSONS_FILE)
    
    @staticmethod
    def get_person_by_email(email: str) -> Dict:
        """メールアドレスで個人情報取得"""
        persons = PersonManager.get_persons()
        for person in persons:
            if person.get('email') == email:
                return person
        return None
    
    @staticmethod
    def get_person_by_id(person_id: str) -> Dict:
        """IDで個人情報取得"""
        persons = PersonManager.get_persons()
        for person in persons:
            if person.get('id') == person_id:
                return person
        return None
    
    @staticmethod
    def create_person(name: str, email: str, department: str, password: str) -> str:
        """新しい個人を作成"""
        persons = PersonManager.get_persons()
        
        # 既存チェック
        if PersonManager.get_person_by_email(email):
            return None
        
        person_id = str(uuid.uuid4())
        person = {
            'id': person_id,
            'name': name,
            'email': email,
            'department': department,
            'password': PersonManager.hash_password(password),
            'created_at': datetime.datetime.now().isoformat()
        }
        
        persons.append(person)
        DataManager.save_json(PERSONS_FILE, persons)
        return person_id
    
    @staticmethod
    def hash_password(password: str) -> str:
        """パスワードをハッシュ化"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(email: str, password: str) -> bool:
        """パスワード認証"""
        person = PersonManager.get_person_by_email(email)
        if not person:
            return False
        return person['password'] == PersonManager.hash_password(password)

class RelationshipManager:
    """関係管理クラス"""
    
    @staticmethod
    def get_relationships() -> List[Dict]:
        """全関係情報取得"""
        return DataManager.load_json(RELATIONSHIPS_FILE)
    
    @staticmethod
    def get_subordinates(manager_id: str) -> List[Dict]:
        """部下一覧取得"""
        relationships = RelationshipManager.get_relationships()
        subordinates = []
        
        for rel in relationships:
            if rel.get('manager_id') == manager_id and rel.get('active', True):
                subordinate = PersonManager.get_person_by_id(rel['subordinate_id'])
                if subordinate:
                    subordinates.append({
                        'id': subordinate['id'],
                        'name': subordinate['name'],
                        'department': subordinate['department'],
                        'relationship_id': rel['id'],
                        'next_meeting': None  # TODO: 次回予定の実装
                    })
        
        return subordinates
    
    @staticmethod
    def get_managers(subordinate_id: str) -> List[Dict]:
        """上司一覧取得"""
        relationships = RelationshipManager.get_relationships()
        managers = []
        
        for rel in relationships:
            if rel.get('subordinate_id') == subordinate_id and rel.get('active', True):
                manager = PersonManager.get_person_by_id(rel['manager_id'])
                if manager:
                    managers.append({
                        'id': manager['id'],
                        'name': manager['name'],
                        'department': manager['department'],
                        'relationship_id': rel['id'],
                        'next_meeting': None  # TODO: 次回予定の実装
                    })
        
        return managers
    
    @staticmethod
    def create_relationship(manager_id: str, subordinate_id: str) -> str:
        """関係を作成"""
        relationships = RelationshipManager.get_relationships()
        
        # 既存関係チェック
        for rel in relationships:
            if (rel.get('manager_id') == manager_id and 
                rel.get('subordinate_id') == subordinate_id and 
                rel.get('active', True)):
                return None
        
        relationship_id = str(uuid.uuid4())
        relationship = {
            'id': relationship_id,
            'manager_id': manager_id,
            'subordinate_id': subordinate_id,
            'active': True,
            'created_at': datetime.datetime.now().isoformat()
        }
        
        relationships.append(relationship)
        DataManager.save_json(RELATIONSHIPS_FILE, relationships)
        return relationship_id

class MeetingManager:
    """ミーティング管理クラス"""
    
    @staticmethod
    def get_meetings() -> List[Dict]:
        """全ミーティング取得"""
        return DataManager.load_json(MEETINGS_FILE)
    
    @staticmethod
    def get_meetings_by_relationship(relationship_id: str) -> List[Dict]:
        """関係別ミーティング取得"""
        meetings = MeetingManager.get_meetings()
        relationship_meetings = [m for m in meetings if m.get('relationship_id') == relationship_id]
        return sorted(relationship_meetings, key=lambda x: x.get('date', ''), reverse=True)
    
    @staticmethod
    def save_meeting(relationship_id: str, categories: List[str], key_points: List[str], 
                    follow_up: str = '', manager_learning: str = '') -> str:
        """ミーティング記録保存"""
        meetings = MeetingManager.get_meetings()
        meeting_id = str(uuid.uuid4())
        
        meeting = {
            'id': meeting_id,
            'relationship_id': relationship_id,
            'date': datetime.datetime.now().isoformat(),
            'categories': categories,
            'key_points': key_points,
            'follow_up': follow_up,
            'manager_learning': manager_learning,
            'created_at': datetime.datetime.now().isoformat()
        }
        
        meetings.append(meeting)
        DataManager.save_json(MEETINGS_FILE, meetings)
        return meeting_id

# 認証デコレータ
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """現在のユーザー情報取得"""
    if 'user_id' in session:
        return PersonManager.get_person_by_id(session['user_id'])
    return None

# ルート設定
@app.route('/')
def index():
    """メインページ"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ログイン"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if PersonManager.verify_password(email, password):
            person = PersonManager.get_person_by_email(email)
            session['user_id'] = person['id']
            flash('ログインしました', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('メールアドレスまたはパスワードが間違っています', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """新規登録"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        
        if password != password_confirm:
            flash('パスワードが一致しません', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('パスワードは6文字以上で入力してください', 'error')
            return render_template('register.html')
        
        user_id = PersonManager.create_person(name, email, department, password)
        if user_id:
            flash('登録が完了しました。ログインしてください', 'success')
            return redirect(url_for('login'))
        else:
            flash('このメールアドレスは既に登録されています', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """ログアウト"""
    session.pop('user_id', None)
    flash('ログアウトしました', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """統合ダッシュボード"""
    current_user = get_current_user()
    subordinates = RelationshipManager.get_subordinates(current_user['id'])
    managers = RelationshipManager.get_managers(current_user['id'])
    
    # 統計情報の計算（簡易版）
    monthly_count = 0  # TODO: 実装
    avg_satisfaction = "4.2"  # TODO: 実装
    total_relationships = len(subordinates) + len(managers)
    
    return render_template('dashboard.html',
                         current_user=current_user,
                         subordinates=subordinates,
                         managers=managers,
                         monthly_count=monthly_count,
                         avg_satisfaction=avg_satisfaction,
                         total_relationships=total_relationships)

@app.route('/manager/prepare')
@login_required
def manager_prepare():
    """上司用事前準備ページ"""
    subordinate_id = request.args.get('subordinate_id')
    current_user = get_current_user()
    
    if not subordinate_id:
        flash('部下IDが指定されていません', 'error')
        return redirect(url_for('dashboard'))
    
    # 関係確認
    subordinates = RelationshipManager.get_subordinates(current_user['id'])
    subordinate = next((s for s in subordinates if s['id'] == subordinate_id), None)
    if not subordinate:
        flash('指定された部下との関係が見つかりません', 'error')
        return redirect(url_for('dashboard'))
    
    # 過去のミーティング取得
    meetings = MeetingManager.get_meetings_by_relationship(subordinate['relationship_id'])
    previous_meeting = meetings[0] if meetings else None
    
    # アジェンダ生成
    agenda = []
    if previous_meeting:
        agenda = generate_agenda(previous_meeting)
    else:
        agenda = [
            "お互いの自己紹介と期待値の共有",
            "現在の業務状況と感じている課題",
            "目標設定と今後の方向性について",
            "困っていることや相談したいこと",
            "1on1で話したいことや改善したいこと"
        ]
    
    return render_template('manager/prepare.html',
                         manager_id=current_user['id'],
                         subordinate_id=subordinate_id,
                         subordinate=subordinate,
                         previous_meeting=previous_meeting,
                         agenda=agenda)

def generate_agenda(previous_meeting: Dict) -> List[str]:
    """アジェンダ生成"""
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
    
    return agenda[:5]

@app.route('/manager/review')
@login_required
def manager_review():
    """上司用振り返りページ"""
    subordinate_id = request.args.get('subordinate_id')
    current_user = get_current_user()
    
    if not subordinate_id:
        flash('部下IDが指定されていません', 'error')
        return redirect(url_for('dashboard'))
    
    # 関係確認
    subordinates = RelationshipManager.get_subordinates(current_user['id'])
    subordinate = next((s for s in subordinates if s['id'] == subordinate_id), None)
    if not subordinate:
        flash('指定された部下との関係が見つかりません', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('manager/review.html',
                         manager_id=current_user['id'],
                         subordinate_id=subordinate_id,
                         subordinate=subordinate)

@app.route('/subordinate/prepare')
@login_required
def subordinate_prepare():
    """部下用事前準備ページ"""
    manager_id = request.args.get('manager_id')
    current_user = get_current_user()
    
    if not manager_id:
        flash('上司IDが指定されていません', 'error')
        return redirect(url_for('dashboard'))
    
    # 関係確認
    managers = RelationshipManager.get_managers(current_user['id'])
    manager = next((m for m in managers if m['id'] == manager_id), None)
    if not manager:
        flash('指定された上司との関係が見つかりません', 'error')
        return redirect(url_for('dashboard'))
    
    # 過去のミーティング取得
    meetings = MeetingManager.get_meetings_by_relationship(manager['relationship_id'])
    previous_meeting = meetings[0] if meetings else None
    
    return render_template('subordinate/prepare.html',
                         subordinate_id=current_user['id'],
                         manager_id=manager_id,
                         manager=manager,
                         previous_meeting=previous_meeting)

@app.route('/subordinate/reflection')
@login_required
def subordinate_reflection():
    """部下用振り返りページ"""
    manager_id = request.args.get('manager_id')
    current_user = get_current_user()
    
    if not manager_id:
        flash('上司IDが指定されていません', 'error')
        return redirect(url_for('dashboard'))
    
    # 関係確認
    managers = RelationshipManager.get_managers(current_user['id'])
    manager = next((m for m in managers if m['id'] == manager_id), None)
    if not manager:
        flash('指定された上司との関係が見つかりません', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('subordinate/reflection.html',
                         subordinate_id=current_user['id'],
                         manager_id=manager_id,
                         manager=manager)

# API エンドポイント
@app.route('/api/add_relationship', methods=['POST'])
@login_required
def add_relationship():
    """関係追加API"""
    data = request.get_json()
    current_user = get_current_user()
    
    if data.get('type') == 'subordinate':
        # 部下を追加
        subordinate_email = data.get('subordinate_email')
        subordinate = PersonManager.get_person_by_email(subordinate_email)
        
        if not subordinate:
            return jsonify({'success': False, 'error': '指定されたメールアドレスのユーザーが見つかりません'})
        
        if subordinate['id'] == current_user['id']:
            return jsonify({'success': False, 'error': '自分自身を部下として追加することはできません'})
        
        relationship_id = RelationshipManager.create_relationship(current_user['id'], subordinate['id'])
        if relationship_id:
            return jsonify({'success': True, 'relationship_id': relationship_id})
        else:
            return jsonify({'success': False, 'error': '既に関係が存在します'})
    
    elif data.get('type') == 'manager':
        # 上司を追加
        manager_email = data.get('manager_email')
        manager = PersonManager.get_person_by_email(manager_email)
        
        if not manager:
            return jsonify({'success': False, 'error': '指定されたメールアドレスのユーザーが見つかりません'})
        
        if manager['id'] == current_user['id']:
            return jsonify({'success': False, 'error': '自分自身を上司として追加することはできません'})
        
        relationship_id = RelationshipManager.create_relationship(manager['id'], current_user['id'])
        if relationship_id:
            return jsonify({'success': True, 'relationship_id': relationship_id})
        else:
            return jsonify({'success': False, 'error': '既に関係が存在します'})
    
    return jsonify({'success': False, 'error': '不正な要求です'})

@app.route('/api/save_meeting', methods=['POST'])
@login_required
def save_meeting():
    """ミーティング記録保存API"""
    data = request.get_json()
    current_user = get_current_user()
    
    subordinate_id = data.get('subordinate_id')
    categories = data.get('categories', [])
    key_points = data.get('key_points', [])
    follow_up = data.get('follow_up', '')
    manager_learning = data.get('manager_learning', '')
    
    # 関係確認
    subordinates = RelationshipManager.get_subordinates(current_user['id'])
    subordinate = next((s for s in subordinates if s['id'] == subordinate_id), None)
    if not subordinate:
        return jsonify({'success': False, 'error': '関係が見つかりません'})
    
    meeting_id = MeetingManager.save_meeting(
        subordinate['relationship_id'], categories, key_points, follow_up, manager_learning
    )
    
    return jsonify({'success': True, 'meeting_id': meeting_id})

if __name__ == '__main__':
    app.run(debug=True, port=5003)
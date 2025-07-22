#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway.appデプロイ時のデモデータ自動生成
"""

import os
import json
from demo_setup import create_demo_data

def init_demo_data_if_needed():
    """デモデータが存在しない場合に自動生成"""
    persons_file = os.path.join('data', 'persons.json')
    
    if not os.path.exists(persons_file):
        print("🚀 Initializing demo data for Railway.app deployment...")
        create_demo_data()
        print("✅ Demo data initialized successfully!")
    else:
        print("✅ Demo data already exists, skipping initialization.")

if __name__ == '__main__':
    init_demo_data_if_needed()
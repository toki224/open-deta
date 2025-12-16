"""
新規登録APIをテストするスクリプト
"""

import requests
import json

api_url = "http://localhost:5000/api/auth/signup"

# テストデータ
test_data = {
    "username": "testuser2",
    "email": "test2@example.com",
    "password": "test12345"
}

print("=== 新規登録APIテスト ===")
print(f"URL: {api_url}")
print(f"データ: {json.dumps(test_data, ensure_ascii=False)}")
print()

try:
    response = requests.post(api_url, json=test_data, headers={"Content-Type": "application/json"})
    
    print(f"ステータスコード: {response.status_code}")
    print(f"レスポンス: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print("✓ 新規登録成功！")
        else:
            print(f"✗ エラー: {data.get('error')}")
    else:
        print(f"✗ HTTPエラー: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("✗ エラー: APIサーバーに接続できません")
    print("  api_server.pyが起動しているか確認してください")
except Exception as e:
    print(f"✗ エラー: {e}")


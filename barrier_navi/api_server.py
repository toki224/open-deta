"""
Flask APIサーバー - stationsデータベースからデータを提供
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from database_connection import DatabaseConnection
import bcrypt

# .envファイルから環境変数を読み込む
# 明示的にパスを指定（api_server.pyと同じディレクトリの.envを読み込む）
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
CORS(app)  # CORSを有効化してフロントエンドからのアクセスを許可

# MySQL接続情報（環境変数から取得）
# 注意: パスワードは必ず.envファイルで設定してください
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),  # デフォルト値は空文字列（.envファイル必須）
    "database": os.getenv("MYSQL_DATABASE", "station")
}

# デバッグ: 環境変数の読み込み状況を確認
print("=== 環境変数の読み込み状況 ===")
print(f".envファイルのパス: {env_path}")
print(f".envファイルの存在: {os.path.exists(env_path)}")
print(f"MYSQL_HOST: {MYSQL_CONFIG['host']}")
print(f"MYSQL_PORT: {MYSQL_CONFIG['port']}")
print(f"MYSQL_USER: {MYSQL_CONFIG['user']}")
print(f"MYSQL_PASSWORD: {'***' if MYSQL_CONFIG['password'] else '(未設定)'}")
print(f"MYSQL_DATABASE: {MYSQL_CONFIG['database']}")
print("=" * 40)

# .envファイルが設定されているか確認（開発時の警告）
if not MYSQL_CONFIG["password"]:
    print("\n⚠️  警告: MYSQL_PASSWORDが設定されていません。")
    print(f"   .envファイルを確認してください: {env_path}")
    print("   .envファイルの例:")
    print("   MYSQL_HOST=localhost")
    print("   MYSQL_PORT=3306")
    print("   MYSQL_USER=root")
    print("   MYSQL_PASSWORD=your_password_here")
    print("   MYSQL_DATABASE=station\n")

BODY_METRIC_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "step_response_status": {"label": "段差への対応", "type": "flag", "required": 1},
    "has_guidance_system": {"label": "案内設備の設置の有無", "type": "flag", "required": 1},
    "has_accessible_restroom": {"label": "障害者対応型便所の設置の有無", "type": "flag", "required": 1},
    "has_accessible_gate": {"label": "障害者対応型改札口の設置の有無", "type": "flag", "required": 1},
    "has_fall_prevention": {"label": "転落防止のための設備の設置の有無", "type": "flag", "required": 1},
    "num_platforms": {"label": "プラットホームの有無", "type": "number", "required": 6},
    "num_step_free_platforms": {"label": "段差が解消されているプラットホームの有無", "type": "number", "required": 6},
    "num_elevators": {"label": "エレベーターの有無", "type": "number", "required": 4},
    "num_compliant_elevators": {"label": "移動等円滑化基準に適合しているエレベーターの有無", "type": "number", "required": 4},
    "num_escalators": {"label": "エスカレーターの有無", "type": "number", "required": 4},
    "num_compliant_escalators": {"label": "移動等円滑化基準に適合しているエスカレーターの有無", "type": "number", "required": 4},
    "num_other_lifts": {"label": "その他の昇降機の有無", "type": "number", "required": 2},
    "num_slopes": {"label": "傾斜路の有無", "type": "number", "required": 2},
    "num_compliant_slopes": {"label": "移動等円滑化基準に適合している傾斜路の有無", "type": "number", "required": 2},
    "num_wheelchair_accessible_platforms": {"label": "車いす使用者の円滑な乗降が可能なプラットホームの有無", "type": "number", "required": 6},
}

BODY_BASE_COLUMNS = [
    "id",
    "station_name",
    "railway_operator",
    "line_name",
    "prefecture",
    "city"
]
BODY_QUERY_COLUMNS = BODY_BASE_COLUMNS + list(BODY_METRIC_DEFINITIONS.keys())


def parse_weight_payload(payload: str) -> Dict[str, float]:
    """重み付け設定をJSON文字列から取得"""
    default_weight = 2.0
    weights = {key: default_weight for key in BODY_METRIC_DEFINITIONS}
    if not payload:
        return weights
    try:
        data = json.loads(payload)
        if isinstance(data, dict):
            for key, value in data.items():
                try:
                    numeric_value = float(value)
                except (TypeError, ValueError):
                    continue
                if key in weights and numeric_value > 0:
                    weights[key] = numeric_value
    except json.JSONDecodeError:
        pass
    return weights


def evaluate_metric(value: Any, definition: Dict[str, Any]) -> Dict[str, Any]:
    metric_type = definition.get("type", "flag")
    required = definition.get("required", 1) or 1
    result: Dict[str, Any] = {"raw_value": value, "required": required}

    if metric_type == "flag":
        met = str(value).strip() == "1"
        ratio = 1.0 if met else 0.0
        result.update({"processed_value": "○" if met else "×", "ratio": ratio, "met": met})
    else:
        try:
            numeric_value = float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            numeric_value = 0.0
        ratio = min(numeric_value / required, 1.0) if required else 0.0
        met = numeric_value >= required
        result.update({"processed_value": numeric_value, "ratio": ratio, "met": met})

    return result


def compute_body_score(row: Dict[str, Any], weights: Dict[str, float], include_details: bool = False) -> Dict[str, Any]:
    total_weight = 0.0
    achieved_weight = 0.0
    met_items = 0
    details: List[Dict[str, Any]] = []

    for field, definition in BODY_METRIC_DEFINITIONS.items():
        weight = weights.get(field, 1.0)
        total_weight += weight
        metric_result = evaluate_metric(row.get(field), definition)
        achieved_weight += metric_result["ratio"] * weight
        if metric_result["met"]:
            met_items += 1

        if include_details:
            details.append({
                "key": field,
                "label": definition["label"],
                "value": metric_result["processed_value"],
                "raw_value": metric_result["raw_value"],
                "ratio": round(metric_result["ratio"], 2),
                "met": metric_result["met"],
                "type": definition["type"],
                "weight": weight
            })

    percentage = (achieved_weight / total_weight) * 100 if total_weight else 0
    return {
        "met_items": met_items,
        "total_items": len(BODY_METRIC_DEFINITIONS),
        "percentage": round(percentage, 1),
        "weighted_score": round(achieved_weight, 2),
        "max_weighted_score": round(total_weight, 2),
        "details": details if include_details else None
    }


def build_body_station_response(row: Dict[str, Any], weights: Dict[str, float], include_details: bool = False) -> Dict[str, Any]:
    score = compute_body_score(row, weights, include_details=include_details)
    response = {
        "station_id": row.get("id"),
        "station_name": row.get("station_name"),
        "prefecture": row.get("prefecture"),
        "city": row.get("city"),
        "operator": row.get("railway_operator"),
        "line_name": row.get("line_name"),
        "score": {
            "met_items": score["met_items"],
            "total_items": score["total_items"],
            "percentage": score["percentage"],
            "label": f"{score['met_items']}/{score['total_items']}点"
        }
    }
    if include_details:
        # metricsから"required"を除外
        metrics_without_required = []
        for metric in score["details"]:
            metric_copy = {k: v for k, v in metric.items() if k != "required"}
            metrics_without_required.append(metric_copy)
        
        response["metrics"] = metrics_without_required
        response["score"]["weighted_score"] = score["weighted_score"]
        response["score"]["max_weighted_score"] = score["max_weighted_score"]
    return response


@app.route('/api/stations', methods=['GET'])
def get_stations():
    """全駅データを取得"""
    try:
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        prefecture = request.args.get('prefecture', default=None, type=str)
        
        db = DatabaseConnection(**MYSQL_CONFIG)
        
        query = "SELECT * FROM stations WHERE 1=1"
        params = []
        
        if prefecture:
            query += " AND prefecture = %s"
            params.append(prefecture)
        
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        stations = db.execute_query(query, tuple(params) if params else None)
        db.close()
        
        return jsonify({
            "success": True,
            "data": stations,
            "count": len(stations)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/stations/<int:station_id>', methods=['GET'])
def get_station(station_id):
    """特定の駅データを取得"""
    try:
        db = DatabaseConnection(**MYSQL_CONFIG)
        stations = db.execute_query(
            "SELECT * FROM stations WHERE id = %s",
            (station_id,)
        )
        db.close()
        
        if stations:
            return jsonify({
                "success": True,
                "data": stations[0]
            })
        else:
            return jsonify({
                "success": False,
                "error": "Station not found"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/stations/count', methods=['GET'])
def get_stations_count():
    """駅の総数を取得"""
    try:
        db = DatabaseConnection(**MYSQL_CONFIG)
        result = db.execute_query("SELECT COUNT(*) as total FROM stations")
        db.close()
        
        return jsonify({
            "success": True,
            "count": result[0]['total']
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/stations/prefectures', methods=['GET'])
def get_prefectures():
    """都道府県一覧を取得"""
    try:
        db = DatabaseConnection(**MYSQL_CONFIG)
        prefectures = db.execute_query("""
            SELECT prefecture, COUNT(*) as count 
            FROM stations 
            WHERE prefecture IS NOT NULL 
            GROUP BY prefecture 
            ORDER BY count DESC
        """)
        db.close()
        
        return jsonify({
            "success": True,
            "data": prefectures
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/stations/statistics', methods=['GET'])
def get_statistics():
    """バリアフリー設備の統計を取得"""
    try:
        db = DatabaseConnection(**MYSQL_CONFIG)
        stats = db.execute_query("""
            SELECT 
                COUNT(*) as total_stations,
                SUM(CASE WHEN has_tactile_paving = 1 THEN 1 ELSE 0 END) as with_tactile_paving,
                SUM(CASE WHEN has_guidance_system = 1 THEN 1 ELSE 0 END) as with_guidance_system,
                SUM(CASE WHEN has_accessible_restroom = 1 THEN 1 ELSE 0 END) as with_accessible_restroom,
                SUM(CASE WHEN has_accessible_gate = 1 THEN 1 ELSE 0 END) as with_accessible_gate,
                SUM(CASE WHEN num_elevators > 0 THEN 1 ELSE 0 END) as with_elevators
            FROM stations
        """)
        db.close()
        
        return jsonify({
            "success": True,
            "data": stats[0] if stats else {}
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/stations/search', methods=['GET'])
def search_stations():
    """駅名で検索"""
    try:
        keyword = request.args.get('keyword', default='', type=str)
        limit = request.args.get('limit', default=50, type=int)
        
        if not keyword:
            return jsonify({
                "success": False,
                "error": "Keyword parameter is required"
            }), 400
        
        db = DatabaseConnection(**MYSQL_CONFIG)
        stations = db.execute_query(
            "SELECT * FROM stations WHERE station_name LIKE %s LIMIT %s",
            (f"%{keyword}%", limit)
        )
        db.close()
        
        return jsonify({
            "success": True,
            "data": stations,
            "count": len(stations)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/body/stations', methods=['GET'])
def get_body_accessible_stations():
    """身体障害者向けスコア付きの駅一覧（修正版：全件数取得付き）"""
    try:
        keyword = request.args.get('keyword', default='', type=str).strip()
        prefecture = request.args.get('prefecture', default=None, type=str)
        limit = request.args.get('limit', default=20, type=int)
        offset = request.args.get('offset', default=0, type=int)
        weights_param = request.args.get('weights', default=None, type=str)
        weights = parse_weight_payload(weights_param)
        filters_param = request.args.get('filters', default=None, type=str)

        # フィルタリストを取得
        filter_list = []
        if filters_param:
            try:
                filter_list = json.loads(filters_param)
                if not isinstance(filter_list, list):
                    filter_list = []
            except json.JSONDecodeError:
                filter_list = []

        # --- クエリ構築の共通部分 ---
        where_clause = "FROM stations WHERE 1=1"
        params: List[Any] = []

        if keyword:
            where_clause += " AND station_name LIKE %s"
            params.append(f"%{keyword}%")
        if prefecture:
            where_clause += " AND prefecture = %s"
            params.append(prefecture)

        for filter_key in filter_list:
            if filter_key in BODY_METRIC_DEFINITIONS:
                metric_def = BODY_METRIC_DEFINITIONS[filter_key]
                if metric_def["type"] == "flag":
                    where_clause += f" AND {filter_key} = %s"
                    params.append(1)
                else:
                    where_clause += f" AND {filter_key} > %s"
                    params.append(0)
        # ---------------------------

        db = DatabaseConnection(**MYSQL_CONFIG)

        # 1. 全件数を取得（ページネーション計算用）
        count_query = f"SELECT COUNT(*) as total {where_clause}"
        count_result = db.execute_query(count_query, tuple(params))
        total_count = count_result[0]['total'] if count_result else 0

        # 2. データ本体を取得
        columns = ", ".join(BODY_QUERY_COLUMNS)
        query = f"SELECT {columns} {where_clause} ORDER BY station_name LIMIT %s OFFSET %s"
        # LIMITとOFFSETをパラメータに追加
        data_params = params + [limit, offset]
        rows = db.execute_query(query, tuple(data_params))
        
        db.close()

        data = [build_body_station_response(row, weights, include_details=False) for row in rows]

        return jsonify({
            "success": True,
            "data": data,
            "count": len(data),       # 取得したデータ数
            "total_count": total_count # ★追加：全件数
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/body/stations/<int:station_id>', methods=['GET'])
def get_body_accessible_station_detail(station_id: int):
    """身体障害者向けスコアの詳細"""
    try:
        weights_param = request.args.get('weights', default=None, type=str)
        weights = parse_weight_payload(weights_param)

        columns = ", ".join(BODY_QUERY_COLUMNS)
        query = f"SELECT {columns} FROM stations WHERE id = %s"

        db = DatabaseConnection(**MYSQL_CONFIG)
        rows = db.execute_query(query, (station_id,))
        db.close()

        if not rows:
            return jsonify({
                "success": False,
                "error": "Station not found"
            }), 404

        detail = build_body_station_response(rows[0], weights, include_details=True)

        return jsonify({
            "success": True,
            "data": detail
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 認証関連API ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """ログイン処理"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                "success": False,
                "error": "ユーザー名とパスワードを入力してください"
            }), 400
        
        db = DatabaseConnection(**MYSQL_CONFIG)
        
        # ユーザー名またはメールアドレスで検索
        # usersテーブルのカラム名を確認して適切に変更してください
        user = db.execute_query(
            "SELECT * FROM users WHERE username = %s OR email = %s LIMIT 1",
            (username, username)
        )
        
        if not user:
            db.close()
            return jsonify({
                "success": False,
                "error": "ユーザー名またはパスワードが正しくありません"
            }), 401
        
        user = user[0]
        
        # パスワードの検証
        # カラム名がpassword_hashの場合はそれを使用、passwordの場合はそれを使用
        password_hash = user.get('password_hash') or user.get('password')
        
        if not password_hash:
            db.close()
            return jsonify({
                "success": False,
                "error": "パスワード情報が見つかりません"
            }), 500
        
        # bcryptでパスワードを検証
        try:
            if isinstance(password_hash, bytes):
                password_hash = password_hash.decode('utf-8')
            
            if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                db.close()
                return jsonify({
                    "success": False,
                    "error": "ユーザー名またはパスワードが正しくありません"
                }), 401
        except Exception as e:
            # パスワードがハッシュ化されていない場合（開発用）
            # 本番環境では削除してください
            if password_hash != password:
                db.close()
                return jsonify({
                    "success": False,
                    "error": "ユーザー名またはパスワードが正しくありません"
                }), 401
        
        # 最終ログイン日時を更新（カラムが存在する場合）
        try:
            db.execute_non_query(
                "UPDATE users SET last_login_at = %s WHERE id = %s",
                (datetime.now(), user['id'])
            )
        except:
            pass  # last_login_atカラムが存在しない場合はスキップ
        
        db.close()
        
        # パスワード情報を除外して返す
        user_response = {k: v for k, v in user.items() if k not in ['password', 'password_hash']}
        
        return jsonify({
            "success": True,
            "data": user_response
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """新規ユーザー登録"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({
                "success": False,
                "error": "すべての項目を入力してください"
            }), 400
        
        if len(password) < 8:
            return jsonify({
                "success": False,
                "error": "パスワードは8文字以上で入力してください"
            }), 400
        
        db = DatabaseConnection(**MYSQL_CONFIG)
        
        # ユーザー名の重複チェック
        existing_user = db.execute_query(
            "SELECT id FROM users WHERE username = %s LIMIT 1",
            (username,)
        )
        if existing_user:
            db.close()
            return jsonify({
                "success": False,
                "error": "このユーザー名は既に使用されています"
            }), 400
        
        # メールアドレスの重複チェック
        existing_email = db.execute_query(
            "SELECT id FROM users WHERE email = %s LIMIT 1",
            (email,)
        )
        if existing_email:
            db.close()
            return jsonify({
                "success": False,
                "error": "このメールアドレスは既に使用されています"
            }), 400
        
        # パスワードをハッシュ化
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # ユーザーを登録
        # usersテーブルのカラム: id, username, email, password_hash
        try:
            db.execute_non_query(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password_hash)
            )
        except Exception as e:
            db.close()
            return jsonify({
                "success": False,
                "error": f"ユーザー登録に失敗しました: {str(e)}"
            }), 500
        
        db.close()
        
        return jsonify({
            "success": True,
            "message": "アカウントが作成されました"
        })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Signup error: {error_detail}")
        return jsonify({
            "success": False,
            "error": f"ユーザー登録に失敗しました: {str(e)}"
        }), 500


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """パスワードリセット（メール送信は未実装）"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({
                "success": False,
                "error": "メールアドレスを入力してください"
            }), 400
        
        db = DatabaseConnection(**MYSQL_CONFIG)
        
        # ユーザーを検索
        user = db.execute_query(
            "SELECT id, email FROM users WHERE email = %s LIMIT 1",
            (email,)
        )
        
        if not user:
            # セキュリティ上の理由で、ユーザーが存在しない場合も成功を返す
            db.close()
            return jsonify({
                "success": True,
                "message": "パスワードリセット用のリンクをメールアドレスに送信しました"
            })
        
        # ここで実際にはメール送信処理を行う
        # 今回は簡易的に成功を返す
        db.close()
        
        return jsonify({
            "success": True,
            "message": "パスワードリセット用のリンクをメールアドレスに送信しました"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/auth/profile', methods=['GET'])
def get_profile():
    """プロフィール情報を取得"""
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "ユーザーIDが必要です"
            }), 400
        
        db = DatabaseConnection(**MYSQL_CONFIG)
        
        # ユーザー情報を取得
        user = db.execute_query(
            "SELECT id, username, email FROM users WHERE id = %s LIMIT 1",
            (user_id,)
        )
        
        if not user:
            db.close()
            return jsonify({
                "success": False,
                "error": "ユーザーが見つかりません"
            }), 404
        
        user = user[0]
        
        # users_preferencesテーブルから設定を取得
        preferences = []
        try:
            preferences = db.execute_query(
                "SELECT disability_type, favorite_stations, preferred_features FROM users_preferences WHERE user_id = %s LIMIT 1",
                (user_id,)
            )
        except Exception as e:
            # users_preferencesテーブルが存在しない、またはエラーが発生した場合
            print(f"Warning: Failed to fetch from users_preferences: {str(e)}")
            preferences = []
        
        # JSONフィールドをパース
        profile_data = {
            "id": user.get("id"),
            "username": user.get("username"),
            "email": user.get("email"),
        }
        
        if preferences and len(preferences) > 0:
            pref = preferences[0]
            # disability_typeをパース
            disability_type = pref.get("disability_type")
            if disability_type:
                try:
                    # JSON文字列をパース（Unicodeエスケープも正しく処理される）
                    if isinstance(disability_type, str):
                        parsed = json.loads(disability_type)
                        profile_data["disability_type"] = parsed if isinstance(parsed, list) else [parsed] if parsed else []
                    else:
                        profile_data["disability_type"] = disability_type if isinstance(disability_type, list) else []
                except Exception as e:
                    print(f"Warning: Failed to parse disability_type: {e}")
                    profile_data["disability_type"] = []
            else:
                profile_data["disability_type"] = []
            
            # favorite_stationsをパースして駅IDから駅名に変換
            favorite_stations = pref.get("favorite_stations")
            if favorite_stations:
                try:
                    station_ids = json.loads(favorite_stations) if isinstance(favorite_stations, str) else favorite_stations
                    if isinstance(station_ids, list) and len(station_ids) > 0:
                        # 駅IDのリストから駅名を取得（SQLインジェクション対策のため整数に変換）
                        station_ids_int = []
                        for sid in station_ids:
                            try:
                                station_ids_int.append(int(sid))
                            except (ValueError, TypeError):
                                continue
                        
                        if station_ids_int:
                            # 駅IDの配列として返す（データベース上でIDで表示されるように）
                            profile_data["favorite_stations"] = station_ids_int
                        else:
                            profile_data["favorite_stations"] = []
                    else:
                        profile_data["favorite_stations"] = []
                except Exception as e:
                    print(f"Warning: Failed to parse favorite_stations: {e}")
                    profile_data["favorite_stations"] = []
            else:
                profile_data["favorite_stations"] = []
            
            # preferred_featuresをパース
            preferred_features = pref.get("preferred_features")
            if preferred_features:
                try:
                    profile_data["preferred_features"] = json.loads(preferred_features) if isinstance(preferred_features, str) else preferred_features
                except:
                    profile_data["preferred_features"] = []
            else:
                profile_data["preferred_features"] = []
        else:
            # users_preferencesにデータがない場合はデフォルト値
            profile_data["disability_type"] = []
            profile_data["favorite_stations"] = []
            profile_data["preferred_features"] = []
        
        db.close()
        
        return jsonify({
            "success": True,
            "data": profile_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/auth/profile', methods=['PUT'])
def update_profile():
    """プロフィール情報を更新"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        username = data.get('username', '').strip()
        disability_type = data.get('disability_type')
        favorite_stations = data.get('favorite_stations')
        preferred_features = data.get('preferred_features')
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "ユーザーIDが必要です"
            }), 400
        
        db = DatabaseConnection(**MYSQL_CONFIG)
        
        # ユーザーの存在確認
        user = db.execute_query(
            "SELECT id FROM users WHERE id = %s LIMIT 1",
            (user_id,)
        )
        
        if not user:
            db.close()
            return jsonify({
                "success": False,
                "error": "ユーザーが見つかりません"
            }), 404
        
        # ユーザー名の重複チェック（他のユーザーが使用していないか）
        if username:
            existing_username = db.execute_query(
                "SELECT id FROM users WHERE username = %s AND id != %s LIMIT 1",
                (username, user_id)
            )
            if existing_username:
                db.close()
                return jsonify({
                    "success": False,
                    "error": "このユーザー名は既に使用されています"
                }), 400
        
        # usersテーブルの更新（ユーザー名のみ）
        if username:
            try:
                db.execute_non_query(
                    "UPDATE users SET username = %s WHERE id = %s",
                    (username, user_id)
                )
            except Exception as e:
                db.close()
                return jsonify({
                    "success": False,
                    "error": f"ユーザー名の更新に失敗しました: {str(e)}"
                }), 500
        
        # users_preferencesテーブルの更新
        # 既存のレコードがあるか確認
        existing_pref = []
        try:
            existing_pref = db.execute_query(
                "SELECT user_id FROM users_preferences WHERE user_id = %s LIMIT 1",
                (user_id,)
            )
        except Exception as e:
            # users_preferencesテーブルが存在しない場合
            print(f"Warning: users_preferences table may not exist: {str(e)}")
            existing_pref = []
        
        disability_type_json = None
        favorite_stations_json = None
        preferred_features_json = None
        
        # 各フィールドをJSON文字列に変換（空の配列はNULLとして保存）
        if disability_type is not None:
            # 空の配列の場合はNULLとして保存
            if isinstance(disability_type, list) and len(disability_type) == 0:
                disability_type_json = None  # 空の配列はNULLとして保存
            elif isinstance(disability_type, list):
                # ensure_ascii=Falseで日本語をそのまま保存（Unicodeエスケープしない）
                disability_type_json = json.dumps(disability_type, ensure_ascii=False)
            else:
                disability_type_json = None
        else:
            disability_type_json = None  # 明示的にNoneを設定（既存の値は保持）
        
        if favorite_stations is not None:
            # 空の配列の場合はNULLとして保存
            if isinstance(favorite_stations, list) and len(favorite_stations) == 0:
                favorite_stations_json = None  # 空の配列はNULLとして保存
            elif isinstance(favorite_stations, list):
                favorite_stations_json = json.dumps(favorite_stations, ensure_ascii=False)
            else:
                favorite_stations_json = None
        else:
            favorite_stations_json = None  # 明示的にNoneを設定（既存の値は保持）
        
        if preferred_features is not None:
            # 空の配列の場合はNULLとして保存
            if isinstance(preferred_features, list) and len(preferred_features) == 0:
                preferred_features_json = None  # 空の配列はNULLとして保存
            elif isinstance(preferred_features, list):
                preferred_features_json = json.dumps(preferred_features, ensure_ascii=False)
            else:
                preferred_features_json = None
        else:
            preferred_features_json = None  # 明示的にNoneを設定（既存の値は保持）
        
        try:
            if existing_pref and len(existing_pref) > 0:
                # 既存レコードを更新
                update_fields = []
                params = []
                
                # 各フィールドを更新（Noneの場合はNULLとして保存）
                # 空の配列が送信された場合もNULLとして保存するため、常に更新する
                if disability_type_json is not None:
                    update_fields.append("disability_type = %s")
                    params.append(disability_type_json)
                else:
                    # 空の配列またはNoneの場合はNULLとして保存
                    update_fields.append("disability_type = NULL")
                
                if favorite_stations_json is not None:
                    update_fields.append("favorite_stations = %s")
                    params.append(favorite_stations_json)
                else:
                    # 空の配列またはNoneの場合はNULLとして保存
                    update_fields.append("favorite_stations = NULL")
                
                if preferred_features_json is not None:
                    update_fields.append("preferred_features = %s")
                    params.append(preferred_features_json)
                else:
                    # 空の配列またはNoneの場合はNULLとして保存
                    update_fields.append("preferred_features = NULL")
                
                # updated_atカラムが存在する場合
                try:
                    columns = db.execute_query("SHOW COLUMNS FROM users_preferences LIKE 'updated_at'")
                    if columns:
                        update_fields.append("updated_at = %s")
                        params.append(datetime.now())
                except:
                    pass
                
                if update_fields:
                    params.append(user_id)
                    query = f"UPDATE users_preferences SET {', '.join(update_fields)} WHERE user_id = %s"
                    db.execute_non_query(query, tuple(params))
            else:
                # 新規レコードを作成
                db.execute_non_query(
                    """INSERT INTO users_preferences 
                       (user_id, disability_type, favorite_stations, preferred_features) 
                       VALUES (%s, %s, %s, %s)""",
                    (user_id, disability_type_json, favorite_stations_json, preferred_features_json)
                )
            
            db.close()
            
            return jsonify({
                "success": True,
                "message": "プロフィールを更新しました"
            })
        except Exception as e:
            db.close()
            return jsonify({
                "success": False,
                "error": f"プロフィールの更新に失敗しました: {str(e)}"
            }), 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    print("Flask APIサーバーを起動します...")
    print("http://localhost:5000 でアクセスできます")
    app.run(debug=True, port=5000)


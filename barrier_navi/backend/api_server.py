"""
Flask APIサーバー - stationsデータベースからデータを提供
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from database_connection import DatabaseConnection
import bcrypt
import os

# プロジェクトルートのパスを設定
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# .envファイルから環境変数を読み込む
# プロジェクトルートの.envを読み込む
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=env_path)

# フロントエンドファイルのパスを設定
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
VIEW_DIR = os.path.join(FRONTEND_DIR, 'view')
DIST_DIR = os.path.join(FRONTEND_DIR, 'dist')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
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
    # フラグ型（〇×で表せる項目）：設置されていれば1点
    "step_response_status": {"label": "段差への対応", "type": "flag", "required": 1},
    "has_guidance_system": {"label": "案内設備の設置の有無", "type": "flag", "required": 1},
    "has_accessible_restroom": {"label": "障害者対応型便所の設置の有無", "type": "flag", "required": 1},
    "has_accessible_gate": {"label": "障害者対応型改札口の設置の有無", "type": "flag", "required": 1},
    "has_fall_prevention": {"label": "転落防止のための設備の設置の有無", "type": "flag", "required": 1},
    # 割合型（分子/分母の形式で表示、基準値以上の割合であれば1点）
    "platform_ratio": {"label": "段差が解消されているプラットホームの割合", "type": "ratio", "numerator": "num_step_free_platforms", "denominator": "num_platforms", "required": 0.8},
    "elevator_ratio": {"label": "移動等円滑化基準に適合しているエレベーターの割合", "type": "ratio", "numerator": "num_compliant_elevators", "denominator": "num_elevators", "required": 0.8},
    "escalator_ratio": {"label": "移動等円滑化基準に適合しているエスカレーターの割合", "type": "ratio", "numerator": "num_compliant_escalators", "denominator": "num_escalators", "required": 0.8},
    # 数値型（基準値以上であれば1点、未満なら0点）
    "num_other_lifts": {"label": "その他の昇降機の設置基数", "type": "number", "required": 2},
    "num_slopes": {"label": "傾斜路の設置箇所数", "type": "number", "required": 2},
    "num_compliant_slopes": {"label": "移動等円滑化基準に適合している傾斜路の設置箇所数", "type": "number", "required": 2},
    "num_wheelchair_accessible_platforms": {"label": "車いす使用者の円滑な乗降が可能なプラットホームの数", "type": "number", "required": 6},
}

HEARING_METRIC_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    # フラグ型（〇×で表せる項目）：設置されていれば1点
    "has_guidance_system": {"label": "案内設備の設置の有無", "type": "flag", "required": 1},
    "has_accessible_restroom": {"label": "障害者対応型便所の設置の有無", "type": "flag", "required": 1},
    "has_accessible_gate": {"label": "障害者対応型改札口の設置の有無", "type": "flag", "required": 1},
    "has_fall_prevention": {"label": "転落防止のための設備の設置の有無", "type": "flag", "required": 1},
}

VISION_METRIC_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    # フラグ型（〇×で表せる項目）：設置されていれば1点
    "step_response_status": {"label": "段差への対応", "type": "flag", "required": 1},
    "has_tactile_paving": {"label": "視覚障害者誘導用ブロックの設置の有無", "type": "flag", "required": 1},
    "has_guidance_system": {"label": "案内設備の設置の有無", "type": "flag", "required": 1},
    "has_accessible_restroom": {"label": "障害者対応型便所の設置の有無", "type": "flag", "required": 1},
    "has_accessible_gate": {"label": "障害者対応型改札口の設置の有無", "type": "flag", "required": 1},
    "has_fall_prevention": {"label": "転落防止のための設備の設置の有無", "type": "flag", "required": 1},
    # 割合型（分子/分母の形式で表示、基準値以上の割合であれば1点）
    "platform_ratio": {"label": "段差が解消されているプラットホームの割合", "type": "ratio", "numerator": "num_step_free_platforms", "denominator": "num_platforms", "required": 0.8},
    # 数値型（基準値以上であれば1点、未満なら0点）
    "num_compliant_elevators": {"label": "移動等円滑化基準に適合しているエレベーターの設置基数", "type": "number", "required": 4},
    "num_compliant_escalators": {"label": "移動等円滑化基準に適合しているエスカレーターの設置基数", "type": "number", "required": 4},
    "num_compliant_slopes": {"label": "移動等円滑化基準に適合している傾斜路の設置箇所数", "type": "number", "required": 2},
}
BODY_BASE_COLUMNS = [
    "id",
    "station_name",
    "railway_operator",
    "line_name",
    "prefecture",
    "city"
]
# 割合型のメトリクスは計算値なので、元のカラム名を含める必要がある
BODY_QUERY_COLUMNS = BODY_BASE_COLUMNS + [
    # フラグ型
    "step_response_status",
    "has_guidance_system",
    "has_accessible_restroom",
    "has_accessible_gate",
    "has_fall_prevention",
    "has_tactile_paving",  # 視覚障害用
    # 割合計算に必要な元のカラム
    "num_platforms",
    "num_step_free_platforms",
    "num_elevators",
    "num_compliant_elevators",
    "num_escalators",
    "num_compliant_escalators",
    # 数値型
    "num_other_lifts",
    "num_slopes",
    "num_compliant_slopes",
    "num_wheelchair_accessible_platforms",
]


def evaluate_metric(value: Any, definition: Dict[str, Any], row: Dict[str, Any] = None) -> Dict[str, Any]:
    metric_type = definition.get("type", "flag")
    required = definition.get("required", 1) or 1
    result: Dict[str, Any] = {"raw_value": value, "required": required}

    if metric_type == "flag":
        met = str(value).strip() == "1"
        ratio = 1.0 if met else 0.0
        result.update({"processed_value": "○" if met else "×", "ratio": ratio, "met": met})
    elif metric_type == "ratio":
        # 割合型: 分子と分母のフィールドから計算
        numerator_key = definition.get("numerator")
        denominator_key = definition.get("denominator")
        if row and numerator_key and denominator_key:
            try:
                numerator = float(row.get(numerator_key, 0) or 0)
                denominator = float(row.get(denominator_key, 0) or 0)
            except (TypeError, ValueError):
                numerator = 0.0
                denominator = 0.0
            
            if denominator > 0:
                calculated_ratio = numerator / denominator
                percentage = calculated_ratio * 100
                met = calculated_ratio >= required
                result.update({
                    "processed_value": f"{int(numerator)}/{int(denominator)} ({percentage:.1f}%)",
                    "numerator": int(numerator),
                    "denominator": int(denominator),
                    "percentage": round(percentage, 1),
                    "ratio": calculated_ratio,
                    "met": met
                })
            else:
                result.update({
                    "processed_value": "0/0 (0.0%)",
                    "numerator": 0,
                    "denominator": 0,
                    "percentage": 0.0,
                    "ratio": 0.0,
                    "met": False
                })
        else:
            result.update({
                "processed_value": "-",
                "numerator": 0,
                "denominator": 0,
                "percentage": 0.0,
                "ratio": 0.0,
                "met": False
            })
    else:
        try:
            numeric_value = float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            numeric_value = 0.0
        ratio = min(numeric_value / required, 1.0) if required else 0.0
        met = numeric_value >= required
        result.update({"processed_value": numeric_value, "ratio": ratio, "met": met})

    return result


def compute_score(row: Dict[str, Any], definitions: Dict[str, Any], include_details: bool = False) -> Dict[str, Any]:
    """指定された基準(definitions)に基づいてスコアを計算"""
    met_items = 0
    details: List[Dict[str, Any]] = []

    for field, definition in definitions.items():
        metric_result = evaluate_metric(row.get(field), definition, row=row)
        if metric_result["met"]:
            met_items += 1

        if include_details:
            detail_item = {
                "key": field,
                "label": definition["label"],
                "value": metric_result["processed_value"],
                "raw_value": metric_result["raw_value"],
                "ratio": round(metric_result["ratio"], 2),
                "met": metric_result["met"],
                "type": definition["type"],
                "required": definition["required"]
            }
            # 割合型の場合は追加情報を含める
            if definition.get("type") == "ratio":
                detail_item["numerator"] = metric_result.get("numerator", 0)
                detail_item["denominator"] = metric_result.get("denominator", 0)
                detail_item["percentage"] = metric_result.get("percentage", 0.0)
            details.append(detail_item)

    total_items = len(definitions)
    percentage = (met_items / total_items) * 100 if total_items > 0 else 0
    
    return {
        "met_items": met_items,
        "total_items": total_items,
        "percentage": round(percentage, 1),
        "details": details if include_details else None
    }


def build_station_response(row: Dict[str, Any], mode: str = 'body', include_details: bool = False) -> Dict[str, Any]:
    """レスポンス用データの構築（モードで切り替え）"""
    # モードに応じて評価基準を切り替える
    definitions = HEARING_METRIC_DEFINITIONS if mode == 'hearing' else VISION_METRIC_DEFINITIONS if mode == 'vision' else BODY_METRIC_DEFINITIONS
    
    score = compute_score(row, definitions, include_details=include_details)
    
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
        response["metrics"] = score["details"]
    return response

# ---------------------------------------------------------
# ★これを新しく追加してください（共通の検索・取得ロジック）
# ---------------------------------------------------------
def get_stations_with_score(mode: str):
    try:
        # モードに応じた定義を選択
        definitions = HEARING_METRIC_DEFINITIONS if mode == 'hearing' else VISION_METRIC_DEFINITIONS if mode == 'vision' else BODY_METRIC_DEFINITIONS
        
        keyword = request.args.get('keyword', default='', type=str).strip()
        prefecture = request.args.get('prefecture', default=None, type=str)
        line_name = request.args.get('line_name', default=None, type=str)
        limit = request.args.get('limit', default=20, type=int)
        offset = request.args.get('offset', default=0, type=int)
        filters_param = request.args.get('filters', default=None, type=str)
        sort_order = request.args.get('sort', default='none', type=str)

        filter_list = []
        if filters_param:
            try:
                filter_list = json.loads(filters_param)
                if not isinstance(filter_list, list):
                    filter_list = []
            except json.JSONDecodeError:
                filter_list = []

        where_clause = "FROM stations WHERE 1=1"
        params: List[Any] = []

        if keyword:
            where_clause += " AND station_name LIKE %s"
            params.append(f"%{keyword}%")
        if prefecture:
            where_clause += " AND prefecture = %s"
            params.append(prefecture)
        if line_name:
            search_line = line_name.replace('線', '')
            if search_line.endswith('新幹'):
                 pass 
            where_clause += " AND line_name LIKE %s"
            params.append(f"%{search_line}%")

        # 定義に基づいてフィルタリング
        for filter_key in filter_list:
            if filter_key in definitions:
                metric_def = definitions[filter_key]
                if metric_def["type"] == "flag":
                    where_clause += f" AND {filter_key} = %s"
                    params.append(1)
                elif metric_def["type"] == "ratio":
                    # 割合型: 分子と分母の両方が存在し、割合が基準値以上であることを確認
                    numerator_key = metric_def.get("numerator")
                    denominator_key = metric_def.get("denominator")
                    required_ratio = metric_def.get("required", 0.8)
                    if numerator_key and denominator_key:
                        # 分母が0より大きく、分子/分母 >= 基準値 の条件
                        where_clause += f" AND {denominator_key} > 0 AND ({numerator_key} / NULLIF({denominator_key}, 0)) >= %s"
                        params.append(required_ratio)
                else:
                    where_clause += f" AND {filter_key} > %s"
                    params.append(0)

        db = DatabaseConnection(**MYSQL_CONFIG)

        # ソート処理変更前（ページごとにDBから取得）
        # count_query = f"SELECT COUNT(*) as total {where_clause}"
        # count_result = db.execute_query(count_query, tuple(params))
        # total_count = count_result[0]['total'] if count_result else 0

        # columns = ", ".join(BODY_QUERY_COLUMNS)
        # query = f"SELECT {columns} {where_clause} ORDER BY station_name LIMIT %s OFFSET %s"
        # data_params = params + [limit, offset]
        # rows = db.execute_query(query, tuple(data_params))
        # db.close()
        # ここで mode を渡してレスポンスを作る
        # data = [build_station_response(row, mode=mode, include_details=False) for row in rows]


        # ソート処理変更後（全件取得してアプリ側でソート・ページング）
        columns = ", ".join(BODY_QUERY_COLUMNS)
        query = f"SELECT {columns} {where_clause} ORDER BY station_name"

        rows = db.execute_query(query, tuple(params))
        db.close()

        all_data = [build_station_response(row, mode=mode, include_details=False) for row in rows]
        total_count = len(all_data)

        if sort_order == 'score-asc':
            all_data.sort(key=lambda x: x['score']['percentage'])
        elif sort_order == 'score-desc':
            all_data.sort(key=lambda x: x['score']['percentage'], reverse=True)

        start = offset
        end = offset + limit
        paged_data = all_data[start:end]

        return jsonify({
            "success": True,
            "data": paged_data,
            "count": len(paged_data),
            "total_count": total_count
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def get_station_detail_with_score(station_id: int, mode: str):
    try:
        columns = ", ".join(BODY_QUERY_COLUMNS)
        query = f"SELECT {columns} FROM stations WHERE id = %s"
        db = DatabaseConnection(**MYSQL_CONFIG)
        rows = db.execute_query(query, (station_id,))
        db.close()

        if not rows:
            return jsonify({"success": False, "error": "Station not found"}), 404

        detail = build_station_response(rows[0], mode=mode, include_details=True)
        return jsonify({"success": True, "data": detail})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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
def get_body_stations():
    return get_stations_with_score(mode='body')
    
@app.route('/api/body/stations/<int:station_id>', methods=['GET'])
def get_body_detail(station_id: int):
    return get_station_detail_with_score(station_id, mode='body')

@app.route('/api/hearing/stations', methods=['GET'])
def get_hearing_stations():
    return get_stations_with_score(mode='hearing')

@app.route('/api/hearing/stations/<int:station_id>', methods=['GET'])
def get_hearing_detail(station_id):
    return get_station_detail_with_score(station_id, mode='hearing')

@app.route('/api/vision/stations', methods=['GET'])
def get_vision_stations():
    return get_stations_with_score(mode='vision')

@app.route('/api/vision/stations/<int:station_id>', methods=['GET'])
def get_vision_detail(station_id):
    return get_station_detail_with_score(station_id, mode='vision')

@app.route('/api/lines', methods=['GET'])
def get_lines():
    """路線名一覧を取得（プルダウン用）"""
    try:
        db = DatabaseConnection(**MYSQL_CONFIG)

        rows = db.execute_query(
            "SELECT DISTINCT line_name FROM stations WHERE line_name IS NOT NULL AND line_name != ''"
            )
        db.close()
        
        lines_set = set()
        for row in rows:
            line_val = row['line_name']
            if line_val:
                split_lines = line_val.split('・')
                for line in split_lines:
                    clean_line = line.strip()
                    if clean_line:
                        lines_set.add(clean_line)
        
        # 五十音順などでソートして返す
        return jsonify({
            "success": True,
            "data": sorted(list(lines_set))
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 静的ファイル提供 ====================

@app.route('/')
def index():
    """ルートパスでログイン画面を表示"""
    return send_file(os.path.join(VIEW_DIR, 'login.html'))

@app.route('/login')
def login_page():
    """ログイン画面"""
    return send_file(os.path.join(VIEW_DIR, 'login.html'))

@app.route('/home')
def home_page():
    """ホーム画面"""
    return send_file(os.path.join(VIEW_DIR, 'home.html'))

@app.route('/index')
def index_page():
    """一覧画面（身体障害向け）"""
    return send_file(os.path.join(VIEW_DIR, 'index.html'))

@app.route('/hearing')
def hearing_page():
    """聴覚障害向け一覧画面"""
    return send_file(os.path.join(VIEW_DIR, 'hearing.html'))

@app.route('/vision')
def vision_page():
    """視覚障害向け一覧画面"""
    return send_file(os.path.join(VIEW_DIR, 'vision.html'))

@app.route('/profile')
def profile_page():
    """プロフィール画面"""
    return send_file(os.path.join(VIEW_DIR, 'profile.html'))

@app.route('/detail')
def detail_page():
    """詳細画面"""
    return send_file(os.path.join(VIEW_DIR, 'detail.html'))

@app.route('/styles.css')
def styles_css():
    """CSSファイル"""
    return send_file(os.path.join(FRONTEND_DIR, 'styles.css'))

@app.route('/dist/<path:filename>')
def dist_files(filename):
    """distディレクトリ内のファイル（JS、CSS等）"""
    return send_from_directory(DIST_DIR, filename)

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
    port = int(os.getenv("FLASK_PORT", "5000"))
    host = os.getenv("FLASK_HOST", "0.0.0.0")  # Docker環境では0.0.0.0が必要
    debug = os.getenv("FLASK_ENV", "production") == "development"
    print(f"http://{host}:{port} でアクセスできます")
    # 作業ディレクトリをプロジェクトルートに変更
    os.chdir(BASE_DIR)
    app.run(debug=debug, host=host, port=port)


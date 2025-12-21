"""
Flask APIサーバー - stationsデータベースからデータを提供
"""

import json
import os
from typing import Dict, Any, List

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from database_connection import DatabaseConnection

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
    # フラグ型（〇×で表せる項目）：設置されていれば1点
    "step_response_status": {"label": "段差への対応", "type": "flag", "required": 1},
    "has_guidance_system": {"label": "案内設備の設置の有無", "type": "flag", "required": 1},
    "has_accessible_restroom": {"label": "障害者対応型便所の設置の有無", "type": "flag", "required": 1},
    "has_accessible_gate": {"label": "障害者対応型改札口の設置の有無", "type": "flag", "required": 1},
    "has_fall_prevention": {"label": "転落防止のための設備の設置の有無", "type": "flag", "required": 1},
    # 数値型（基準値以上であれば1点、未満なら0点）
    "num_platforms": {"label": "プラットホームの数", "type": "number", "required": 6},
    "num_step_free_platforms": {"label": "段差が解消されているプラットホームの数", "type": "number", "required": 6},
    "num_elevators": {"label": "エレベーターの設置基数", "type": "number", "required": 4},
    "num_compliant_elevators": {"label": "移動等円滑化基準に適合しているエレベーターの設置基数", "type": "number", "required": 4},
    "num_escalators": {"label": "エスカレーターの設置基数", "type": "number", "required": 4},
    "num_compliant_escalators": {"label": "移動等円滑化基準に適合しているエスカレーターの設置基数", "type": "number", "required": 4},
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

BODY_BASE_COLUMNS = [
    "id",
    "station_name",
    "railway_operator",
    "line_name",
    "prefecture",
    "city"
]
BODY_QUERY_COLUMNS = BODY_BASE_COLUMNS + list(BODY_METRIC_DEFINITIONS.keys())


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


def compute_score(row: Dict[str, Any], definitions: Dict[str, Any], include_details: bool = False) -> Dict[str, Any]:
    """指定された基準(definitions)に基づいてスコアを計算"""
    met_items = 0
    details: List[Dict[str, Any]] = []

    for field, definition in definitions.items():
        metric_result = evaluate_metric(row.get(field), definition)
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
                "required": definition["required"]
            })

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
    definitions = HEARING_METRIC_DEFINITIONS if mode == 'hearing' else BODY_METRIC_DEFINITIONS
    
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
        definitions = HEARING_METRIC_DEFINITIONS if mode == 'hearing' else BODY_METRIC_DEFINITIONS
        
        keyword = request.args.get('keyword', default='', type=str).strip()
        prefecture = request.args.get('prefecture', default=None, type=str)
        line_name = request.args.get('line_name', default=None, type=str)
        limit = request.args.get('limit', default=20, type=int)
        offset = request.args.get('offset', default=0, type=int)
        filters_param = request.args.get('filters', default=None, type=str)

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
                else:
                    where_clause += f" AND {filter_key} > %s"
                    params.append(0)

        db = DatabaseConnection(**MYSQL_CONFIG)

        count_query = f"SELECT COUNT(*) as total {where_clause}"
        count_result = db.execute_query(count_query, tuple(params))
        total_count = count_result[0]['total'] if count_result else 0

        columns = ", ".join(BODY_QUERY_COLUMNS)
        query = f"SELECT {columns} {where_clause} ORDER BY station_name LIMIT %s OFFSET %s"
        data_params = params + [limit, offset]
        rows = db.execute_query(query, tuple(data_params))
        db.close()

        # ここで mode を渡してレスポンスを作る
        data = [build_station_response(row, mode=mode, include_details=False) for row in rows]

        return jsonify({
            "success": True,
            "data": data,
            "count": len(data),
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


if __name__ == '__main__':
    print("Flask APIサーバーを起動します...")
    print("http://localhost:5000 でアクセスできます")
    app.run(debug=True, port=5000)


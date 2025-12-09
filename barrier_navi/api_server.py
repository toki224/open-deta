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
    """身体障害者向けスコア付きの駅一覧"""
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

        columns = ", ".join(BODY_QUERY_COLUMNS)
        query = f"SELECT {columns} FROM stations WHERE 1=1"
        params: List[Any] = []

        if keyword:
            query += " AND station_name LIKE %s"
            params.append(f"%{keyword}%")
        if prefecture:
            query += " AND prefecture = %s"
            params.append(prefecture)

        # 設備の有無でフィルタリング
        for filter_key in filter_list:
            if filter_key in BODY_METRIC_DEFINITIONS:
                metric_def = BODY_METRIC_DEFINITIONS[filter_key]
                if metric_def["type"] == "flag":
                    # flag型: 値が1のもののみ
                    query += f" AND {filter_key} = %s"
                    params.append(1)
                else:
                    # number型: 値が0より大きいもののみ
                    query += f" AND {filter_key} > %s"
                    params.append(0)

        query += " ORDER BY station_name LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        db = DatabaseConnection(**MYSQL_CONFIG)
        rows = db.execute_query(query, tuple(params))
        db.close()

        data = [build_body_station_response(row, weights, include_details=False) for row in rows]

        return jsonify({
            "success": True,
            "data": data,
            "count": len(data)
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


if __name__ == '__main__':
    print("Flask APIサーバーを起動します...")
    print("http://localhost:5000 でアクセスできます")
    app.run(debug=True, port=5000)


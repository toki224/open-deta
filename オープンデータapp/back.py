from fastapi import FastAPI, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import mysql.connector
import os
from dotenv import load_dotenv

# uvicorn起動　uvicorn back:app --reload

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_connection():
    connection = mysql.connector.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_DATABASE"]
    )
    try:
        yield connection
    finally:
        connection.close()

COLUMN_MAP = {
    'step_free': 'step_response_status',
    'platform_count': 'num_platforms',
    'step_free_platform_count': 'num_step_free_platforms',
    'elevator_count': 'num_elevators',
    'compliant_elevator_count': 'num_compliant_elevators',
    'escalator_count': 'num_escalators',
    'compliant_escalator_count': 'num_compliant_escalators',
    'other_lift_count': 'num_other_lifts',
    'slope_count': 'num_slopes',
    'compliant_slope_count': 'num_compliant_slopes',
    'info_facility': 'has_guidance_system',
    'toilet': 'has_accessible_restroom',
    'ticket_gate': 'has_accessible_gate',
    'wheelchair_platform_count': 'num_wheelchair_accessible_platforms',
    'fall_prevention': 'has_fall_prevention'
}

FLAG_KEYS = {
    'step_free', 'info_facility', 'toilet', 'ticket_gate', 'fall_prevention'
}

@app.get("/lines")
def get_lines(db = Depends(get_connection)):
    cursor = db.cursor()
    # 重複なし
    cursor.execute("SELECT DISTINCT line_name FROM stations")
    rows = cursor.fetchall()
    cursor.close()
    
    lines_set = set()
    for row in rows:
        if row[0]:
            split_lines = row[0].split('・')
            for line in split_lines:
                lines_set.add(line.strip())
    
    return sorted(list(lines_set))


@app.get("/stations")
def get_stations(
    name: Optional[str] = None,
    line_name: Optional[str] = None,
    
    step_free: bool = False,
    platform_count: bool = False,
    step_free_platform_count: bool = False,
    elevator_count: bool = False,
    compliant_elevator_count: bool = False,
    escalator_count: bool = False,
    compliant_escalator_count: bool = False,
    other_lift_count: bool = False,
    slope_count: bool = False,
    compliant_slope_count: bool = False,
    info_facility: bool = False,
    toilet: bool = False,
    ticket_gate: bool = False,
    wheelchair_platform_count: bool = False,
    fall_prevention: bool = False,
    db = Depends(get_connection)
):
    cursor = db.cursor(dictionary=True)

    sql = "SELECT *, station_name as name FROM stations WHERE 1=1"
    params = []

    # 駅名
    if name:
        sql += " AND station_name LIKE %s"
        params.append(f"%{name}%")

    #路線
    if line_name:
        sql += " AND line_name LIKE %s"
        params.append(f"%{line_name}%")

    # チェックボックス
    query_params = {
        'step_free': step_free,
        'platform_count': platform_count,
        'step_free_platform_count': step_free_platform_count,
        'elevator_count': elevator_count,
        'compliant_elevator_count': compliant_elevator_count,
        'escalator_count': escalator_count,
        'compliant_escalator_count': compliant_escalator_count,
        'other_lift_count': other_lift_count,
        'slope_count': slope_count,
        'compliant_slope_count': compliant_slope_count,
        'info_facility': info_facility,
        'toilet': toilet,
        'ticket_gate': ticket_gate,
        'wheelchair_platform_count': wheelchair_platform_count,
        'fall_prevention': fall_prevention
    }

    for param_key, is_checked in query_params.items():
        if is_checked:
            db_col = COLUMN_MAP.get(param_key)
            if db_col:
                if param_key in FLAG_KEYS:
                    sql += f" AND {db_col} = 1"
                else:
                    sql += f" AND {db_col} > 0"

    sql += " ORDER BY id"
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    cursor.close()

    results = []
    for row in rows:
        station_data = {"name": row['name']}
        
        for js_key, db_col in COLUMN_MAP.items():
            val = row.get(db_col)
            
            if js_key in FLAG_KEYS:
                if val == 1:
                    station_data[js_key] = True
            else:
                if val is not None and val > 0:
                    station_data[js_key] = val

        results.append(station_data)

    return results

app.mount("/", StaticFiles(directory="static", html=True), name="static")
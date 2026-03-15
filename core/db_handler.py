import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import math
import os

DB_PATH = "data/study.db"
CSV_PATH = "exam_db/1-7_haikantoponpu.csv"

def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check current schema for question_status
    cursor.execute("PRAGMA table_info(question_status)")
    columns = cursor.fetchall()
    needs_recreation = False
    if columns:
        for col in columns:
            if col[1] == 'question_id' and col[2] == 'INTEGER':
                needs_recreation = True
                break
    
    if needs_recreation:
        cursor.execute("DROP TABLE IF EXISTS study_history")
        cursor.execute("DROP TABLE IF EXISTS question_status")
        conn.commit()

    # Study History Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS study_history (
        id INTEGER PRIMARY KEY,
        question_id TEXT,
        is_correct INTEGER,
        ease_factor REAL DEFAULT 2.5,
        interval INTEGER DEFAULT 0,
        repetition INTEGER DEFAULT 0,
        next_review TEXT,
        mastery_level TEXT DEFAULT 'Unlearned',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Mastery status per question
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS question_status (
        question_id TEXT PRIMARY KEY,
        ease_factor REAL DEFAULT 2.5,
        interval INTEGER DEFAULT 0,
        repetition INTEGER DEFAULT 0,
        next_review TEXT,
        mastery_level TEXT DEFAULT 'Unlearned',
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def get_master_data():
    import json
    json_path = "exam_db/questions.json"
    
    # Ignore temporary files starting with ~$
    if os.path.exists(CSV_PATH) and not os.path.basename(CSV_PATH).startswith("~$"):
        try:
            # Try utf-8-sig first (handles BOM)
            df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
        except UnicodeDecodeError:
            # Fallback to cp932 (Shift-JIS)
            df = pd.read_csv(CSV_PATH, encoding='cp932')
        
        if not df.empty:
            return df

    # If CSV is missing or empty, try to load from JSON and save to CSV
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        flat_data = []
        for q in data:
            choices = q.get('choices', [])
            exps = q.get('choice_explanations', [])
            
            row = {
                'id': q.get('question_id'),
                'section': q.get('section_label'),
                'difficulty': q.get('difficulty'),
                'question': q.get('stem'),
                'choice_1': choices[0]['text'] if len(choices) > 0 else '',
                'choice_2': choices[1]['text'] if len(choices) > 1 else '',
                'choice_3': choices[2]['text'] if len(choices) > 2 else '',
                'choice_4': choices[3]['text'] if len(choices) > 3 else '',
                'answer': q.get('answer'),
                'exp_1': exps[0]['explanation'] if len(exps) > 0 else '',
                'exp_2': exps[1]['explanation'] if len(exps) > 1 else '',
                'exp_3': exps[2]['explanation'] if len(exps) > 2 else '',
                'exp_4': exps[3]['explanation'] if len(exps) > 3 else ''
            }
            flat_data.append(row)
        
        df = pd.DataFrame(flat_data)
        if not os.path.exists("exam_db"):
            os.makedirs("exam_db")
        df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
        return df

    # Fallback to empty DataFrame with correct columns
    return pd.DataFrame(columns=['id', 'section', 'difficulty', 'question', 'choice_1', 'choice_2', 'choice_3', 'choice_4', 'answer', 'exp_1', 'exp_2', 'exp_3', 'exp_4'])

def update_srs(question_id, quality):
    """
    quality: 0 (Again), 1 (Hard), 2 (Good), 3 (Easy)
    SM-2 Algorithm simplified with specific intervals
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT ease_factor, interval, repetition FROM question_status WHERE question_id = ?", (question_id,))
    row = cursor.fetchone()
    
    if row:
        ef, iv, rep = row
    else:
        ef, iv, rep = 2.5, 0, 0
    
    # User requested specific intervals:
    # Again: 1 day
    # Hard: 1 day
    # Good: 3 days
    # Easy: 15 days
    
    if quality == 0: # Again
        iv = 1
        rep = 0
    elif quality == 1: # Hard
        iv = 1
        rep = min(rep + 1, 1) # Keep in early stage
    elif quality == 2: # Good
        if rep == 0: iv = 1
        elif rep == 1: iv = 3
        else: iv = math.ceil(iv * ef)
        rep += 1
    elif quality == 3: # Easy
        iv = 15
        rep += 1
    
    # Ease factor adjustment (standard SM-2)
    q_map = {0: 0, 1: 2, 2: 4, 3: 5}
    q = q_map[quality]
    ef = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    if ef < 1.3:
        ef = 1.3
        
    next_review = (datetime.now() + timedelta(days=iv)).strftime('%Y-%m-%d')
    
    # Determine mastery level
    if quality == 3 or rep > 5:
        mastery = "Mastered"
    else:
        mastery = "Learning"
        
    cursor.execute('''
    INSERT OR REPLACE INTO question_status (question_id, ease_factor, interval, repetition, next_review, mastery_level, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (str(question_id), float(ef), int(iv), int(rep), str(next_review), str(mastery)))
    
    cursor.execute('''
    INSERT INTO study_history (question_id, is_correct, ease_factor, interval, repetition, next_review, mastery_level)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (str(question_id), int(1 if quality >= 2 else 0), float(ef), int(iv), int(rep), str(next_review), str(mastery)))
    
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    df_status = pd.read_sql_query("SELECT * FROM question_status", conn)
    df_history = pd.read_sql_query("SELECT * FROM study_history", conn)
    conn.close()
    return df_status, df_history

def get_due_questions():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT question_id FROM question_status WHERE next_review <= ?", conn, params=(today,))
    conn.close()
    return df['question_id'].tolist()

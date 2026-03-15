import sqlite3
import json
import os
from datetime import datetime

class DBHandler:
    def __init__(self, db_path='exam_db/exam_app.db'):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Questions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    question_id TEXT PRIMARY KEY,
                    section TEXT,
                    section_label TEXT,
                    question_no INTEGER,
                    stem TEXT,
                    choices TEXT,
                    answer TEXT,
                    difficulty TEXT,
                    choice_explanations TEXT
                )
            ''')
            # Performance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id TEXT,
                    is_correct BOOLEAN,
                    timestamp DATETIME,
                    FOREIGN KEY (question_id) REFERENCES questions(question_id)
                )
            ''')
            conn.commit()

    def load_questions_from_json(self, json_path='exam_db/questions.json'):
        if not os.path.exists(json_path):
            return False
        
        with open(json_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for q in questions:
                cursor.execute('''
                    INSERT OR REPLACE INTO questions (
                        question_id, section, section_label, question_no, stem, 
                        choices, answer, difficulty, choice_explanations
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    q.get('question_id'),
                    q.get('section'),
                    q.get('section_label'),
                    q.get('question_no'),
                    q.get('stem'),
                    json.dumps(q.get('choices', []), ensure_ascii=False),
                    q.get('answer'),
                    q.get('difficulty'),
                    json.dumps(q.get('choice_explanations', ''), ensure_ascii=False)
                ))
            conn.commit()
        return True

    def get_sections(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT section FROM questions')
            return [row[0] for row in cursor.fetchall()]

    def get_questions_by_section(self, section):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM questions WHERE section = ?', (section,))
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            questions = []
            for row in rows:
                q = dict(zip(columns, row))
                q['choices'] = json.loads(q['choices'])
                q['choice_explanations'] = json.loads(q['choice_explanations'])
                questions.append(q)
            return questions

    def save_result(self, question_id, is_correct):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO performance (question_id, is_correct, timestamp)
                VALUES (?, ?, ?)
            ''', (question_id, is_correct, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()

    def get_stats(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    q.section, 
                    COUNT(p.id) as total_attempts,
                    SUM(CASE WHEN p.is_correct THEN 1 ELSE 0 END) as correct_answers
                FROM performance p
                JOIN questions q ON p.question_id = q.question_id
                GROUP BY q.section
            ''')
            return cursor.fetchall()

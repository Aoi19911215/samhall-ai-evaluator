import json
import os
from datetime import datetime

def save_evaluation(name, age, gender, disability_type, scores, job_matches):
    os.makedirs('data/evaluations', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"data/evaluations/eval_{name}_{timestamp}.json"
    
    data = {
        'timestamp': timestamp,
        'name': name,
        'age': age,
        'gender': gender,

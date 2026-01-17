import os
import json
from openai import OpenAI

class TextAnalyzer:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found")
        self.client = OpenAI(api_key=api_key)
        
        self.skills = [
            "読解力", "文書作成力", "計算力", "時間管理能力",
            "容儀", "運動能力", "モビリティ", "身体的耐性",
            "集中力", "問題解決力", "協力・チーム力", "コミュニケーション力",
            "柔軟性", "個人業務遂行力", "サービスパフォーマンス"
        ]
    
    def analyze(self, text_responses):
        prompt = f"""
以下のテキスト回答から、15項目のスキルを0.0〜2.0で評価してください。

評価基準:
- 0.0-0.5: 限定的 (Limited) - 大幅なサポートが必要
- 0.6-1.4: 良好 (Good) - 標準的な業務を遂行可能
- 1.5-2.0: 高い (High) - 複雑な業務も優れた能力で遂行

15項目:
{', '.join(self.skills)}

テキスト回答:
{json.dumps(text_responses, ensure_ascii=False, indent=2)}

JSON形式で出力してください:
{{
  "読解力": 1.5,
  "文書作成力": 1.2,
  ...
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは障害者雇用の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            json_str = content.strip()
            if '```json' in json_str:
                json_str = json_str.split('```json')[1].split('```')[0].strip()
            elif '```' in json_str:
                json_str = json_str.split('```')[1].split('```')[0].strip()
            
            scores = json.loads(json_str)
            
            result = {}
            for skill in self.skills:
                result[skill] = float(scores.get(skill, 1.0))
            
            return result
            
        except Exception as e:
            print(f"Error in text analysis: {e}")
            return {skill: 1.0 for skill in self.skills}

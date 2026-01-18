import os
import json
from openai import OpenAI
import streamlit as st

class TextAnalyzer:
    def __init__(self):
        # APIキーを環境変数またはStreamlit Secretsから取得
        api_key = os.getenv('OPENAI_API_KEY') or st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found")
        
        # proxiesを指定せず、新しい形式で初期化
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
必ずJSON形式で、スキル名をキー、数値を値として出力してください。

評価基準:
- 0.0-0.5: 限定的 (Limited)
- 0.6-1.4: 良好 (Good)
- 1.5-2.0: 高い (High)

15項目:
{', '.join(self.skills)}

テキスト回答:
{json.dumps(text_responses, ensure_ascii=False)}
"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは障害者雇用の専門家です。必ず有効なJSON形式で回答してください。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }, # 強制的にJSONにする
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            scores = json.loads(content)
            
            result = {}
            for skill in self.skills:
                # 文字列で返ってきた場合も考慮してfloatに変換
                val = scores.get(skill, 1.0)
                result[skill] = float(val)
            
            return result
            
        except Exception as e:
            st.error(f"AI分析でエラーが発生しました: {e}")
            return {skill: 1.0 for skill in self.skills}

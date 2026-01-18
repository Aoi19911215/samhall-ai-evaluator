import openai
import streamlit as st
import json

class TextAnalyzer:
    def __init__(self):
        # StreamlitのSecretsからAPIキーを取得
        self.api_key = st.secrets["OPENAI_API_KEY"]
        self.client = openai.OpenAI(api_key=self.api_key)
        
        self.skills = [
            "読解力", "文書作成力", "計算力", "時間管理能力",
            "容儀", "運動能力", "モビリティ", "身体的耐性",
            "集中力", "問題解決力", "協力・チーム力", "コミュニケーション力",
            "柔軟性", "個人業務遂行力", "サービスパフォーマンス"
        ]

    def analyze(self, text_responses):
        """
        OpenAI APIを使用して回答を分析します。
        個人情報は一切含めず、テキスト回答のみを送信します。
        """
        # プロンプト（AIへの指示書）の作成
        prompt = f"""
        あなたは就労移行支援の専門家です。以下の「O-lys」評価に基づいた回答を分析し、
        各スキルのスコアを0.5から2.0の間で算出してください。

        【回答データ】
        {json.dumps(text_responses, ensure_ascii=False)}

        【評価項目】
        {", ".join(self.skills)}

        【出力形式】
        JSON形式で、項目名をキー、数値を値として出力してください。解説は不要です。
        例: {{"読解力": 1.5, "計算力": 1.2, ...}}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # 最もコスパの良いモデル
                messages=[
                    {"role": "system", "content": "あなたはプロの職業適性判定官です。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" } # JSONで受け取る設定
            )
            
            # AIからの回答をパース
            content = response.choices[0].message.content
            scores = json.loads(content)
            
            # 全項目が揃っているか確認し、不足があれば1.0で補完
            result = {skill: float(scores.get(skill, 1.0)) for skill in self.skills}
            return result

        except Exception as e:
            st.error(f"AI分析中にエラーが発生しました: {e}")
            # エラー時は基本点（1.0）を返す
            return {skill: 1.0 for skill in self.skills}

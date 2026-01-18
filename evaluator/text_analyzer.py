import json

class TextAnalyzer:
    def __init__(self):
        self.skills = [
            "読解力", "文書作成力", "計算力", "時間管理能力",
            "容儀", "運動能力", "モビリティ", "身体的耐性",
            "集中力", "問題解決力", "協力・チーム力", "コミュニケーション力",
            "柔軟性", "個人業務遂行力", "サービスパフォーマンス"
        ]
    
    def analyze(self, text_responses):
        """
        【セキュリティ配慮版】
        外部API（OpenAI等）を利用する場合でも、ここには『回答文』だけが届き、
        『誰のものか』という情報は届かないように設計します。
        """
        
        # --- 匿名化処理のシミュレーション ---
        # 実際にはここで、特定の固有名詞を [DUMMY] に置き換える処理などを追加可能です。
        cleaned_responses = {}
        for key, text in text_responses.items():
            # 前後の空白削除や、不必要な個人情報（仮）の除去
            cleaned_responses[key] = text.strip()

        # 現在はコストとセキュリティを考慮し、ローカル（簡易AI）で計算
        result = {skill: 1.0 for skill in self.skills}
        
        # 読解力
        res_reading = cleaned_responses.get('reading', '')
        if len(res_reading) > 20: result["読解力"] = 1.7
        
        # 計算力
        res_calc = cleaned_responses.get('calculation', '')
        if any(char.isdigit() for char in res_calc): result["計算力"] = 1.8
        
        # コミュニケーション
        res_comm = cleaned_responses.get('communication', '')
        if "相談" in res_comm or "連絡" in res_comm:
            result["コミュニケーション力"] = 1.9
            result["協力・チーム力"] = 1.7

        return result

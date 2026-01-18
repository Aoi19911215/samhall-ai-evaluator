import json

class TextAnalyzer:
    def __init__(self):
        # 15項目のスキル定義
        self.skills = [
            "読解力", "文書作成力", "計算力", "時間管理能力",
            "容儀", "運動能力", "モビリティ", "身体的耐性",
            "集中力", "問題解決力", "協力・チーム力", "コミュニケーション力",
            "柔軟性", "個人業務遂行力", "サービスパフォーマンス"
        ]
    
    def analyze(self, text_responses):
        """
        APIを使わず、回答の文字数やキーワードから簡易的にスコアを算出する
        """
        # 全項目を基本点（1.0）で初期化
        result = {skill: 1.0 for skill in self.skills}
        
        # 1. 読解・理解力の評価
        res_reading = text_responses.get('reading', '')
        if len(res_reading) > 30:
            result["読解力"] = 1.8
            result["集中力"] = 1.5
        elif len(res_reading) > 10:
            result["読解力"] = 1.3
        
        # 2. 文章作成力の評価
        res_writing = text_responses.get('writing', '')
        if len(res_writing) > 50:
            result["文書作成力"] = 1.9
            result["個人業務遂行力"] = 1.7
        elif len(res_writing) > 20:
            result["文書作成力"] = 1.4
            
        # 3. 計算・論理力の評価（数字や計算記号が含まれているか）
        res_calc = text_responses.get('calculation', '')
        if any(char.isdigit() for char in res_calc):
            result["計算力"] = 1.8
            result["問題解決力"] = 1.5
            if "円" in res_calc or "=" in res_calc:
                result["計算力"] = 2.0
        
        # 4. コミュニケーションの評価（ポジティブなキーワードがあるか）
        res_comm = text_responses.get('communication', '')
        keywords = ["相談", "話す", "報告", "連絡", "お願いします", "協力"]
        count = sum(1 for k in keywords if k in res_comm)
        
        if count >= 2:
            result["コミュニケーション力"] = 1.9
            result["協力・チーム力"] = 1.8
            result["サービスパフォーマンス"] = 1.6
        elif count == 1:
            result["コミュニケーション力"] = 1.4
            result["協力・チーム力"] = 1.3
            
        # 共通：身だしなみや運動能力などは、回答がしっかりしていれば標準点以上にする
        if all(len(r) > 10 for r in text_responses.values()):
            result["容儀"] = 1.5
            result["柔軟性"] = 1.4
            
        return result

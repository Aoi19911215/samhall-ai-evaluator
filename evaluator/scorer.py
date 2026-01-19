import math

class SamhallScorer:
    """
    ユーザーのスキルスコアと職種データベースを照合し、
    マッチング率を算出するクラス。
    """

    @staticmethod
    def calculate_final_scores(text_scores):
        """
        TextAnalyzerから受け取った生スコアを最終スコアとして整形します。
        将来的にここで重み付けなどの調整が可能です。
        """
        # 現在はAnalyzerのスコアをそのまま使用します
        return text_scores

    @staticmethod
    def match_jobs(user_scores, job_db):
        """
        職種データベースの各職種とユーザーのスコアを比較し、
        マッチ率（%）を計算して降順で返します。
        """
        matches = []
        if not isinstance(user_scores, dict):
            return []

        for job in job_db:
            if not isinstance(job, dict):
                continue
                
            total_diff = 0
            # job_database.jsonに定義されている要件を取得
            reqs = job.get('requirements', {})
            
            # 評価対象のスキル項目
            skills = ['reading', 'writing', 'calculation', 'communication']
            
            for skill in skills:
                # ユーザーの値を数値化（デフォルト0）
                val = user_scores.get(skill, 0)
                user_val = float(val) if isinstance(val, (int, float, str)) else 0
                
                # 職種の要求値を取得（デフォルト0.8）
                req_val = float(reqs.get(skill, 0.8))
                
                # --- スキル差の計算ロジック ---
                if user_val < req_val:
                    # スキルが不足している場合：ペナルティをマイルドに（係数3.0）
                    # これを大きくすると、マッチ率がガクンと下がります
                    total_diff += (req_val - user_val) * 3.0
                else:
                    # スキルが足りている場合：超過分をわずかに加点要素へ
                    total_diff += (user_val - req_val) * 0.5

            # --- 基本マッチ率の算出 ---
            # 85点をベースにし、スキルの差分を引いていきます（係数5.0）
            base_rate = 85.0 - (total_diff * 5.0) 
            
            # 【モチベーション維持】最低保証スコアを45.0%に設定
            # これにより「マッチ0%」という悲しい結果を防ぎます
            match_rate = max(45.0, base_rate)
            
            # --- 身体・環境条件による補正（マルチプライヤー） ---
            multiplier = 1.0
            
            # 1. 身体的負荷のチェック
            physical_info = str(user_scores.get('physical_info', ''))
            if job.get('physical_level') == 'heavy' and '重いものは不可' in physical_info:
                multiplier *= 0.8 # 適合しない場合は20%減
            
            # 2. 環境配慮のチェック
            env_info = str(user_scores.get('environment_info', ''))
            job_env = job.get('environment', 'なし')
            if job_env != 'なし' and job_env in env_info:
                multiplier *= 0.7 # 避けるべき環境に該当する場合は30%減
            
            # --- 最終スコアの決定 ---
            # 上限を99.0%に設定し、100%（完璧）ではない「伸びしろ」を表現
            final_rate = min(99.0, match_rate * multiplier)
            
            matches.append({
                'job': job,
                'match_rate': round(final_rate, 1) # 小数点第1位で丸める
            })
        
        # マッチ率が高い順（降順）にソートして返す
        return sorted(matches, key=lambda x: x['match_rate'], reverse=True)

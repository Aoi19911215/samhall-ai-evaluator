import math

class SamhallScorer:
    @staticmethod
    def calculate_final_scores(text_scores):
        return text_scores

    @staticmethod
    def match_jobs(user_scores, job_db):
        matches = []
        if not isinstance(user_scores, dict): return []

        for job in job_db:
            if not isinstance(job, dict): continue
                
            total_diff = 0
            reqs = job.get('requirements', {})
            skills = ['reading', 'writing', 'calculation', 'communication']
            
            for skill in skills:
                # ユーザーの値を数値化
                val = user_scores.get(skill, 0)
                user_val = float(val) if isinstance(val, (int, float, str)) else 0
                req_val = float(reqs.get(skill, 0.8)) # 要求値を少し下げてマッチしやすく
                
                # スキル差の計算（不足していてもペナルティをマイルドに）
                if user_val < req_val:
                    total_diff += (req_val - user_val) * 3.0 # 18→3へ大幅緩和
                else:
                    total_diff += (user_val - req_val) * 0.5

            # --- ここがポイント：マッチ率の底上げ ---
            # 100点から引くのではなく、85点くらいをベースにして「マイナス」を抑える
            base_rate = 85.0 - (total_diff * 5.0) 
            
            # 最低保証スコア：どんなに低くても45%は出るようにする
            match_rate = max(45.0, base_rate)
            
            # 身体・環境条件の掛け算（0.3→0.8など、下げすぎないように調整）
            multiplier = 1.0
            
            # 身体条件チェック
            physical_info = str(user_scores.get('physical_info', ''))
            if job.get('physical_level') == 'heavy' and '重いものは不可' in physical_info:
                multiplier *= 0.8 # 20%減に留める
            
            # 環境条件チェック
            env_info = str(user_scores.get('environment_info', ''))
            job_env = job.get('environment', 'なし')
            if job_env != 'なし' and job_env in env_info:
                multiplier *= 0.7 # 30%減に留める
            
            # 最終スコア算出（最高は99.0%に抑えて「伸びしろ」を作る）
            final_rate = min(99.0, match_rate * multiplier)
            
            matches.append({
                'job': job,
                'match_rate': round(final_rate, 1) # 87.4% のように表示
            })
        
        # マッチ率順に並び替え
        return sorted(matches, key=lambda x: x['match_rate'], reverse=True)

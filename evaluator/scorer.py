import math

class SamhallScorer:
    @staticmethod
    def calculate_final_scores(text_scores):
        # text_scoresが辞書であることを確認し、スコア部分のみを抽出
        if isinstance(text_scores, dict):
            return text_scores
        return {}

    @staticmethod
    def match_jobs(user_scores, job_db):
        matches = []
        
        # 安全策：user_scores が辞書でない場合は空リストを返す
        if not isinstance(user_scores, dict):
            return []

        for job in job_db:
            # job が辞書形式であることを確認
            if not isinstance(job, dict):
                continue
                
            total_diff = 0
            reqs = job.get('requirements', {})
            
            # 評価対象の4項目
            skills = ['reading', 'writing', 'calculation', 'communication']
            
            for skill in skills:
                # user_scores[skill] が辞書や文字列の場合に備え、安全に数値化
                val = user_scores.get(skill, 0)
                try:
                    user_val = float(val) if isinstance(val, (int, float, str)) else 0
                except (ValueError, TypeError):
                    user_val = 0
                
                req_val = float(reqs.get(skill, 1.0))
                
                # --- 精度向上のための計算ロジック ---
                if user_val < req_val:
                    # スキルが足りない場合は厳しく減点（差の1.5倍）
                    total_diff += (req_val - user_val) * 1.5
                else:
                    # スキルが余裕で足りている場合は、微量の加点（ピッタリ度を出すため）
                    total_diff += (user_val - req_val) * 0.1

            # ベースマッチ率（係数を12→15に上げると、より数値がバラけます）
            match_rate = 100 - (total_diff * 15)
            
            # --- 身体・環境条件による係数補正 ---
            multiplier = 1.0
            
            # 1. 身体負担の判定
            physical_lifting = user_scores.get('physical_lifting', '')
            if job.get('physical_level') == 'heavy' and '重いものは不可' in str(physical_lifting):
                multiplier *= 0.3 # 重労働NGなら30%まで低下
            
            # 2. 環境不適合の判定（避けるべき環境のリストをチェック）
            avoid_env = user_scores.get('avoid_env', [])
            job_env = job.get('environment', '')
            
            if isinstance(avoid_env, list) and job_env in avoid_env:
                multiplier *= 0.5 # 嫌な環境なら50%低下
            
            # 最終スコア算出
            final_rate = max(0, min(100.0, match_rate * multiplier))
            
            # 小数点第一位まで表示
            matches.append({
                'job': job,
                'match_rate': round(final_rate, 1)
            })
        
        # 高い順にソート
        return sorted(matches, key=lambda x: x['match_rate'], reverse=True)

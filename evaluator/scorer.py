import math

class SamhallScorer:
    @staticmethod
    def calculate_final_scores(text_scores):
        # AI分析のスコアをそのまま使用（0.0〜2.0の範囲を想定）
        return text_scores

    @staticmethod
    def match_jobs(user_scores, job_db):
        matches = []
        
        for job in job_db:
            # 1. スキルマッチング（距離計算方式）
            # 各項目の「理想値」とのズレを計算します
            total_diff = 0
            reqs = job.get('requirements', {})
            
            # 評価対象の4項目
            skills = ['reading', 'writing', 'calculation', 'communication']
            
            for skill in skills:
                user_val = user_scores.get(skill, 0)
                req_val = reqs.get(skill, 1.0) # 職種ごとの要求値（未設定なら1.0）
                
                # 要求値に足りない場合は大きく減点、超えている場合は少し加点
                if user_val < req_val:
                    total_diff += (req_val - user_val) * 1.5 # 不足分は厳しく
                else:
                    total_diff += (user_val - req_val) * 0.2 # 超過分はプラス要素としてわずかに反映

            # ベースのマッチ率計算（100点からズレを引く）
            # 係数を調整することで、パーセントの広がりを制御できます
            match_rate = 100 - (total_diff * 12)
            
            # 2. 身体・環境条件による「足切り係数」（重要！）
            multiplier = 1.0
            
            # 例：重労働職種なのに「重いものは不可」を選んでいる場合
            if job.get('physical_level') == 'heavy' and user_scores.get('physical_lifting') == '重いものは不可':
                multiplier *= 0.4 # 適合率を強制的に40%まで下げる
            
            # 例：屋外職種なのに「屋外」を避ける環境に入れている場合
            if job.get('environment') == 'outdoor' and '屋外（暑さ・寒さ）' in user_scores.get('avoid_env', []):
                multiplier *= 0.5
            
            # 最終スコアの算出（0-100の間に収める）
            final_rate = max(0, min(100, match_rate * multiplier))
            
            # 小数点第一位まで計算（例: 87.4%）
            matches.append({
                'job': job,
                'match_rate': round(final_rate, 1)
            })
        
        # マッチ率が高い順に並び替え
        return sorted(matches, key=lambda x: x['match_rate'], reverse=True)

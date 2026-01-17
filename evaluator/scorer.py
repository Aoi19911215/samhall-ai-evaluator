class SamhallScorer:
    @staticmethod
    def calculate_final_scores(text_scores):
        scores = {}
        for skill, score in text_scores.items():
            scores[skill] = score
        return scores
    
    @staticmethod
    def match_jobs(scores, job_database):
        matches = []
        for job in job_database.get('jobs', []):
            required = job.get('required_scores', {})
            match_count = 0
            total_count = len(required)
            
            for skill, req_score in required.items():
                user_score = scores.get(skill, 1.0)
                if user_score >= req_score:
                    match_count += 1
            
            match_rate = (match_count / total_count * 100) if total_count > 0 else 0
            
            matches.append({
                'job': job,
                'match_rate': match_rate,
                'matched_skills': match_count,
                'total_skills': total_count
            })
        
        return sorted(matches, key=lambda x: x['match_rate'], reverse=True)

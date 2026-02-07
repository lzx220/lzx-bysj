# app/services/similarity_search.py
class SimpleSimilaritySearch:
    """简单的相似性搜索（适合大学生项目）"""

    @staticmethod
    def find_similar_cases(current_record, limit=5):
        """查找相似病例"""
        from app.models import MedicalRecord

        # 简单规则：诊断相同就算相似
        similar = MedicalRecord.query.filter(
            MedicalRecord.id != current_record.id,
            MedicalRecord.diagnosis == current_record.diagnosis
        ).limit(limit).all()

        result = []
        for record in similar:
            result.append({
                'id': record.id,
                'patient_info': f"{record.patient.full_name if record.patient else '未知患者'}",
                'diagnosis': record.diagnosis,
                'symptoms': record.chief_complaint[:50] + '...' if len(
                    record.chief_complaint) > 50 else record.chief_complaint,
                'treatment': record.treatment_plan,
                'similarity': 0.8  # 固定相似度
            })

        return result

    @staticmethod
    def find_cases_by_treatment(treatment_type, limit=10):
        """按治疗类型查找"""
        from app.models import MedicalRecord

        cases = MedicalRecord.query.filter(
            MedicalRecord.treatment_plan.like(f'%{treatment_type}%')
        ).limit(limit).all()

        return cases
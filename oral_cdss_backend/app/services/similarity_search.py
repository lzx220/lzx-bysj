# similarity_search.py - 学生简化版

from app import db
from app.models import MedicalRecord, AssessmentResult


class SimpleSimilaritySearch:
    """简单版相似病例搜索 - 适合学生项目"""

    def __init__(self):
        # 简单权重，不需要机器学习
        self.weights = {
            'bone_loss_percentage': 1.0,
            'mobility_degree': 1.0,
            'caries_degree': 1.0,
            'periodontal_status': 1.0,
            'pulp_condition': 1.0,
            'oral_hygiene': 1.0,
            'smoking_status': 1.0,
            'diabetic_status': 1.0
        }

    def find_similar_cases(self, current_record, limit=5):
        """查找相似病例 - 超简单版"""
        try:
            # 1. 获取所有病历（排除当前病历）
            all_records = MedicalRecord.query.filter(
                MedicalRecord.id != current_record.id,
                MedicalRecord.is_finalized == True
            ).all()

            if not all_records:
                return []

            # 2. 为每个病历计算相似度
            results = []
            for record in all_records:
                # 计算相似度（0-100分）
                similarity_score = self._calculate_similarity(current_record, record)

                # 只保留相似度大于60分的
                if similarity_score > 60:
                    # 获取评估结果
                    assessment = AssessmentResult.query.filter_by(
                        medical_record_id=record.id,
                        is_latest=True
                    ).first()

                    # 添加到结果
                    results.append({
                        'record_id': record.id,
                        'patient_id': record.patient_id,
                        'chief_complaint': record.chief_complaint[:50] + "..." if len(
                            record.chief_complaint) > 50 else record.chief_complaint,
                        'diagnosis': record.diagnosis,
                        'treatment_plan': record.treatment_plan,
                        'visit_date': record.visit_date.strftime('%Y-%m-%d') if record.visit_date else None,
                        'similarity_score': similarity_score,  # 0-100分
                        'similarity_level': self._get_similarity_level(similarity_score),
                        'assessment': self._format_assessment(assessment)
                    })

            # 3. 按相似度排序，取前几个
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return results[:limit]

        except Exception as e:
            print(f"搜索出错（别担心，正常现象）: {str(e)}")
            return []

    def _calculate_similarity(self, record1, record2):
        """计算两个病历的相似度（0-100分）"""
        score = 0

        # 1. 检查主要诊断是否相似（占40分）
        if record1.diagnosis and record2.diagnosis:
            if record1.diagnosis.lower() == record2.diagnosis.lower():
                score += 40
            elif record1.diagnosis in record2.diagnosis or record2.diagnosis in record1.diagnosis:
                score += 20

        # 2. 检查主诉是否相似（占30分）
        if record1.chief_complaint and record2.chief_complaint:
            # 简单关键词匹配
            keywords1 = set(record1.chief_complaint.lower().split())
            keywords2 = set(record2.chief_complaint.lower().split())
            common_keywords = keywords1.intersection(keywords2)

            if common_keywords:
                score += min(30, len(common_keywords) * 5)

        # 3. 检查牙齿问题（占30分）
        # 骨吸收百分比相似
        if record1.bone_loss_percentage is not None and record2.bone_loss_percentage is not None:
            diff = abs(record1.bone_loss_percentage - record2.bone_loss_percentage)
            if diff < 10:
                score += 10
            elif diff < 20:
                score += 5

        # 牙齿松动度相似
        if record1.mobility_degree is not None and record2.mobility_degree is not None:
            if record1.mobility_degree == record2.mobility_degree:
                score += 10

        # 龋坏程度相似
        if record1.caries_degree and record2.caries_degree:
            if record1.caries_degree == record2.caries_degree:
                score += 10

        return min(100, score)  # 确保不超过100分

    def _get_similarity_level(self, score):
        """根据分数返回相似级别"""
        if score >= 80:
            return "高度相似"
        elif score >= 60:
            return "中度相似"
        elif score >= 40:
            return "轻度相似"
        else:
            return "不相似"

    def _format_assessment(self, assessment):
        """格式化评估结果"""
        if not assessment:
            return None

        return {
            'total_score': assessment.total_score,
            'risk_level': assessment.risk_level,
            'recommended_treatment': assessment.recommended_treatment
        }

    def find_cases_by_treatment(self, treatment_type, limit=10):
        """根据治疗类型查找病例"""
        try:
            records = MedicalRecord.query.join(
                AssessmentResult,
                AssessmentResult.medical_record_id == MedicalRecord.id
            ).filter(
                AssessmentResult.recommended_treatment == treatment_type,
                MedicalRecord.is_finalized == True
            ).limit(limit).all()

            cases = []
            for record in records:
                assessment = AssessmentResult.query.filter_by(
                    medical_record_id=record.id,
                    is_latest=True
                ).first()

                cases.append({
                    'record_id': record.id,
                    'patient_id': record.patient_id,
                    'diagnosis': record.diagnosis,
                    'treatment_plan': record.treatment_plan,
                    'visit_date': record.visit_date.strftime('%Y-%m-%d') if record.visit_date else None,
                    'assessment': self._format_assessment(assessment)
                })

            return cases

        except Exception as e:
            print(f"按治疗类型查找出错: {str(e)}")
            return []

    def validate_record(self, medical_record):
        """验证病历是否完整"""
        required_fields = ['diagnosis', 'chief_complaint']

        missing = []
        for field in required_fields:
            if not getattr(medical_record, field, None):
                missing.append(field)

        if missing:
            return False, f"缺少必要信息: {', '.join(missing)}"

        return True, "病历完整"


# 使用示例
def test_simple_search():
    """测试函数"""
    print("=== 简单相似性搜索测试 ===")

    # 创建搜索器
    search = SimpleSimilaritySearch()

    # 假设我们有一个当前病历
    class MockRecord:
        def __init__(self):
            self.id = 1
            self.diagnosis = "牙周炎"
            self.chief_complaint = "牙齿松动，牙龈出血"
            self.bone_loss_percentage = 30
            self.mobility_degree = 2
            self.caries_degree = "medium"
            self.treatment_plan = "牙周治疗"
            self.is_finalized = True
            self.patient_id = 100
            self.visit_date = None

    current = MockRecord()

    # 查找相似病例
    similar_cases = search.find_similar_cases(current, limit=3)

    print(f"找到 {len(similar_cases)} 个相似病例:")
    for i, case in enumerate(similar_cases, 1):
        print(f"{i}. {case['diagnosis']} - 相似度: {case['similarity_score']}分 ({case['similarity_level']})")
        print(f"   主诉: {case['chief_complaint']}")

    return similar_cases


if __name__ == "__main__":
    # 运行测试
    test_simple_search()
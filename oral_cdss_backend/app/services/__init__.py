# app/services/__init__.py
# 先注释掉所有导入，让系统能启动
# from .decision_algorithm import DecisionAlgorithm
# from .rule_engine import RuleEngine
# from .similarity_search import SimilaritySearch

# 或者如果必须导入，确保模块能正常导入
try:
    from .decision_algorithm import DecisionAlgorithm
    from .rule_engine import RuleEngine
    from .similarity_search import SimilaritySearch
except ImportError as e:
    print(f"服务导入警告: {e}")


    # 创建空类作为占位符
    class DecisionAlgorithm:
        pass


    class RuleEngine:
        pass


    class SimilaritySearch:
        pass
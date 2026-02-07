from app import db


def init_db():
    """初始化数据库"""
    try:
        # 在函数内部导入 models，避免循环导入
        from app.models import User, Patient, MedicalRecord, Rule, RuleCategory, AssessmentResult

        # 创建所有表
        db.create_all()

        # 创建默认管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@dentalcds.com',
                full_name='系统管理员',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)

        # 创建默认规则分类
        categories = [
            {'name': '牙体状况', 'description': '牙齿本身的健康状况', 'weight': 1.2, 'order': 1},
            {'name': '牙周状况', 'description': '牙龈和牙周组织的健康状况', 'weight': 1.0, 'order': 2},
            {'name': '咬合关系', 'description': '牙齿咬合和排列情况', 'weight': 0.8, 'order': 3},
            {'name': '患者因素', 'description': '患者个人习惯和健康状况', 'weight': 0.9, 'order': 4},
            {'name': '影像学检查', 'description': 'X光、CT等影像检查结果', 'weight': 1.1, 'order': 5}
        ]

        for cat_data in categories:
            category = RuleCategory.query.filter_by(name=cat_data['name']).first()
            if not category:
                category = RuleCategory(**cat_data)
                db.session.add(category)

        # 创建默认规则
        rules = [
            # 牙体状况规则
            {
                'category_id': 1,
                'name': '深龋齿',
                'description': '深度龋齿影响牙髓健康',
                'condition_field': 'caries_degree',
                'condition_operator': '=',
                'condition_value': 'deep',
                'score': -20,
                'risk_level': 'high',
                'treatment_suggestion': 'root_canal'
            },
            {
                'category_id': 1,
                'name': '牙髓坏死',
                'description': '牙髓失去活力',
                'condition_field': 'pulp_condition',
                'condition_operator': '=',
                'condition_value': 'necrotic',
                'score': -25,
                'is_mandatory': True,
                'mandatory_failure_message': '牙髓坏死必须先进行根管治疗',
                'risk_level': 'high',
                'treatment_suggestion': 'root_canal'
            },
            # 牙周状况规则
            {
                'category_id': 2,
                'name': '严重骨吸收',
                'description': '牙槽骨吸收超过50%',
                'condition_field': 'bone_loss_percentage',
                'condition_operator': '>',
                'condition_value': '50',
                'score': -30,
                'risk_level': 'high',
                'treatment_suggestion': 'implant'
            },
            {
                'category_id': 2,
                'name': '牙齿松动III度',
                'description': '牙齿严重松动',
                'condition_field': 'mobility_degree',
                'condition_operator': '=',
                'condition_value': '3',
                'score': -25,
                'is_mandatory': True,
                'mandatory_failure_message': '牙齿III度松动建议拔除',
                'risk_level': 'high',
                'treatment_suggestion': 'extraction'
            },
            # 患者因素规则
            {
                'category_id': 4,
                'name': '糖尿病患者',
                'description': '糖尿病影响伤口愈合',
                'condition_field': 'diabetic_status',
                'condition_operator': '=',
                'condition_value': 'true',
                'score': -15,
                'risk_level': 'medium',
                'treatment_suggestion': 'observation'
            },
            {
                'category_id': 4,
                'name': '吸烟者',
                'description': '吸烟影响牙周健康和种植体成功率',
                'condition_field': 'smoking_status',
                'condition_operator': '=',
                'condition_value': 'smoker',
                'score': -10,
                'risk_level': 'medium',
                'treatment_suggestion': 'observation'
            },
            # 正面规则
            {
                'category_id': 1,
                'name': '浅表龋齿',
                'description': '仅限釉质层的浅表龋齿',
                'condition_field': 'caries_degree',
                'condition_operator': '=',
                'condition_value': 'superficial',
                'score': 5,
                'risk_level': 'low',
                'treatment_suggestion': 'filling'
            },
            {
                'category_id': 2,
                'name': '牙周健康',
                'description': '牙周组织健康无炎症',
                'condition_field': 'periodontal_status',
                'condition_operator': '=',
                'condition_value': 'healthy',
                'score': 15,
                'risk_level': 'low',
                'treatment_suggestion': 'full_crown'
            }
        ]

        for rule_data in rules:
            # 检查是否已存在类似规则
            existing = Rule.query.filter_by(
                name=rule_data['name'],
                category_id=rule_data['category_id']
            ).first()
            if not existing:
                rule = Rule(**rule_data)
                db.session.add(rule)

        db.session.commit()
        print("数据库初始化完成！")

    except Exception as e:
        db.session.rollback()
        print(f"数据库初始化失败: {str(e)}")
        raise


def db_session():
    """获取数据库会话"""
    return db.session


# 添加一些常用的数据库操作函数
def get_or_create(model, **kwargs):
    """获取或创建记录"""
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance, True


def add_record(model, **kwargs):
    """添加记录"""
    try:
        instance = model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance, True
    except Exception as e:
        db.session.rollback()
        return None, str(e)


def update_record(instance, **kwargs):
    """更新记录"""
    try:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, str(e)


def delete_record(instance):
    """删除记录"""
    try:
        db.session.delete(instance)
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, str(e)
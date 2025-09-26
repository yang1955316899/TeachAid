"""
智能教学系统测试用例
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.intelligent_tutor_service import (
    IntelligentTutorService,
    DifficultyLevel,
    TeachingPhase,
    StudentResponse
)


class TestIntelligentTutorService:
    """智能教学服务测试"""

    @pytest.fixture
    def tutor_service(self):
        """创建教学服务实例"""
        service = IntelligentTutorService()
        # Mock Qwen API客户端
        service.qwen_client.chat_completion = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_start_learning_session(self, tutor_service):
        """测试开始学习会话"""
        # Mock API响应
        tutor_service.qwen_client.chat_completion.return_value = "你好！我们今天要学习二次函数，你对这个话题了解多少呢？"

        result = await tutor_service.start_learning_session(
            user_id="test_user_123",
            subject="数学",
            topic="二次函数",
            difficulty=DifficultyLevel.INTERMEDIATE,
            learning_objectives=["理解二次函数的基本概念", "掌握顶点式和一般式的转换"]
        )

        assert "session_id" in result
        assert result["subject"] == "数学"
        assert result["topic"] == "二次函数"
        assert "initial_question" in result
        assert len(result["initial_question"]) > 0

    @pytest.mark.asyncio
    async def test_process_student_input_correct_answer(self, tutor_service):
        """测试处理学生正确回答"""
        # Mock评估API响应
        tutor_service.qwen_client.chat_completion.side_effect = [
            '{"response_type": "correct", "understanding": 0.8, "confused": false, "help_needed": "question"}',
            "很好！你理解得很准确。那么你能告诉我二次函数的顶点坐标公式是什么吗？"
        ]

        context = {
            "user_id": "test_user_123",
            "subject": "数学",
            "topic": "二次函数"
        }

        result = await tutor_service.process_student_input(
            session_id="test_session_123",
            student_input="二次函数是形如y=ax²+bx+c的函数",
            context=context
        )

        assert result["success"] is True
        assert result["understanding_level"] == 0.8
        assert "ai_response" in result
        assert len(result["ai_response"]) > 0

    @pytest.mark.asyncio
    async def test_process_student_input_confused(self, tutor_service):
        """测试处理学生困惑回答"""
        # Mock评估API响应
        tutor_service.qwen_client.chat_completion.side_effect = [
            '{"response_type": "confused", "understanding": 0.3, "confused": true, "help_needed": "explain"}',
            "我理解你的困惑，让我们重新开始。二次函数其实就像一个抛物线..."
        ]

        context = {
            "user_id": "test_user_123",
            "subject": "数学",
            "topic": "二次函数"
        }

        result = await tutor_service.process_student_input(
            session_id="test_session_123",
            student_input="我不太明白什么是二次函数",
            context=context
        )

        assert result["success"] is True
        assert result["understanding_level"] == 0.3
        assert "重新开始" in result["ai_response"] or "困惑" in result["ai_response"]

    @pytest.mark.asyncio
    async def test_generate_initial_assessment(self, tutor_service):
        """测试生成初始评估问题"""
        from app.services.intelligent_tutor_service import TutorState

        tutor_service.qwen_client.chat_completion.return_value = "你对二次函数有什么了解吗？"

        state = TutorState(
            subject="数学",
            topic="二次函数",
            difficulty=DifficultyLevel.INTERMEDIATE,
            learning_objectives=["理解基本概念"]
        )

        question = await tutor_service._generate_initial_assessment(state)

        assert len(question) > 0
        assert "二次函数" in question

    def test_route_teaching_strategy(self, tutor_service):
        """测试教学策略路由"""
        # 测试完全理解且正确的情况
        state = {
            "understanding_level": 0.9,
            "student_response_type": StudentResponse.CORRECT,
            "question_attempts": 1,
            "max_attempts": 3
        }
        result = tutor_service._route_teaching_strategy(state)
        assert result == "complete"

        # 测试困惑的情况
        state = {
            "understanding_level": 0.4,
            "student_response_type": StudentResponse.CONFUSED,
            "question_attempts": 1,
            "max_attempts": 3
        }
        result = tutor_service._route_teaching_strategy(state)
        assert result == "confused"

        # 测试需要鼓励的情况
        state = {
            "understanding_level": 0.2,
            "student_response_type": StudentResponse.INCORRECT,
            "question_attempts": 1,
            "max_attempts": 3
        }
        result = tutor_service._route_teaching_strategy(state)
        assert result == "encourage"


class TestTutorContextService:
    """上下文管理服务测试"""

    @pytest.fixture
    def context_service(self):
        """创建上下文服务实例"""
        from app.services.tutor_context_service import TutorContextService
        return TutorContextService()

    @pytest.mark.asyncio
    async def test_session_lifecycle(self, context_service):
        """测试会话生命周期"""
        # 这个测试需要数据库连接，在实际环境中运行
        pass


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_complete_learning_flow(self):
        """测试完整的学习流程"""
        # 模拟完整的学习对话流程
        tutor = IntelligentTutorService()

        # Mock API调用
        tutor.qwen_client.chat_completion = AsyncMock()

        # 1. 开始会话
        tutor.qwen_client.chat_completion.return_value = "让我们开始学习二次函数！你觉得什么是函数？"

        session_result = await tutor.start_learning_session(
            user_id="integration_test_user",
            subject="数学",
            topic="二次函数",
            difficulty=DifficultyLevel.INTERMEDIATE
        )

        assert "session_id" in session_result

        # 2. 模拟学生回答序列
        conversation_flow = [
            {
                "student_input": "函数就是一个式子吧",
                "mock_assessment": '{"response_type": "partial", "understanding": 0.4, "confused": false, "help_needed": "hint"}',
                "mock_response": "你的理解有一定道理，但可以更精确一些。函数其实是表示两个变量之间关系的规则..."
            },
            {
                "student_input": "哦，我明白了，就是x和y之间的关系",
                "mock_assessment": '{"response_type": "correct", "understanding": 0.7, "confused": false, "help_needed": "question"}',
                "mock_response": "很好！那么二次函数有什么特点呢？"
            },
            {
                "student_input": "二次函数有x的平方项",
                "mock_assessment": '{"response_type": "correct", "understanding": 0.85, "confused": false, "help_needed": "question"}',
                "mock_response": "完全正确！你已经很好地理解了二次函数的基本概念。"
            }
        ]

        session_id = session_result["session_id"]
        context = {
            "user_id": "integration_test_user",
            "subject": "数学",
            "topic": "二次函数"
        }

        for step in conversation_flow:
            # Mock API响应
            tutor.qwen_client.chat_completion.side_effect = [
                step["mock_assessment"],
                step["mock_response"]
            ]

            result = await tutor.process_student_input(
                session_id=session_id,
                student_input=step["student_input"],
                context=context
            )

            assert result["success"] is True
            assert len(result["ai_response"]) > 0

        print("集成测试完成：完整学习流程运行正常")


# 性能测试
class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self):
        """测试并发会话处理"""
        tutor = IntelligentTutorService()
        tutor.qwen_client.chat_completion = AsyncMock(return_value="测试回复")

        # 模拟10个并发会话
        tasks = []
        for i in range(10):
            task = tutor.start_learning_session(
                user_id=f"concurrent_user_{i}",
                subject="数学",
                topic="二次函数"
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # 验证所有会话都成功创建
        assert len(results) == 10
        for result in results:
            assert "session_id" in result
            assert "initial_question" in result

        print("并发测试完成：10个并发会话成功处理")


# 边界条件测试
class TestEdgeCases:
    """边界条件测试"""

    @pytest.mark.asyncio
    async def test_empty_student_input(self):
        """测试空输入处理"""
        tutor = IntelligentTutorService()

        # 测试空字符串输入
        result = await tutor.process_student_input(
            session_id="test_session",
            student_input="",
            context={"subject": "数学", "topic": "二次函数"}
        )

        # 应该有适当的错误处理或默认响应
        assert "success" in result

    @pytest.mark.asyncio
    async def test_very_long_input(self):
        """测试超长输入处理"""
        tutor = IntelligentTutorService()
        tutor.qwen_client.chat_completion = AsyncMock(return_value="我理解了你的详细回答")

        # 生成一个很长的输入
        long_input = "我觉得二次函数" + "很有趣" * 1000

        result = await tutor.process_student_input(
            session_id="test_session",
            student_input=long_input,
            context={"subject": "数学", "topic": "二次函数"}
        )

        # 应该能够处理长输入
        assert "success" in result

    @pytest.mark.asyncio
    async def test_api_failure_handling(self):
        """测试API失败处理"""
        tutor = IntelligentTutorService()

        # Mock API失败
        tutor.qwen_client.chat_completion = AsyncMock(side_effect=Exception("API调用失败"))

        result = await tutor.process_student_input(
            session_id="test_session",
            student_input="什么是二次函数？",
            context={"subject": "数学", "topic": "二次函数"}
        )

        # 应该有合适的错误处理
        assert result["success"] is False
        assert "error_message" in result


if __name__ == "__main__":
    # 运行集成测试
    async def run_integration_test():
        test = TestIntegration()
        await test.test_complete_learning_flow()

        performance_test = TestPerformance()
        await performance_test.test_concurrent_sessions()

        edge_test = TestEdgeCases()
        await edge_test.test_empty_student_input()
        await edge_test.test_api_failure_handling()

        print("所有测试完成！")

    # 运行测试
    asyncio.run(run_integration_test())
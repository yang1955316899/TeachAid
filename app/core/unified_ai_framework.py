"""
统一AI框架 - 整合LiteLLM和LangGraph
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from enum import Enum

import litellm
from litellm import completion, acompletion
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel
from loguru import logger

from app.core.config import settings


class ModelTier(str, Enum):
    """模型层级"""
    PRIMARY = "primary"
    FALLBACK = "fallback"
    BUDGET = "budget"


class TaskComplexity(str, Enum):
    """任务复杂度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProcessingState(BaseModel):
    """工作流状态"""
    input_data: Dict[str, Any] = {}
    extracted_content: Optional[str] = None
    rewritten_answer: Optional[str] = None
    model_used: Optional[str] = None
    quality_score: Optional[int] = None
    cost: float = 0.0
    processing_time: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    start_time: float = time.time()


class UnifiedAIFramework:
    """统一AI框架"""
    
    def __init__(self):
        self.model_config = {
            "primary": {
                "vision": "gpt-4o",
                "chat": "gpt-4o-mini", 
                "rewrite": "claude-3-5-sonnet-20241022"
            },
            "fallback": {
                "vision": "qwen-vl-max",
                "chat": "deepseek-chat",
                "rewrite": "yi-large"
            },
            "budget": {
                "vision": "qwen-vl-plus",
                "chat": "qwen-turbo", 
                "rewrite": "moonshot-v1-8k"
            }
        }
        
        # 配置LiteLLM
        self._setup_litellm()
        
        # 构建工作流
        self.processing_workflow = self._build_processing_workflow()
        
    def _setup_litellm(self):
        """配置LiteLLM"""
        # 设置日志级别
        litellm.set_verbose = settings.debug
        
        # 配置API密钥
        litellm.api_key = settings.ai.openai_api_key
        litellm.anthropic_api_key = settings.ai.anthropic_api_key
        
        # 启用缓存
        litellm.cache = litellm.Cache()
        
        # 成本追踪
        if settings.cost_control.cost_tracking_enabled:
            litellm.success_callback = ["langfuse"]
            
    def _build_processing_workflow(self) -> StateGraph:
        """构建处理工作流"""
        workflow = StateGraph(ProcessingState)
        
        # 添加节点
        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("extract_content", self._extract_content)
        workflow.add_node("rewrite_answer", self._rewrite_answer)
        workflow.add_node("assess_quality", self._assess_quality)
        workflow.add_node("handle_error", self._handle_error)
        
        # 设置流程
        workflow.set_entry_point("validate_input")
        
        # 条件边
        workflow.add_conditional_edges(
            "validate_input",
            self._should_continue,
            {
                "continue": "extract_content",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "extract_content", 
            self._should_retry,
            {
                "continue": "rewrite_answer",
                "retry": "extract_content",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "rewrite_answer",
            self._should_optimize,
            {
                "assess": "assess_quality",
                "complete": END,
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("assess_quality", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile(checkpointer=MemorySaver())
        
    async def process_question(self, 
                             question: str,
                             original_answer: str,
                             subject: str = "通用",
                             question_type: str = "解答题",
                             complexity: TaskComplexity = TaskComplexity.MEDIUM) -> Dict[str, Any]:
        """处理题目 - 主入口"""
        
        initial_state = ProcessingState(
            input_data={
                "question": question,
                "original_answer": original_answer,
                "subject": subject,
                "question_type": question_type,
                "complexity": complexity
            }
        )
        
        try:
            result = await self.processing_workflow.ainvoke(
                initial_state.dict(),
                config={"configurable": {"thread_id": "default"}}
            )
            
            return {
                "success": True,
                "extracted_content": result.get("extracted_content"),
                "rewritten_answer": result.get("rewritten_answer"),
                "model_used": result.get("model_used"),
                "quality_score": result.get("quality_score", 0),
                "processing_time": result.get("processing_time", 0),
                "cost": result.get("cost", 0.0),
                "error_message": result.get("error_message")
            }
            
        except Exception as e:
            logger.error(f"处理题目失败: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "cost": 0.0,
                "processing_time": time.time() - initial_state.start_time
            }
    
    async def _validate_input(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """验证输入"""
        input_data = state.get("input_data", {})
        
        if not input_data.get("question") or not input_data.get("original_answer"):
            state["error_message"] = "题目或答案内容不能为空"
            return state
            
        logger.info(f"验证输入成功: {input_data.get('subject', '未知学科')}")
        return state
    
    async def _extract_content(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """提取内容（多模态AI处理）"""
        input_data = state.get("input_data", {})
        complexity = input_data.get("complexity", TaskComplexity.MEDIUM)
        
        # 选择模型
        model = self._select_model("vision", complexity)
        
        # 构建提示词
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的教学内容分析专家。请分析题目内容，提取关键信息。"
            },
            {
                "role": "user", 
                "content": f"""
                请分析以下题目：
                
                题目：{input_data.get('question', '')}
                答案：{input_data.get('original_answer', '')}
                学科：{input_data.get('subject', '通用')}
                
                请提取：
                1. 题目类型和难度
                2. 知识点
                3. 解题步骤
                4. 易错点
                
                以JSON格式返回结果。
                """
            }
        ]
        
        try:
            response = await acompletion(
                model=model,
                messages=messages,
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            state["extracted_content"] = content
            state["model_used"] = model
            state["cost"] += self._calculate_cost(response)
            
            logger.info(f"内容提取成功，使用模型: {model}")
            
        except Exception as e:
            state["error_message"] = f"内容提取失败: {e}"
            state["retry_count"] = state.get("retry_count", 0) + 1
            logger.error(f"内容提取失败: {e}")
            
        return state
    
    async def _rewrite_answer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """改写答案"""
        input_data = state.get("input_data", {})
        subject = input_data.get("subject", "通用")
        
        # 选择最佳改写模型
        model = self._select_rewrite_model(subject)
        
        # 构建改写提示词
        messages = [
            {
                "role": "system",
                "content": self._get_rewrite_system_prompt(subject)
            },
            {
                "role": "user",
                "content": f"""
                原题目：{input_data.get('question', '')}
                原答案：{input_data.get('original_answer', '')}
                学科：{subject}
                
                请将答案改写为引导式教学内容。
                """
            }
        ]
        
        try:
            response = await acompletion(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                stream=False
            )
            
            rewritten = response.choices[0].message.content
            state["rewritten_answer"] = rewritten
            state["cost"] += self._calculate_cost(response)
            
            logger.info(f"答案改写成功，使用模型: {model}")
            
        except Exception as e:
            state["error_message"] = f"答案改写失败: {e}"
            logger.error(f"答案改写失败: {e}")
            
        return state
    
    async def _assess_quality(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """评估质量"""
        input_data = state.get("input_data", {})
        
        assessment_prompt = f"""
        评估以下答案改写的质量（1-10分）：
        
        原始答案：{input_data.get('original_answer', '')}
        改写答案：{state.get('rewritten_answer', '')}
        
        评估维度：
        1. 教学启发性
        2. 内容准确性
        3. 语言适合度
        4. 结构清晰度
        
        只返回分数（整数）。
        """
        
        try:
            response = await acompletion(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": assessment_prompt}],
                temperature=0.3,
                max_tokens=10
            )
            
            score_text = response.choices[0].message.content.strip()
            score = int(''.join(filter(str.isdigit, score_text))[:2] or 0)
            
            state["quality_score"] = min(max(score, 1), 10)
            state["cost"] += self._calculate_cost(response)
            
        except Exception as e:
            logger.warning(f"质量评估失败: {e}")
            state["quality_score"] = 5  # 默认中等质量
            
        return state
    
    async def _handle_error(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理错误"""
        error_msg = state.get("error_message", "未知错误")
        logger.error(f"工作流错误: {error_msg}")
        
        state["processing_time"] = time.time() - state.get("start_time", time.time())
        return state
    
    def _should_continue(self, state: Dict[str, Any]) -> str:
        """判断是否继续"""
        return "error" if state.get("error_message") else "continue"
    
    def _should_retry(self, state: Dict[str, Any]) -> str:
        """判断是否重试"""
        if state.get("error_message"):
            retry_count = state.get("retry_count", 0)
            return "retry" if retry_count < 3 else "error"
        return "continue"
    
    def _should_optimize(self, state: Dict[str, Any]) -> str:
        """判断是否需要优化"""
        if state.get("error_message"):
            return "error"
        return "assess" if state.get("rewritten_answer") else "complete"
    
    def _select_model(self, task_type: str, complexity: TaskComplexity) -> str:
        """智能选择模型"""
        if complexity == TaskComplexity.HIGH:
            tier = "primary"
        elif complexity == TaskComplexity.MEDIUM:
            tier = "primary"
        else:
            tier = "budget"
            
        return self.model_config[tier].get(task_type, "gpt-4o-mini")
    
    def _select_rewrite_model(self, subject: str) -> str:
        """根据学科选择改写模型"""
        if subject in ["数学", "物理", "化学"]:
            return "claude-3-5-sonnet-20241022"  # Claude逻辑推理强
        elif subject in ["语文", "历史", "政治"]:
            return "yi-large"  # 中文理解优秀
        elif subject == "英语":
            return "gpt-4o"  # 英语原生优势
        else:
            return "deepseek-chat"  # 平衡性价比
    
    def _get_rewrite_system_prompt(self, subject: str) -> str:
        """获取改写系统提示词"""
        base_prompt = """你是一位资深教师，擅长将标准答案转换为引导式教学内容。

改写原则：
1. 保留原答案的正确性和完整性
2. 将直接答案转换为引导式问题
3. 增加思路解析和方法总结
4. 突出易错点和注意事项
5. 适当添加变式练习建议

改写风格：
- 语言亲切，符合学生认知水平
- 逻辑清晰，步骤分明
- 富有启发性，避免直接给出答案"""

        if subject == "数学":
            base_prompt += "\n\n数学学科特点：注重解题思路和方法，强调数学思维的培养。"
        elif subject in ["语文", "历史"]:
            base_prompt += "\n\n文科特点：注重理解和分析，培养批判性思维。"
            
        return base_prompt
    
    def _calculate_cost(self, response) -> float:
        """计算成本"""
        try:
            return litellm.completion_cost(completion_response=response) or 0.0
        except:
            return 0.0
    
    async def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return list(set([
            model for config in self.model_config.values()
            for model in config.values()
        ]))
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = await acompletion(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            return {
                "status": "healthy",
                "models_available": await self.get_available_models(),
                "test_response_time": 0.5  # 模拟
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e)
            }


# 全局实例
unified_ai = UnifiedAIFramework()
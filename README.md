# TeachAid - AI辅助教学平台

## 一、项目概述

TeachAid是一个基于大语言模型的AI辅助教学平台，旨在提升教培机构教学效率。平台通过多模态AI技术，将传统题目答案转换为更适合教学的引导式内容，并为学生提供智能化的学习互动体验。

### 核心价值
- **教师端**：智能化题目处理，提升备课效率
- **学生端**：个性化学习引导，增强理解效果
- **机构端**：数据化教学管理，优化教学质量

## 二、技术架构

### 技术栈选型
```
后端：FastAPI + Python 3.11+
前端：Vue 3.5+ + Vben Admin 5.0 + JavaScript + Ant Design Vue
构建工具：Vite 5.0+ + Pnpm Monorepo + TurboRepo
AI框架：LangGraph (工作流编排) + LiteLLM (多模型统一接口)
数据库：MySQL 8.0+ (主库) + Redis 7+ (缓存)
多模态AI：GPT-4V / Claude-3 / 通义千问VL / Yi-Vision
监控调试：LangSmith (AI应用可观测性)
代码规范：ESLint + Prettier + Stylelint
部署：Docker + Nginx
项目结构：前后端一体化目录结构
```

### 架构特点
- **智能工作流编排**：LangGraph处理复杂多步骤教学流程，支持状态管理和人机交互
- **统一多模型接口**：LiteLLM提供100+ LLM统一调用，支持自动fallback和成本优化
- **多模态理解**：使用视觉大模型替代传统OCR，准确理解复杂图表公式
- **智能模型路由**：根据任务复杂度、成本预算、性能表现自动选择最优模型
- **故障容错机制**：模型故障时自动切换备用模型，保证服务稳定性
- **实时监控调试**：集成LangSmith，提供完整的AI应用可观测性
- **企业级前端架构**：基于Vben Admin 5.0，提供完善的权限管理、主题切换、国际化支持
- **现代化工程体系**：JavaScript轻量开发，Monorepo架构，完善的代码规范

## 三、核心功能设计

### 3.1 多模态题目导入系统

#### 功能描述
支持多种格式的教学材料导入，通过多模态AI进行智能解析和结构化处理。

#### 支持格式
- **图片格式**：JPG, PNG, WEBP (单张/批量上传)
- **文档格式**：PDF (多页自动分割)
- **文本格式**：直接粘贴或TXT文件上传

#### 技术实现方案

##### 统一多模态处理框架
```python
# app/core/unified_ai_framework.py
import litellm
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

class UnifiedAIFramework:
    def __init__(self):
        # LiteLLM模型配置 - 支持智能切换
        self.model_config = {
            "primary": {
                "vision": "gpt-4o",  # 主力视觉模型
                "chat": "gpt-4o-mini",  # 对话模型
                "rewrite": "claude-3-5-sonnet-20241022"  # 改写模型
            },
            "fallback": {
                "vision": "qwen-vl-max",
                "chat": "deepseek-chat", 
                "rewrite": "yi-large"
            },
            "budget": {
                "vision": "qwen-vl-plus",  # 成本优化
                "chat": "qwen-turbo",
                "rewrite": "moonshot-v1-8k"
            }
        }
        
        # LangGraph工作流
        self.question_workflow = self._build_question_processing_workflow()
        
    async def extract_qa_content(self, file_path: str, complexity: str = "medium") -> dict:
        """智能多模态内容提取"""
        
        # 根据复杂度智能选择模型
        model_tier = self._select_model_tier(complexity)
        model = self.model_config[model_tier]["vision"]
        
        extraction_prompt = self._build_extraction_messages(file_path)
        
        try:
            # LiteLLM统一调用多家模型
            response = await litellm.acompletion(
                model=model,
                messages=extraction_prompt,
                temperature=0.1,
                max_tokens=2000
            )
            
            return {
                "extracted_content": response.choices[0].message.content,
                "model_used": model,
                "cost": response.usage.total_tokens * self._get_model_cost(model)
            }
            
        except Exception as e:
            # 自动fallback到备用模型
            return await self._fallback_extraction(file_path, str(e))
    
    def _build_question_processing_workflow(self) -> StateGraph:
        """构建题目处理工作流 - LangGraph"""
        
        workflow = StateGraph(QuestionProcessingState)
        
        # 添加处理节点
        workflow.add_node("extract_content", self.extract_with_litellm)
        workflow.add_node("validate_extraction", self.validate_content)
        workflow.add_node("rewrite_answer", self.rewrite_with_best_model)
        workflow.add_node("quality_assessment", self.assess_quality)
        workflow.add_node("save_result", self.save_to_database)
        workflow.add_node("handle_error", self.handle_error)
        
        # 智能条件路由
        workflow.add_conditional_edges(
            "extract_content",
            self.should_continue_processing,
            {
                "continue": "validate_extraction",
                "retry": "extract_content",
                "error": "handle_error"
            }
        )
        
        # 设置检查点 - 支持长时间运行和故障恢复
        return workflow.compile(checkpointer=PostgresSaver())
    
    async def rewrite_with_best_model(self, state: dict) -> dict:
        """智能模型选择改写答案"""
        
        # 根据学科和题型选择最优模型
        best_model = self._select_rewrite_model(
            state["subject"], 
            state["question_type"]
        )
        
        response = await litellm.acompletion(
            model=best_model,
            messages=self._build_rewrite_prompt(state),
            temperature=0.7,
            stream=True  # 支持流式响应
        )
        
        return {
            **state,
            "rewritten_answer": response.choices[0].message.content,
            "model_used": best_model,
            "processing_time": time.time() - state["start_time"]
        }
```

##### 文件预处理流程
```python
# app/services/file_processor.py
class FileProcessorService:
    async def preprocess_upload(self, file: UploadFile) -> List[str]:
        """文件预处理和分割"""
        
        # 保存上传文件
        file_path = await self._save_upload_file(file)
        
        if file.filename.endswith('.pdf'):
            # PDF分页处理
            pages = await self._split_pdf_pages(file_path)
            return [await self._pdf_page_to_image(page) for page in pages]
        else:
            # 图片处理（压缩、格式转换）
            processed_path = await self._process_image(file_path)
            return [processed_path]
    
    async def _split_pdf_pages(self, pdf_path: str) -> List[str]:
        """PDF按页分割"""
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        pages = []
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            # 转换为高分辨率图片
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_path = f"/tmp/page_{page_num}.png"
            pix.save(img_path)
            pages.append(img_path)
            
        doc.close()
        return pages
```

### 3.2 智能提示词管理系统

#### 功能描述
支持提示词模板的创建、编辑、测试和版本管理，为不同学科和题型提供专业的改写策略。

#### 核心特性
- **分层提示词**：系统级 → 学科级 → 题型级
- **版本控制**：支持提示词迭代和回滚
- **效果测试**：在线预览改写效果
- **智能缓存**：基于语义相似度的缓存机制

#### 技术实现方案

##### 提示词模板系统
```python
# app/services/prompt_template_service.py
class PromptTemplateService:
    def __init__(self):
        self.cache_service = PromptCacheService()
        self.templates = {}
    
    async def create_template(self, template_data: dict) -> PromptTemplate:
        """创建提示词模板"""
        
        template = PromptTemplate(
            id=template_data["id"],
            name=template_data["name"],
            category=template_data["category"],  # system/subject/type
            level=template_data["level"],        # 优先级
            system_prompt=template_data["system_prompt"],
            user_prompt_template=template_data["user_prompt_template"],
            variables=template_data["variables"],
            examples=template_data.get("examples", []),
            version=1
        )
        
        await self.db.save(template)
        return template
    
    async def render_prompt(self, template_id: str, **variables) -> List[BaseMessage]:
        """渲染提示词模板"""
        
        template = await self.get_template(template_id)
        
        # 构建系统提示
        system_prompt = template.system_prompt
        
        # 渲染用户提示
        user_prompt = template.user_prompt_template.format(**variables)
        
        # 添加少样本示例
        messages = [{"role": "system", "content": system_prompt}]
        
        for example in template.examples:
            messages.extend([
                {"role": "user", "content": example["input"]},
                {"role": "assistant", "content": example["output"]}
            ])
        
        messages.append({"role": "user", "content": user_prompt})
        
        return messages

# 内置提示词模板
BUILTIN_TEMPLATES = {
    "math_calculation": {
        "name": "数学计算题改写",
        "system_prompt": """你是一位资深数学教师，擅长将复杂的数学解答转换为启发式的教学内容。

改写原则：
1. 保留原答案的正确性和完整性
2. 将直接的计算步骤转换为引导式问题
3. 增加思路解析和方法总结
4. 突出易错点和注意事项
5. 适当添加变式练习建议

改写风格：
- 语言亲切，符合学生认知水平
- 逻辑清晰，步骤分明
- 富有启发性，避免直接给出答案
""",
        "user_prompt_template": """
原题目：{question}
原答案：{answer}
学生水平：{grade_level}

请将上述答案改写为更适合教学的版本。
""",
        "variables": ["question", "answer", "grade_level"]
    }
}
```

##### 智能缓存和成本控制
```python
# app/services/intelligent_cache_service.py
import litellm
from litellm import BudgetManager

class IntelligentCacheService:
    def __init__(self):
        # LiteLLM内置缓存
        litellm.cache = litellm.Cache()
        
        # 成本管理
        self.budget_manager = BudgetManager(
            project_name="TeachAid",
            budget_limit=1000.0  # 月预算限制
        )
        
        # Redis语义缓存
        self.semantic_cache = RedisSemanticCache(
            redis_url="redis://localhost:6379",
            embedding=OpenAIEmbeddings(),
            score_threshold=0.85
        )
    
    async def cached_completion(self, 
                              messages: List[dict], 
                              model: str,
                              **kwargs) -> str:
        """带缓存的LLM调用"""
        
        # 检查预算
        if self.budget_manager.get_current_cost() > self.budget_manager.budget_limit * 0.9:
            # 预算不足时自动切换到经济模型
            model = self._get_budget_model(model)
        
        # LiteLLM自动处理缓存
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            cache={
                "use_cache": True,
                "cache_params": {
                    "similarity_threshold": 0.8,
                    "ttl": 3600
                }
            },
            **kwargs
        )
        
        # 记录成本
        cost = litellm.completion_cost(completion_response=response)
        await self.budget_manager.track_cost(model, cost)
        
        return response.choices[0].message.content
    
    def _get_budget_model(self, original_model: str) -> str:
        """获取经济替代模型"""
        budget_alternatives = {
            "gpt-4o": "gpt-4o-mini",
            "claude-3-5-sonnet-20241022": "claude-3-haiku-20240307",
            "gpt-4-vision-preview": "qwen-vl-plus"
        }
        return budget_alternatives.get(original_model, "qwen-turbo")
```

### 3.3 AI答案改写引擎

#### 功能描述
基于大语言模型的答案改写系统，将标准答案转换为引导式教学内容。

#### 改写策略
- **启发式引导**：用问题代替直接答案
- **分步骤讲解**：复杂问题拆解为简单步骤  
- **思维过程展示**：展现解题思路和方法
- **易错点提醒**：预防常见错误
- **扩展练习**：提供相关变式题目

#### 技术实现方案

```python
# app/services/intelligent_rewriting_service.py
class IntelligentRewritingService:
    def __init__(self):
        self.ai_framework = UnifiedAIFramework()
        self.template_service = PromptTemplateService()
        self.cache_service = IntelligentCacheService()
        
        # LangGraph改写工作流
        self.rewrite_workflow = self._build_rewrite_workflow()
    
    def _build_rewrite_workflow(self) -> StateGraph:
        """构建智能改写工作流"""
        workflow = StateGraph(RewriteState)
        
        workflow.add_node("analyze_content", self.analyze_question_complexity)
        workflow.add_node("select_strategy", self.select_rewrite_strategy)
        workflow.add_node("generate_rewrite", self.generate_with_best_model)
        workflow.add_node("quality_check", self.assess_quality_score)
        workflow.add_node("optimize_result", self.optimize_teaching_effect)
        
        # 智能路由：根据质量分数决定是否需要优化
        workflow.add_conditional_edges(
            "quality_check",
            self.should_optimize,
            {
                "optimize": "optimize_result",
                "accept": END,
                "retry": "select_strategy"
            }
        )
        
        return workflow.compile()
    
    async def rewrite_answer(self, 
                           question: str,
                           original_answer: str,
                           subject: str = "通用",
                           question_type: str = "解答题",
                           grade_level: str = "初中") -> dict:
        """智能答案改写 - 多模型协同"""
        
        # 启动LangGraph工作流
        initial_state = {
            "question": question,
            "original_answer": original_answer,
            "subject": subject,
            "question_type": question_type,
            "grade_level": grade_level,
            "complexity": "unknown",
            "quality_score": 0
        }
        
        result = await self.rewrite_workflow.ainvoke(initial_state)
        
        return result
    
    async def generate_with_best_model(self, state: dict) -> dict:
        """使用最佳模型生成改写"""
        
        # 智能模型选择策略
        best_model = self._select_optimal_model(state)
        
        # 构建专业提示词
        messages = await self._build_rewrite_messages(state, best_model)
        
        # 使用LiteLLM调用最优模型
        response = await self.cache_service.cached_completion(
            messages=messages,
            model=best_model,
            temperature=0.7,
            max_tokens=2000
        )
        
        return {
            **state,
            "rewritten_answer": response,
            "model_used": best_model,
            "tokens_used": len(response.split()) * 1.3  # 估算
        }
    
    def _select_optimal_model(self, state: dict) -> str:
        """根据题目特征选择最优模型"""
        
        subject = state["subject"]
        complexity = state["complexity"]
        
        # 学科专业化选择
        if subject in ["数学", "物理", "化学"]:
            if complexity == "high":
                return "claude-3-5-sonnet-20241022"  # Claude逻辑推理强
            else:
                return "gpt-4o-mini"  # 性价比选择
                
        elif subject in ["语文", "历史", "政治"]:
            return "yi-large"  # 中文理解优秀
            
        elif subject == "英语":
            return "gpt-4o"  # 英语原生优势
            
        else:
            # 通用场景
            return "deepseek-chat"  # 平衡性价比
    
    async def assess_quality_score(self, state: dict) -> dict:
        """AI质量评估"""
        
        assessment_prompt = f"""
        请评估以下答案改写的质量（1-10分）：
        
        原始答案：{state['original_answer']}
        改写答案：{state['rewritten_answer']}
        
        评估维度：
        1. 教学启发性（是否引导思考）
        2. 内容准确性（是否保持正确）
        3. 语言适合度（是否符合学生水平）
        4. 结构清晰度（是否条理分明）
        
        返回JSON格式：{{"score": 8, "feedback": "改写建议"}}
        """
        
        response = await litellm.acompletion(
            model="gpt-4o-mini",  # 使用经济模型评估
            messages=[{"role": "user", "content": assessment_prompt}],
            temperature=0.3
        )
        
        assessment = json.loads(response.choices[0].message.content)
        
        return {
            **state,
            "quality_score": assessment["score"],
            "feedback": assessment["feedback"]
        }
```

### 3.4 用户权限管理系统

#### 功能描述
基于角色的权限控制系统，支持多级组织架构和细粒度权限管理。

#### 用户角色体系
- **超级管理员**：平台全局管理权限
- **机构管理员**：管理机构内的教师和学生
- **教师用户**：管理自己的班级和题目
- **学生用户**：查看作业和与AI对话

#### 技术实现方案

```python
# app/services/auth_service.py
from fastapi_users import FastAPIUsers, BaseUserManager
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import SQLAlchemyUserDatabase

class AuthService:
    def __init__(self):
        self.user_db = SQLAlchemyUserDatabase(UserDB, database, users)
        self.jwt_auth = JWTAuthentication(
            secret=JWT_SECRET,
            lifetime_seconds=3600,
            tokenUrl="auth/login"
        )
    
    async def register_user(self, user_data: UserCreate, role: str = "student") -> User:
        """用户注册"""
        
        # 验证邀请码（To B场景需要邀请注册）
        if not await self._validate_invitation_code(user_data.invitation_code):
            raise HTTPException(status_code=400, detail="Invalid invitation code")
        
        # 创建用户
        user = await self.user_manager.create(
            user_data,
            safe=True,
            request=None
        )
        
        # 分配角色权限
        await self.assign_role(user.id, role)
        
        return user
    
    async def assign_permissions(self, user_id: str, permissions: List[str]):
        """分配用户权限"""
        
        user_permissions = [
            UserPermission(user_id=user_id, permission=perm)
            for perm in permissions
        ]
        
        await self.db.bulk_save_objects(user_permissions)

# 权限装饰器
def require_permission(permission: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not await auth_service.has_permission(current_user.id, permission):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# API使用示例
@router.post("/questions/upload")
@require_permission("question:create")
async def upload_question(
    file: UploadFile,
    current_user: User = Depends(get_current_user)
):
    return await question_service.process_upload(file, current_user.id)
```

### 3.5 智能学习对话系统

#### 功能描述
基于上下文感知的AI对话系统，为学生提供个性化的学习引导和答疑服务。

#### 核心特性
- **上下文理解**：记住当前题目和历史对话
- **引导式教学**：不直接给答案，而是启发思考
- **文本标注支持**：针对选中文本进行精准回答
- **多轮对话记忆**：支持连续深入讨论

#### 技术实现方案

```python
# app/services/intelligent_chat_service.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
import litellm

class IntelligentChatService:
    def __init__(self):
        self.ai_framework = UnifiedAIFramework()
        self.cache_service = IntelligentCacheService()
        
        # LangGraph对话工作流
        self.chat_workflow = self._build_adaptive_chat_workflow()
        
    async def start_chat_session(self, 
                                student_id: str, 
                                question_id: str) -> str:
        """开始对话会话"""
        
        session_id = f"chat_{student_id}_{question_id}_{int(time.time())}"
        
        # 获取题目上下文
        question_data = await self.db.get_question(question_id)
        
        # 初始化对话记忆
        chat_history = RedisChatMessageHistory(
            session_id=session_id,
            url="redis://localhost:6379/0",
            ttl=86400  # 24小时过期
        )
        
        memory = ConversationSummaryBufferMemory(
            llm=ChatOpenAI(model="gpt-3.5-turbo"),
            chat_memory=chat_history,
            max_token_limit=1500,
            return_messages=True
        )
        
        # 保存会话上下文
        await self.context_manager.save_session_context(
            session_id=session_id,
            student_id=student_id,
            question_data=question_data,
            memory=memory
        )
        
        return session_id
    
    async def chat_with_ai(self,
                          session_id: str,
                          user_message: str,
                          selected_text: str = None) -> dict:
        """与AI对话"""
        
        # 获取会话上下文
        context = await self.context_manager.get_session_context(session_id)
        if not context:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # 构建引导式系统提示
        system_prompt = await self._build_guidance_prompt(
            context["question_data"], 
            selected_text
        )
        
        # 构建对话链
        conversation_chain = ConversationChain(
            llm=self.llm_service.get_llm("gpt-4"),
            memory=context["memory"],
            verbose=True
        )
        
        # 处理用户消息
        if selected_text:
            enhanced_message = f"""
我对这部分内容有疑问：「{selected_text}」

我的问题是：{user_message}
"""
        else:
            enhanced_message = user_message
        
        # 生成AI回复
        ai_response = await conversation_chain.apredict(
            input=enhanced_message,
            system_prompt=system_prompt
        )
        
        # 记录对话轮次
        await self._log_chat_interaction(
            session_id=session_id,
            user_message=enhanced_message,
            ai_response=ai_response,
            selected_text=selected_text
        )
        
        return {
            "response": ai_response,
            "session_id": session_id,
            "can_continue": True
        }
    
    async def _build_guidance_prompt(self, question_data: dict, selected_text: str = None) -> str:
        """构建引导式系统提示"""
        
        base_prompt = f"""
你是一位耐心的AI教学助手，正在帮助学生理解以下题目：

题目：{question_data['question']}
学科：{question_data['subject']}
难度：{question_data['difficulty']}

你的教学原则：
1. 不要直接给出答案，而要引导学生自己思考
2. 通过提问帮助学生发现问题的关键点
3. 分步骤引导，从简单到复杂
4. 鼓励学生说出自己的想法
5. 当学生迷茫时，给出适当的提示
6. 语言要亲切自然，符合学生的认知水平

当学生提问时，你要：
- 先了解学生的具体困惑点
- 通过反问确认学生的理解程度
- 给出引导性的提示，而非直接答案
- 鼓励学生尝试解决问题
"""
        
        if selected_text:
            base_prompt += f"""

学生特别对这部分内容有疑问：「{selected_text}」
请重点针对这部分内容进行引导讲解。
"""
        
        return base_prompt

# SSE流式响应支持
@router.post("/chat/{session_id}/stream")
async def stream_chat(
    session_id: str,
    message: ChatMessage,
    current_user: User = Depends(get_current_student)
):
    async def generate_response():
        response_generator = chat_service.stream_chat_response(
            session_id=session_id,
            user_message=message.content,
            selected_text=message.selected_text
        )
        
        async for chunk in response_generator:
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain"
    )
```

### 3.6 作业布置与管理系统

#### 功能描述
教师可以选择题目组建作业，学生接收作业并进行学习互动，系统提供数据统计和学习分析。

#### 核心功能
- **作业创建**：教师选择题目，设置截止时间和学习要求
- **作业分发**：自动推送给指定班级学生
- **学习跟踪**：记录学生的学习轨迹和对话记录
- **数据分析**：生成学习报告和薄弱点分析

#### 技术实现方案

```python
# app/services/homework_service.py
class HomeworkService:
    def __init__(self):
        self.question_service = QuestionService()
        self.chat_service = StudentChatService()
        self.analytics_service = LearningAnalyticsService()
    
    async def create_homework(self,
                            teacher_id: str,
                            homework_data: HomeworkCreate) -> Homework:
        """创建作业"""
        
        # 验证题目权限
        for question_id in homework_data.question_ids:
            if not await self.question_service.can_access(teacher_id, question_id):
                raise HTTPException(status_code=403, detail=f"Cannot access question {question_id}")
        
        # 创建作业
        homework = Homework(
            id=str(uuid.uuid4()),
            title=homework_data.title,
            description=homework_data.description,
            teacher_id=teacher_id,
            class_id=homework_data.class_id,
            question_ids=homework_data.question_ids,
            due_date=homework_data.due_date,
            created_at=datetime.utcnow()
        )
        
        await self.db.save(homework)
        
        # 自动分发给班级学生
        await self._distribute_homework(homework)
        
        return homework
    
    async def _distribute_homework(self, homework: Homework):
        """分发作业给学生"""
        
        students = await self.db.get_class_students(homework.class_id)
        
        student_homeworks = [
            StudentHomework(
                id=str(uuid.uuid4()),
                homework_id=homework.id,
                student_id=student.id,
                status="assigned",
                assigned_at=datetime.utcnow()
            )
            for student in students
        ]
        
        await self.db.bulk_save(student_homeworks)
        
        # 发送通知
        for student in students:
            await self.notification_service.send_homework_notification(
                student_id=student.id,
                homework=homework
            )
    
    async def get_student_homework_progress(self, 
                                         student_id: str, 
                                         homework_id: str) -> dict:
        """获取学生作业进度"""
        
        homework = await self.db.get_homework(homework_id)
        student_homework = await self.db.get_student_homework(student_id, homework_id)
        
        question_progress = []
        
        for question_id in homework.question_ids:
            # 获取对话记录
            chat_sessions = await self.chat_service.get_question_chat_sessions(
                student_id, question_id
            )
            
            progress = {
                "question_id": question_id,
                "chat_sessions": len(chat_sessions),
                "total_messages": sum(session.message_count for session in chat_sessions),
                "last_interaction": max(session.updated_at for session in chat_sessions) if chat_sessions else None,
                "understanding_level": await self._assess_understanding_level(
                    student_id, question_id, chat_sessions
                )
            }
            
            question_progress.append(progress)
        
        return {
            "homework": homework,
            "student_homework": student_homework,
            "question_progress": question_progress,
            "overall_progress": self._calculate_overall_progress(question_progress)
        }

# 学习分析服务
class LearningAnalyticsService:
    async def generate_student_report(self, 
                                    student_id: str, 
                                    time_range: tuple = None) -> dict:
        """生成学生学习报告"""
        
        # 获取学习数据
        chat_data = await self.get_student_chat_data(student_id, time_range)
        homework_data = await self.get_student_homework_data(student_id, time_range)
        
        # 分析学习模式
        learning_patterns = await self._analyze_learning_patterns(chat_data)
        
        # 识别薄弱知识点
        weak_points = await self._identify_weak_knowledge_points(
            student_id, chat_data, homework_data
        )
        
        # 生成建议
        recommendations = await self._generate_learning_recommendations(
            learning_patterns, weak_points
        )
        
        return {
            "student_id": student_id,
            "time_range": time_range,
            "learning_summary": {
                "total_questions": len(set(data["question_id"] for data in chat_data)),
                "total_chat_sessions": len(chat_data),
                "average_session_length": np.mean([data["message_count"] for data in chat_data]),
                "most_active_subject": self._get_most_active_subject(chat_data)
            },
            "learning_patterns": learning_patterns,
            "weak_knowledge_points": weak_points,
            "recommendations": recommendations
        }
```

## 四、数据库设计

### 数据库模型

```python
# app/models/database_models.py
from sqlalchemy import Column, String, DateTime, JSON, Text, Boolean, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    """用户基础信息表"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), nullable=False)  # admin/teacher/student
    organization_id = Column(String, ForeignKey("organizations.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # 关系
    organization = relationship("Organization", back_populates="users")
    created_questions = relationship("Question", back_populates="creator")
    student_homeworks = relationship("StudentHomework", back_populates="student")

class Organization(Base):
    """机构信息表"""
    __tablename__ = "organizations"
    
    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True)  # 机构代码
    settings = Column(JSON)  # 机构配置信息
    created_at = Column(DateTime)
    
    users = relationship("User", back_populates="organization")
    classes = relationship("Class", back_populates="organization")

class Class(Base):
    """班级表"""
    __tablename__ = "classes"
    
    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    grade_level = Column(String(20))  # 年级
    subject = Column(String(50))      # 学科
    teacher_id = Column(String, ForeignKey("users.id"))
    organization_id = Column(String, ForeignKey("organizations.id"))
    created_at = Column(DateTime)
    
    teacher = relationship("User", foreign_keys=[teacher_id])
    organization = relationship("Organization", back_populates="classes")
    homeworks = relationship("Homework", back_populates="class_obj")

class Question(Base):
    """题目表"""
    __tablename__ = "questions"
    
    id = Column(String, primary_key=True)
    title = Column(String(200))
    content = Column(Text, nullable=False)      # 题目内容
    original_answer = Column(Text)              # 原始答案
    rewritten_answer = Column(Text)             # AI改写后的答案
    subject = Column(String(50))                # 学科
    question_type = Column(String(50))          # 题目类型
    difficulty = Column(String(20))             # 难度等级
    knowledge_points = Column(JSON)             # 知识点标签
    
    # AI处理相关
    extraction_model = Column(String(50))       # 提取使用的模型
    rewrite_template_id = Column(String)        # 改写使用的模板
    quality_score = Column(Integer)             # 质量评分 (1-10)
    
    # 元信息
    creator_id = Column(String, ForeignKey("users.id"))
    source_file_path = Column(String(500))      # 原始文件路径
    has_image = Column(Boolean, default=False)
    has_formula = Column(Boolean, default=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    creator = relationship("User", back_populates="created_questions")

class PromptTemplate(Base):
    """提示词模板表"""
    __tablename__ = "prompt_templates"
    
    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50))               # system/subject/type
    subject = Column(String(50))                # 适用学科
    question_type = Column(String(50))          # 适用题型
    
    system_prompt = Column(Text)                # 系统提示词
    user_prompt_template = Column(Text)         # 用户提示词模板
    variables = Column(JSON)                    # 模板变量定义
    examples = Column(JSON)                     # 少样本示例
    
    # 版本控制
    version = Column(Integer, default=1)
    parent_template_id = Column(String)         # 父模板ID（用于版本控制）
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    avg_quality_score = Column(Integer)
    
    creator_id = Column(String, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)

class Homework(Base):
    """作业表"""
    __tablename__ = "homeworks"
    
    id = Column(String, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    teacher_id = Column(String, ForeignKey("users.id"))
    class_id = Column(String, ForeignKey("classes.id"))
    question_ids = Column(JSON)                 # 包含的题目ID列表
    
    due_date = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    teacher = relationship("User", foreign_keys=[teacher_id])
    class_obj = relationship("Class", back_populates="homeworks")
    student_homeworks = relationship("StudentHomework", back_populates="homework")

class StudentHomework(Base):
    """学生作业表"""
    __tablename__ = "student_homeworks"
    
    id = Column(String, primary_key=True)
    homework_id = Column(String, ForeignKey("homeworks.id"))
    student_id = Column(String, ForeignKey("users.id"))
    
    status = Column(String(20), default="assigned")  # assigned/in_progress/completed
    progress = Column(JSON)                          # 每道题的进度信息
    
    assigned_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    homework = relationship("Homework", back_populates="student_homeworks")
    student = relationship("User", back_populates="student_homeworks")

class ChatSession(Base):
    """对话会话表"""
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True)
    student_id = Column(String, ForeignKey("users.id"))
    question_id = Column(String, ForeignKey("questions.id"))
    homework_id = Column(String, ForeignKey("homeworks.id"))
    
    session_data = Column(JSON)                 # 会话元数据
    message_count = Column(Integer, default=0)
    understanding_level = Column(Integer)       # 理解程度评估 (1-5)
    
    started_at = Column(DateTime)
    last_interaction_at = Column(DateTime)

class ChatMessage(Base):
    """对话消息表"""
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"))
    
    role = Column(String(10))                   # user/assistant
    content = Column(Text, nullable=False)
    selected_text = Column(Text)                # 用户选中的文本
    
    # AI响应相关
    model_used = Column(String(50))
    token_count = Column(Integer)
    response_time = Column(Integer)             # 响应时间(ms)
    from_cache = Column(Boolean, default=False)
    
    created_at = Column(DateTime)

class FileUpload(Base):
    """文件上传记录表"""
    __tablename__ = "file_uploads"
    
    id = Column(String, primary_key=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    file_type = Column(String(50))
    
    # 处理状态
    status = Column(String(20), default="uploaded")  # uploaded/processing/completed/failed
    processing_result = Column(JSON)                 # 处理结果
    extracted_questions = Column(JSON)               # 提取的题目列表
    
    uploader_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime)
```

### Redis缓存结构

```python
# Redis数据结构设计

# 1. 提示词精确缓存
# Key: exact:{md5_hash}
# Value: {"response": "...", "timestamp": 1640995200, "hit_count": 5}
# TTL: 86400 (24小时)

# 2. 对话会话缓存  
# Key: chat_session:{session_id}
# Value: {"context": {...}, "memory": {...}}
# TTL: 86400 (24小时)

# 3. 用户权限缓存
# Key: user_permissions:{user_id}
# Value: ["question:create", "homework:assign", ...]
# TTL: 3600 (1小时)

# 4. 文件处理队列
# Key: file_processing_queue
# Type: List
# Value: [{"file_id": "...", "priority": 1}, ...]

# 5. 统计数据缓存
# Key: stats:{date}:{metric}
# Value: 数值
# TTL: 86400 (24小时)
```

## 五、API接口设计

### 5.1 认证授权接口

```python
# app/api/auth.py
@router.post("/auth/register")
async def register(user_data: UserRegister):
    """用户注册"""
    return await auth_service.register_user(user_data)

@router.post("/auth/login")
async def login(credentials: UserLogin):
    """用户登录"""
    return await auth_service.authenticate(credentials)

@router.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    """刷新访问令牌"""
    return await auth_service.refresh_access_token(refresh_token)

@router.get("/auth/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取用户信息"""
    return current_user
```

### 5.2 题目管理接口

```python
# app/api/questions.py
@router.post("/questions/upload")
@require_permission("question:create")
async def upload_file(
    file: UploadFile,
    current_user: User = Depends(get_current_teacher)
):
    """上传并处理题目文件"""
    return await question_service.process_file_upload(file, current_user.id)

@router.get("/questions/upload/{file_id}/status")
async def get_upload_status(file_id: str):
    """获取文件处理状态"""
    return await question_service.get_processing_status(file_id)

@router.get("/questions")
async def list_questions(
    page: int = 1,
    size: int = 20,
    subject: str = None,
    question_type: str = None,
    current_user: User = Depends(get_current_user)
):
    """获取题目列表"""
    return await question_service.get_questions(
        page=page, size=size, subject=subject, question_type=question_type,
        user_id=current_user.id
    )

@router.put("/questions/{question_id}/rewrite")
async def rewrite_answer(
    question_id: str,
    rewrite_config: AnswerRewriteConfig,
    current_user: User = Depends(get_current_teacher)
):
    """重新改写答案"""
    return await answer_service.rewrite_answer(
        question_id=question_id,
        config=rewrite_config,
        teacher_id=current_user.id
    )
```

### 5.3 作业管理接口

```python
# app/api/homework.py
@router.post("/homework")
@require_permission("homework:create")
async def create_homework(
    homework_data: HomeworkCreate,
    current_user: User = Depends(get_current_teacher)
):
    """创建作业"""
    return await homework_service.create_homework(current_user.id, homework_data)

@router.get("/homework")
async def list_homeworks(
    role: str = None,  # teacher/student
    current_user: User = Depends(get_current_user)
):
    """获取作业列表"""
    if current_user.role == "teacher":
        return await homework_service.get_teacher_homeworks(current_user.id)
    else:
        return await homework_service.get_student_homeworks(current_user.id)

@router.get("/homework/{homework_id}/progress")
async def get_homework_progress(
    homework_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取作业进度"""
    if current_user.role == "teacher":
        return await homework_service.get_class_progress(homework_id, current_user.id)
    else:
        return await homework_service.get_student_progress(current_user.id, homework_id)
```

### 5.4 学习对话接口

```python
# app/api/chat.py
@router.post("/chat/sessions")
async def start_chat_session(
    session_data: ChatSessionStart,
    current_user: User = Depends(get_current_student)
):
    """开始对话会话"""
    return await chat_service.start_chat_session(
        student_id=current_user.id,
        question_id=session_data.question_id
    )

@router.post("/chat/{session_id}/messages")
async def send_message(
    session_id: str,
    message: ChatMessageCreate,
    current_user: User = Depends(get_current_student)
):
    """发送对话消息"""
    return await chat_service.chat_with_ai(
        session_id=session_id,
        user_message=message.content,
        selected_text=message.selected_text
    )

@router.get("/chat/{session_id}/messages")
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_student)
):
    """获取对话历史"""
    return await chat_service.get_chat_history(session_id)

@router.post("/chat/{session_id}/stream")
async def stream_chat(
    session_id: str,
    message: ChatMessageCreate,
    current_user: User = Depends(get_current_student)
):
    """流式对话响应"""
    return StreamingResponse(
        chat_service.stream_chat_response(session_id, message),
        media_type="text/plain"
    )
```

## 六、前端页面结构

### 6.1 项目目录结构（基于Vben Admin 5.0）

```
TeachAid/
├── app/                         // FastAPI后端代码
│   ├── core/                   // 核心功能
│   │   ├── unified_ai_framework.py
│   │   ├── config.py
│   │   └── database.py
│   ├── services/               // 业务服务
│   │   ├── file_processor.py
│   │   ├── prompt_template_service.py
│   │   ├── intelligent_cache_service.py
│   │   ├── intelligent_rewriting_service.py
│   │   ├── auth_service.py
│   │   ├── intelligent_chat_service.py
│   │   └── homework_service.py
│   ├── api/                    // API路由
│   │   ├── auth.py
│   │   ├── questions.py
│   │   ├── homework.py
│   │   └── chat.py
│   ├── models/                 // 数据模型
│   │   ├── database_models.py
│   │   └── pydantic_models.py
│   └── main.py                 // FastAPI应用入口
├── web/                        // Vben Admin前端代码
│   ├── src/
│   │   ├── views/             // 页面组件
│   │   │   ├── teacher/       // 教师端页面
│   │   │   │   ├── dashboard/
│   │   │   │   ├── question/  // 题目管理
│   │   │   │   ├── homework/  // 作业管理
│   │   │   │   ├── class/     // 班级管理
│   │   │   │   └── prompt/    // 提示词管理
│   │   │   └── student/       // 学生端页面
│   │   │       ├── dashboard/
│   │   │       ├── homework/
│   │   │       ├── study/     // 学习界面
│   │   │       └── progress/
│   │   ├── components/        // 业务组件
│   │   │   ├── QuestionViewer/
│   │   │   ├── ChatPanel/
│   │   │   ├── FileUpload/
│   │   │   └── AIChat/
│   │   ├── api/              // API接口封装
│   │   │   ├── auth.js
│   │   │   ├── question.js
│   │   │   ├── homework.js
│   │   │   └── chat.js
│   │   ├── stores/           // Pinia状态管理
│   │   │   ├── auth.js
│   │   │   ├── question.js
│   │   │   └── chat.js
│   │   ├── router/           // 路由配置
│   │   │   ├── routes/
│   │   │   └── index.js
│   │   ├── utils/            // 工具函数
│   │   ├── assets/           // 静态资源
│   │   └── main.js           // Vue应用入口
│   ├── public/               // 公共资源
│   ├── package.json          // 前端依赖
│   ├── vite.config.js        // Vite配置
│   └── .env                  // 环境变量
├── uploads/                  // 文件上传目录
├── logs/                     // 日志文件
├── requirements.txt          // Python依赖
├── pnpm-workspace.yaml       // Pnpm Monorepo配置
├── turbo.json                // TurboRepo配置
├── docker-compose.yml        // Docker配置
├── .eslintrc.js             // ESLint配置
├── .prettierrc              // Prettier配置
└── README.md                // 项目文档
```

### 6.2 Vben Admin架构特色

**企业级前端特性：**
- **权限管理**：基于RBAC的细粒度权限控制，支持动态路由
- **主题系统**：多套主题，支持暗黑模式和自定义主题色
- **国际化**：完整的i18n支持，中英文切换
- **响应式布局**：适配PC、平板、手机多端
- **JavaScript**：轻量级开发，快速上手，降低学习成本

**开发体验优化：**
- **Monorepo**：使用Pnpm + TurboRepo管理多包架构
- **代码规范**：ESLint + Prettier + Stylelint自动化代码规范
- **组件封装**：高度可复用的业务组件和基础组件
- **状态管理**：Pinia现代化状态管理，轻量高效
- **构建优化**：Vite极速热更新，构建性能优异

**核心页面模块：**

**教师端：**
- 仪表板：数据概览、快速入口、统计图表
- 题目管理：上传解析、答案改写、模板配置
- 作业管理：创建分发、进度监控、学情分析
- 班级管理：学生管理、权限分配、数据统计
- 系统设置：提示词管理、AI模型配置

**学生端：**
- 学习仪表板：作业列表、学习进度、成绩统计
- 智能学习：题目展示、AI对话、笔记记录
- 学习分析：知识点掌握、薄弱环节、学习建议

### 6.3 核心组件设计（JavaScript版本）

```vue
<!-- web/src/components/QuestionViewer/index.vue -->
<template>
  <div class="question-viewer">
    <div class="question-content" v-html="formattedQuestion"></div>
    <div class="answer-section">
      <h3>教学答案</h3>
      <div 
        class="answer-content"
        @mouseup="handleTextSelection"
        v-html="formattedAnswer">
      </div>
      <el-button 
        v-if="selectedText" 
        @click="askAI"
        type="primary"
        class="ask-ai-btn">
        🤖 问AI这部分
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps(['question', 'rewrittenAnswer'])
const emit = defineEmits(['askAI'])

const selectedText = ref('')

const handleTextSelection = () => {
  const selection = window.getSelection()
  if (selection.rangeCount > 0 && selection.toString().trim()) {
    selectedText.value = selection.toString().trim()
  }
}

const askAI = () => {
  emit('askAI', {
    selectedText: selectedText.value,
    context: props.rewrittenAnswer
  })
  selectedText.value = ''
}
</script>
```

```vue
<!-- web/src/components/ChatPanel/index.vue -->
<template>
  <div class="chat-panel">
    <div class="chat-messages" ref="messagesContainer">
      <div 
        v-for="message in messages" 
        :key="message.id"
        :class="['message', message.role]">
        <div class="message-content" v-html="message.content"></div>
        <div class="message-time">{{ formatTime(message.created_at) }}</div>
      </div>
      <div v-if="isLoading" class="message assistant typing">
        <div class="typing-indicator">AI正在思考中...</div>
      </div>
    </div>
    
    <div class="chat-input">
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="3"
        placeholder="输入你的问题..."
        @keydown.ctrl.enter="sendMessage">
      </el-input>
      <el-button 
        @click="sendMessage"
        :loading="isLoading"
        type="primary">
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useChat } from '@/composables/useChat'

const props = defineProps(['sessionId'])
const { messages, sendMessage: sendChatMessage, isLoading } = useChat(props.sessionId)

const inputMessage = ref('')
const messagesContainer = ref(null)

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  await sendChatMessage(inputMessage.value)
  inputMessage.value = ''
  
  // 滚动到底部
  nextTick(() => {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  })
}
</script>
```

## 七、部署方案

### Docker配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: 
      context: ./
      dockerfile: Dockerfile
    ports:
      - "8000:8000"    # FastAPI后端
      - "3000:3000"    # Vue前端
    environment:
      - DATABASE_URL=postgresql://teachaid:password@db:5432/teachaid
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=your_jwt_secret_key
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - QWEN_API_KEY=${QWEN_API_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./static:/app/static

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=teachaid
      - POSTGRES_USER=teachaid
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

### 开发环境启动

```bash
# 克隆项目
git clone <repository_url>
cd TeachAid

# 方式一：本地开发
# 1. 安装全局依赖
npm install -g pnpm

# 2. 安装Python依赖
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 安装前端依赖（使用pnpm）
cd web
pnpm install

# 4. 数据库初始化
cd ..
alembic upgrade head

# 5. 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. 启动前端开发服务器（新终端）
cd web
pnpm dev

# 方式二：Docker一键启动
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 项目配置文件

```json
// web/package.json - 前端依赖和脚本（基于Vben Admin）
{
  "name": "teachaid-web",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 3000",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext .vue,.js --fix",
    "format": "prettier --write ."
  },
  "dependencies": {
    "vue": "^3.5.0",
    "ant-design-vue": "^4.2.0",
    "pinia": "^2.1.0",
    "vue-router": "^4.2.0",
    "axios": "^1.6.0",
    "@vueuse/core": "^10.0.0",
    "lodash-es": "^4.17.21",
    "dayjs": "^1.11.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-vue": "^4.5.0",
    "eslint": "^8.55.0",
    "eslint-plugin-vue": "^9.18.0",
    "prettier": "^3.1.0",
    "unplugin-auto-import": "^0.17.0",
    "unplugin-vue-components": "^0.26.0"
  }
}

// pnpm-workspace.yaml - Monorepo配置
packages:
  - 'web'
  - 'app'

// web/vite.config.js - Vite配置
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { AntDesignVueResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      imports: ['vue', 'vue-router', 'pinia'],
      dts: true
    }),
    Components({
      resolvers: [AntDesignVueResolver()],
      dts: true
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 2000
  }
})
```

```dockerfile
# Dockerfile - 一体化部署
FROM python:3.11-slim

# 安装Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

WORKDIR /app

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install -r requirements.txt

# 安装pnpm并构建前端
RUN npm install -g pnpm
COPY web/ ./web/
RUN cd web && pnpm install && pnpm build

# 暴露端口
EXPOSE 8000 3000

# 启动脚本
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & cd web && pnpm preview -- --host 0.0.0.0 --port 3000"]
```

## 八、总结

本设计方案采用了现代化的技术栈，结合AI能力，为教培机构提供了完整的智能教学解决方案。核心特色包括：

1. **多模态AI理解**：替代传统OCR，更准确理解复杂教学内容
2. **智能缓存系统**：显著降低AI调用成本，提升响应速度  
3. **引导式教学**：AI不直接给答案，而是启发学生思考
4. **渐进式架构**：从简单开始，支持未来复杂功能扩展
5. **完整权限控制**：支持多角色、多级组织的权限管理

该方案具备良好的可扩展性和维护性，能够满足教培机构的实际业务需求。

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "\u4f18\u5316README.md\u529f\u80fd\u8bbe\u8ba1", "status": "completed", "activeForm": "\u4f18\u5316README.md\u529f\u80fd\u8bbe\u8ba1"}, {"content": "\u8be6\u7ec6\u8bbe\u8ba1\u6bcf\u4e2a\u6838\u5fc3\u529f\u80fd\u7684\u5b9e\u73b0\u65b9\u6848", "status": "in_progress", "activeForm": "\u8be6\u7ec6\u8bbe\u8ba1\u6bcf\u4e2a\u6838\u5fc3\u529f\u80fd\u7684\u5b9e\u73b0\u65b9\u6848"}, {"content": "\u8bbe\u8ba1\u6280\u672f\u67b6\u6784\u548c\u6570\u636e\u5e93\u6a21\u578b", "status": "pending", "activeForm": "\u8bbe\u8ba1\u6280\u672f\u67b6\u6784\u548c\u6570\u636e\u5e93\u6a21\u578b"}, {"content": "\u8bbe\u8ba1API\u63a5\u53e3\u89c4\u8303", "status": "pending", "activeForm": "\u8bbe\u8ba1API\u63a5\u53e3\u89c4\u8303"}, {"content": "\u8bbe\u8ba1\u524d\u7aef\u9875\u9762\u7ed3\u6784", "status": "pending", "activeForm": "\u8bbe\u8ba1\u524d\u7aef\u9875\u9762\u7ed3\u6784"}]
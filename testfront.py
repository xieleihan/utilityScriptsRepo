import os
import logging
from typing import Optional
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain.chat_models import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 前端知识库数据
FRONTEND_KNOWLEDGE_BASE = [
    {"id": 1, "question": "什么是DOM？", "answer": "DOM（Document Object Model）是HTML和XML文档的编程接口。它将文档构造为节点和对象的树结构，使JavaScript能够访问和修改页面内容、结构和样式。"},
    {"id": 2, "question": "解释JavaScript的闭包概念", "answer": "闭包是指函数能够访问其外部作用域中的变量，即使在外部函数已经返回之后。这是因为JavaScript的词法作用域特性，内部函数保持对外部函数变量的引用。"},
    {"id": 3, "question": "CSS盒模型是什么？", "answer": "CSS盒模型描述了元素在页面中所占空间的计算方式。包括content（内容）、padding（内边距）、border（边框）、margin（外边距）四个部分。"},
    {"id": 4, "question": "React和Vue的区别", "answer": "React使用JSX语法和虚拟DOM，采用单向数据流；Vue使用模板语法，支持双向数据绑定，学习曲线更平缓。"},
    {"id": 5, "question": "什么是跨域问题？如何解决？", "answer": "跨域是指浏览器的同源策略限制了不同域名、端口或协议之间的资源访问。解决方案包括：CORS、JSONP、代理服务器、postMessage等。"}
]

def retrieve_context(query: str) -> str:
    """简单知识库检索"""
    if not query.strip():
        return "请输入具体的问题或关键词进行检索。"
    query_lower = query.lower()
    results = []
    for item in FRONTEND_KNOWLEDGE_BASE:
        if query_lower in item["question"].lower() or query_lower in item["answer"].lower():
            results.append(item)
    if not results:
        return f"未找到与'{query}'相关的知识。"
    return "\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in results[:3]])

def validate_environment() -> bool:
    required = ['OPENAI_API_KEY', 'OPENAI_API_BASE_URL']
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        logger.error(f"缺少环境变量: {', '.join(missing)}")
        return False
    return True

class FrontendInterviewer:
    def __init__(self):
        if not validate_environment():
            raise ValueError("环境配置不正确")
        
        self.llm = ChatOpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_API_BASE_URL'),
            model="deepseek-chat",
            temperature=0.1,
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        self.interview_started = False
        self.turn_count = 0
        self.question_count = 1
        self.max_turns = int(os.getenv('MAX_CONVERSATION_TURNS', 20))
        self.system_prompt = (
            "你是一个资深前端技术面试官，严格按照指定格式提问和评判回答。"
        )

    def start_interview(self) -> str:
        self.interview_started = True
        self.turn_count = 0
        self.question_count = 1
        return """欢迎参加前端技术面试！
**第1题**：什么是DOM？请简单解释一下DOM的概念和作用。
        """

    def get_response(self, user_input: str) -> str:
        if not user_input.strip():
            return "请说些什么，我在认真倾听。"
        
        self.turn_count += 1
        if self.turn_count > self.max_turns:
            return self._end_interview("对话轮次已达上限")

        knowledge_context = retrieve_context(user_input)
        prompt = f"""
系统角色: {self.system_prompt}

候选人对第{self.question_count}题的回答: {user_input}

参考知识库:
{knowledge_context}

请严格按照以下格式回复:

**回答评判**：[正确/错误/部分正确]

**详细解释**：
[详细解释]

**知识补充**：
[补充知识点]

---

**下一题**：
[提出第{self.question_count + 1}个具体技术问题]
"""
        # 直接调用 LLM
        try:
            result = self.llm.invoke(prompt)
            response = result.content if hasattr(result, 'content') else str(result)
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            response = "抱歉，我遇到了技术问题，请稍后再试。"
        
        self.question_count += 1

        if self._should_end_interview(user_input):
            response += "\n\n" + self._end_interview("面试自然结束")
        
        return response

    def _should_end_interview(self, user_input: str) -> bool:
        end_keywords = ["结束", "退出", "再见", "谢谢", "quit", "exit"]
        if any(kw in user_input.lower() for kw in end_keywords):
            return True
        if self.question_count > 15 or self.turn_count >= self.max_turns - 1:
            return True
        return False

    def _end_interview(self, reason: str) -> str:
        return f"""
**面试总结**

轮次: {self.turn_count}
问题数量: {self.question_count - 1}

祝您技术之路越走越远！{reason}
        """

def main():
    try:
        interviewer = FrontendInterviewer()
        print(interviewer.start_interview())
        while True:
            user_input = input("\n您: ").strip()
            if user_input.lower() in ['quit', 'exit', '退出', '结束', '再见']:
                print("\n再见！感谢参加面试。")
                break
            response = interviewer.get_response(user_input)
            print("\n面试官:", response)
            if "**面试总结**" in response:
                break
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
        print(f"系统启动失败: {e}")

if __name__ == "__main__":
    main()

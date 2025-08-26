import os
import json
import faiss
import numpy as np

# 引入OpenAI
from openai import OpenAI
# 引入 LangChain 相关组件
from langchain.agents import initialize_agent, AgentType # 代理和代理类型
from langchain.chat_models import ChatOpenAI # 聊天模型
from langchain.chains.conversation.memory import ConversationBufferMemory # 记忆
from langchain.tools import Tool # 工具

# 引入本地模型,实现向量化
from sentence_transformers import SentenceTransformer
# 在线向量化
from langchain_community.embeddings import HuggingFaceEmbeddings

# 定义向量json的存放
VECTOR_STORE_PATH = "./assets/book1.json"

# 读取文本文件内容
if os.path.exists(VECTOR_STORE_PATH):
    print("存在向量文件,跳过生成")
    with open(VECTOR_STORE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    print("未生成向量文件,开始生成")
    # 加载多语言模型（支持中文）
    # model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    with open("./assets/book.txt", "r", encoding="utf-8") as f:
        text = f.read()
    # 将文本分割成段落
    chunks = [text[i:i + 500] for i in range(0, len(text), 500)]
    # 向量化
    # embeddings = model.encode(chunks)
    # 使用在线向量化
    embeddings = model.embed_documents(chunks)
    # 保存向量数据到本地文件
    # data = [{"text": chunk, "vector": emb.tolist()} for chunk, emb in zip(chunks, embeddings)]
    data = [{"text": chunk, "vector": emb} for chunk, emb in zip(chunks, embeddings)]
    with open("./assets/book1.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

vectors = np.array([d["vector"] for d in data], dtype='float32')
dimension = vectors.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(vectors)


# ---------- 测试 --------------
query = ""
# 先向量化查询
# 本地
# model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
# 在线
model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# 本地
# query_vector = model.encode([query])
# 在线
query_vector = model.embed_query(query)
query_vector = np.array(query_vector, dtype='float32').reshape(1, -1)  # 转二维

D, I = index.search(np.array(query_vector, dtype='float32'), k=3)

# print("最相关的段落：")
# for idx in I[0]:
#     print("-", data[idx]["text"])
# ---------- 测试 --------------

# 引入环境变量
from dotenv import load_dotenv
load_dotenv()


def retrieve_context(query, top_k=3):
    # 向量化查询
    query_vector = model.embed_query(query)
    query_vector = np.array(query_vector, dtype='float32').reshape(1, -1)

    # 检索
    D, I = index.search(query_vector, k=top_k)

    # 取出对应文本
    context = "\n".join([data[idx]["text"] for idx in I[0]])
    return context

# 工具函数
tools = [
    Tool(
        name="知识库检索",
        func=lambda q: retrieve_context(q),
        description="检索相关上下文内容"
    )
]

# 初始化 LLM
llm = ChatOpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    base_url=os.getenv('OPENAI_API_BASE_URL'),
    model="deepseek-chat",
    temperature=0,
)

# 开启记忆
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="output")

prompt = '''
    
'''


def getLLMRespoense(content):
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        agent_kwargs={
            "system_message": prompt
        }
    )

    response = agent.run(content)
    return response

getLLMRespoense("")
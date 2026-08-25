import os
from abc import abstractmethod, ABC
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from utils.config_handler import rag_conf

# Ollama 服务地址：
#   本地跑      → 用 rag.yml 里的 base_url（默认 http://localhost:11434）
#   容器里跑    → compose 注入环境变量 OLLAMA_BASE_URL=http://ollama:11434 覆盖
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", rag_conf.get("base_url", "http://localhost:11434"))


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        pass


class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return ChatOllama(model=rag_conf["chat_model_name"], base_url=OLLAMA_BASE_URL)


class EmbeddingsFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return OllamaEmbeddings(model=rag_conf["embedding_model_name"], base_url=OLLAMA_BASE_URL)


chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()

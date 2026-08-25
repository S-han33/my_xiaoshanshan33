import os.path
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.logger_handler import logger
from utils.file_handler import txt_loader, pdf_loader,docx_loader ,listdir_type ,get_file_md5
from utils.path_tool import get_abs_path
from utils.config_handler import chroma_conf
from model.factory import embed_model

class VectorStoreService:
    def __init__(self):
        self.vectors = Chroma(
            collection_name=chroma_conf['collection_name'],
            embedding_function =embed_model,
            persist_directory= chroma_conf['persist_directory']
        )

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf['chunk_size'],
            chunk_overlap=chroma_conf['chunk_overlap'],
            separators=chroma_conf['separators'],
            length_function=len,
        )

    def get_retriever(self):
        return self.vectors.as_retriever(search_kwargs = {"k":chroma_conf['k']})

    def load_document(self):
        """
                从数据文件夹内读取数据文件，转为向量存入向量库
                要计算文件的MD5做去重
                :return: None
                """

        def chunk_md5_hex(md5_for_check):
            if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
                open(get_abs_path(chroma_conf["md5_hex_store"]), "w", encoding="utf-8").close()
                return False

            with open(get_abs_path(chroma_conf["md5_hex_store"]), "r", encoding="utf-8") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == md5_for_check:
                        return True
                return False

        def add_md5_hex(md5_for_check):
            with open(get_abs_path(chroma_conf["md5_hex_store"]), "a", encoding="utf-8") as f:
                f.write(md5_for_check + '\n')

        def get_file_document(read_path):
            if read_path.endswith("txt"):
                return txt_loader(read_path)
            if read_path.endswith("pdf"):
                return pdf_loader(read_path)
            if read_path.endswith("docx"):
                return docx_loader(read_path)
            return []

        allowed_files_path = listdir_type(get_abs_path(chroma_conf["data_path"]),
                                          tuple(chroma_conf["allow_knowledge_file_type"]),)
        for path in allowed_files_path:
            md5_hex = get_file_md5(path)

            if chunk_md5_hex(md5_hex):
                logger.info(f"[加载知识库]{path}内容已经存在知识库内，跳过")
                continue
            try:
                documents: list[Document] = get_file_document(path)
                if not documents:
                    logger.warning(f"[加载知识库]{path}内没有有效文本内容，跳过")
                    continue

                split_document: list[Document] = self.splitter.split_documents(documents)
                if not split_document:
                    logger.warning(f"[加载知识库]{path}分片后没有有效文本内容，跳过")
                    continue
                self.vectors.add_documents(split_document)
                add_md5_hex(md5_hex)
                logger.info(f"[加载知识库]{path} 内容加载成功")
            except Exception as e:
                logger.error(f"[加载知识库]{path}加载失败：{str(e)}", exc_info=True)
                continue

if __name__ == '__main__':
    vs = VectorStoreService()

    vs.load_document()

    retriever = vs.get_retriever()

    res = retriever.invoke("迷路")   #拿"迷路"当问题去检索 ，打印检索到的内容。搜到了 = 加载成功；搜不到 = 加载有问题
    for r in res:
        print(r.page_content)
        print("-"*20)







import  os, hashlib

from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_core.documents import Document

from utils.logger_handler import logger


def get_file_md5 (filepath):
    if not os.path.exists(filepath):
        logger.error(f"[md5计算]文件{filepath}不存在")
        return
    if not os.path.isfile(filepath):
        logger.error(f"[md5计算]路径{filepath}不是文件")
        return

    md5_obj = hashlib.md5()
    chunk_size = 4069
    try:
        with open(filepath,"rb")as f:
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)
            md5_hex = md5_obj.hexdigest()
            return md5_hex
    except Exception as e:
        logger.error(f"计算文件{filepath}md5失败，{str(e)}")
        return None
def listdir_type(path, types):
    files = []
    if not os.path.isdir(path):
        logger.error(f"[listdir_type]{path}不是文件夹")
        return types

    for f in os.listdir(path):
        if f.endswith(types):
            files.append(os.path.join(path, f))
    return  tuple(files)

def pdf_loader(filepath: str, passwd=None):
    return PyPDFLoader(filepath,passwd).load()

def txt_loader(filepath: str)-> list[Document]:
    return TextLoader(filepath,encoding='utf-8').load()

def docx_loader(filepath: str) -> list[Document]:
    return Docx2txtLoader(filepath).load()

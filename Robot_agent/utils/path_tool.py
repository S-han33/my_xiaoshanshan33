import os

def get_catalogue():
    current_directory= os.path.abspath(__file__)
    directory_up = os.path.dirname(current_directory)
    project_root = os.path.dirname(directory_up)
    return project_root

def get_abs_path(relative_path:str):
    path_catalogue = get_catalogue()
    return os.path.join(path_catalogue,relative_path)

if __name__ == '__main__':
    print(get_abs_path("练习.py"))

import os

def get_file_list(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list

if __name__ == '__main__':
    directory = 'C:/Users/Yhrza/Desktop/python'  # 请将这里替换为你想要列出文件的目录路径      
    files = get_file_list(directory)
    for file in files:
        print(file)

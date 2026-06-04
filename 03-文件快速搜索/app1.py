from pathlib import Path

print("简单文件查找器")
print("输入 起始目录 查找所有匹配的文件")

try:

    s= input()
    start = Path(s)#先转换path对象

    pattern = input("请输入文件名（如：*.txt , data*.csv）：")
    print("提示：用* 匹配任意字符 , 比如 *.txt 或 report*.pdf/n")

    print(f"\n正在搜索 {s} 下的名字匹配 {pattern} 的文件...\n")

    matched=list(start.rglob(pattern))

    if(len(matched)==0):
        print("Not Found Anything!")
    else:
        print ("Have Found:")
        for idx,filePath in enumerate(matched):
            
            print(f"{idx}.{filePath}")

except (FileNotFoundError, NotADirectoryError) as e:#防御性代码
    print("Error ! Not Found Anything!")
# enumerate 返回的就是这种元组序列
pairs = [(1, "苹果"), (2, "香蕉")]
for i, item in pairs:      # 直接遍历元组列表，照样两个变量接
    print(i, item)

# 同理，两个元素的列表也行
pairs2 = [[1, "苹果"], [2, "香蕉"]]
for i, item in pairs2:     # 元素是列表也能解包
    print(f"这是第二组数据{i, item}")

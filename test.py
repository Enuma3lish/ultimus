def process_scheduler(func, *args):
    # 如果只有一个参数且这个参数是列表，直接将列表作为单一参数传递
    if len(args) == 1 and isinstance(args[0], list):
        return func(args[0])
    
    # 否则，将所有参数传递给函数，包括列表
    return func(*args)
def target_function(*args):
    # 打印接收到的参数
    print(f"Function called with {len(args)} arguments.")
    for i, arg in enumerate(args, start=1):
        print(f"Argument {i}: {arg}")

# 僅一個列表作為參數
process_scheduler(target_function, [1, 2, 3])

# 多個單一值和一個列表作為參數
process_scheduler(target_function, 1, 2, 3, [4, 5, 6])

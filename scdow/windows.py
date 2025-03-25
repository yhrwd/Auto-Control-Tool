import pygetwindow as gw

def wininit(keyword: str, x: int, y: int, w: int, h: int):
    found_windows = []
    for win in gw.getWindowsWithTitle(keyword):
        if keyword in win.title:
            found_windows.append(win)

    if not found_windows:
        print(f"未找到标题包含 '{keyword}' 的窗口。")
        return None

    if len(found_windows) > 1:
        print(f"共找到 {len(found_windows)} 个相关窗口，请选择：")
        for i, win in enumerate(found_windows, start=1):
            print(f"{i}. {win.title}")
        winsel = found_windows[int(input("请输入序号：")) - 1]
    else:
        winsel = found_windows[0]

    try:
        winsel.minimize()
        winsel.restore()
        # 调整窗口位置和大小
        winsel.moveTo(x, y)
        winsel.resizeTo(w, h)

        # 验证窗口参数
        actual_rect = (winsel.left, winsel.top, winsel.width, winsel.height)
        print("初始化成功\n", f"窗口参数: X={actual_rect[0]}, Y={actual_rect[1]}," f"W={actual_rect[2]}, H={actual_rect[3]}")
        return winsel
    except Exception as e:
        print(f"处理窗口时发生错误: {e}")
        return None

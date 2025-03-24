import pygetwindow as gw
import win32gui
import win32con

def wininit(keyword: str, x: int, y: int, w: int, h: int):
    windows = gw.getAllWindows()
    found = False  # 用于标记是否找到窗口
    for window in windows:
        if keyword in window.title:
            # 使用 _hWnd 属性获取窗口句柄。
            ck = window._hWnd
            print("找到窗口，句柄为：", ck)
            found = True  # 找到窗口，将标记设置为 True

            # 激活并还原窗口。
            window.activate()
            win32gui.SendMessage(ck, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)

            # 将处理窗口大小位置。
            window.resizeTo(w, h)
            window.moveTo(x, y)

            try:
                # 获取窗口矩形。
                rect = win32gui.GetWindowRect(ck)
                print("已初始化窗口: X×Y: %d,%d, W×H: %d,%d" % rect)
                return ck  
            except Exception as e:
                # 捕获并打印可能的异常。
                print(f"处理窗口时发生错误: {e}")
    
    # 在所有窗口识别完后，检查是否找到窗口
    if not found:
        print(f"未找到标题包含 '{keyword}' 的窗口。")

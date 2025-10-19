# main.py
# 主函数
import threading

#多头择时策略
from stock_project.DTZS_run import dtzs_run

def main():
    stop_event = threading.Event()

    # 创建并启动策略线程
    strategy_thread = threading.Thread(
        target=dtzs_run,
        args=(stop_event,),
        daemon=True  # 设置为守护线程，主线程退出时自动结束
    )
    strategy_thread.start()
    print("策略已启动，输入 'stop' 停止程序...")

    try:
        # 主线程等待用户输入
        while True:
            user_input = input().strip().lower()
            if user_input == 'stop':
                print("正在停止策略...")
                stop_event.set()  # 设置停止信号
                strategy_thread.join(timeout=30)  # 等待线程结束（最多30秒）
                break
    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止...")
        stop_event.set()
    finally:
        print("程序已安全停止")


if __name__ == "__main__":
    main()
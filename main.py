import asyncio
from log_monitor import monitor_log

async def main():
    # Запускаем два монитора логов параллельно
    await asyncio.gather(
        monitor_log(r'C:\Users\rootu\cubixworld\updates\HiTech\logs\fml-client-latest.log', 'HiTech'),
        monitor_log(r'C:\Users\rootu\cubixworld\updates\HiTech-Mobile\logs\fml-client-latest.log', 'Mobile')
    )

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()  # Используем существующий event loop
        loop.run_until_complete(main())
    finally:
        loop.close()  # Закрываем loop

import sys
import os
import matplotlib
matplotlib.use('Agg')  # без GUI, сохраняем в файл
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def main():
    csv_file = "experiment_results.csv"
    if len(sys.argv) >= 2:
        csv_file = sys.argv[1]

    if not os.path.exists(csv_file):
        print(f"Файл {csv_file} не найден!")
        return

    # Чтение CSV
    sizes = []
    times = []
    gflops = []
    gflops_s = []
    memory = []

    with open(csv_file, 'r') as f:
        header = f.readline()  # пропускаем заголовок
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            sizes.append(int(parts[0]))
            times.append(float(parts[1]))
            gflops.append(float(parts[2]))
            gflops_s.append(float(parts[3]))
            memory.append(float(parts[4]))

    if not sizes:
        print("Нет данных для построения графиков!")
        return

    # --- Стиль ---
    plt.rcParams.update({
        'font.size': 12,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'figure.figsize': (10, 6)
    })

    # === График 1: Время выполнения ===
    fig, ax = plt.subplots()
    ax.plot(sizes, times, 'bo-', linewidth=2, markersize=8, label='Время (сек)')
    ax.set_xlabel('Размер матрицы N')
    ax.set_ylabel('Время выполнения (сек)')
    ax.set_title('Зависимость времени умножения матриц от размера\n(однопоточная реализация, порядок i-k-j)')
    ax.legend()

    # Подписи значений на точках
    for i, (x, y) in enumerate(zip(sizes, times)):
        ax.annotate(f'{y:.3f}', (x, y), textcoords="offset points",
                    xytext=(0, 12), ha='center', fontsize=9)

    plt.tight_layout()
    plt.savefig('graph_time.png', dpi=150)
    print(f"  Сохранён график: graph_time.png")
    plt.close()

    # === График 2: Производительность GFLOP/s ===
    fig, ax = plt.subplots()
    ax.plot(sizes, gflops_s, 'rs-', linewidth=2, markersize=8, label='GFLOP/s')
    ax.set_xlabel('Размер матрицы N')
    ax.set_ylabel('Производительность (GFLOP/s)')
    ax.set_title('Производительность умножения матриц\n(однопоточная реализация, порядок i-k-j)')
    ax.legend()

    for i, (x, y) in enumerate(zip(sizes, gflops_s)):
        ax.annotate(f'{y:.2f}', (x, y), textcoords="offset points",
                    xytext=(0, 12), ha='center', fontsize=9)

    plt.tight_layout()
    plt.savefig('graph_gflops.png', dpi=150)
    print(f"  Сохранён график: graph_gflops.png")
    plt.close()

    # === График 3: Память ===
    fig, ax = plt.subplots()
    ax.bar(range(len(sizes)), memory, color='green', alpha=0.7)
    ax.set_xticks(range(len(sizes)))
    ax.set_xticklabels([str(s) for s in sizes])
    ax.set_xlabel('Размер матрицы N')
    ax.set_ylabel('Память (МБ)')
    ax.set_title('Потребление памяти (3 матрицы NxN, double)')

    for i, (x, y) in enumerate(zip(range(len(sizes)), memory)):
        ax.text(x, y + 0.5, f'{y:.1f}', ha='center', fontsize=9)

    plt.tight_layout()
    plt.savefig('graph_memory.png', dpi=150)
    print(f"  Сохранён график: graph_memory.png")
    plt.close()

    # === График 4: Комбинированный (время + теоретическая O(n³)) ===
    fig, ax1 = plt.subplots()

    color1 = 'tab:blue'
    ax1.set_xlabel('Размер матрицы N')
    ax1.set_ylabel('Время (сек)', color=color1)
    ax1.plot(sizes, times, 'bo-', linewidth=2, markersize=8, label='Время (факт)', color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)

    # Теоретическая кривая O(n³), масштабированная по первой точке
    if times[0] > 0:
        scale = times[0] / (sizes[0] ** 3)
        theoretical = [scale * (n ** 3) for n in sizes]
        ax1.plot(sizes, theoretical, 'b--', alpha=0.4, linewidth=1.5, label='Теор. O(N³)')

    ax1.legend(loc='upper left')
    ax1.set_title('Время выполнения vs теоретическая сложность O(N³)')
    plt.tight_layout()
    plt.savefig('graph_combined.png', dpi=150)
    print(f"  Сохранён график: graph_combined.png")
    plt.close()

    # === Вывод таблицы в консоль ===
    print("\n" + "=" * 75)
    print(f"{'N':>6} | {'Время (сек)':>12} | {'GFLOP':>8} | {'GFLOP/s':>8} | {'Память (МБ)':>12}")
    print("-" * 75)
    for i in range(len(sizes)):
        print(f"{sizes[i]:>6} | {times[i]:>12.6f} | {gflops[i]:>8.3f} | {gflops_s[i]:>8.4f} | {memory[i]:>12.2f}")
    print("=" * 75)

if __name__ == "__main__":
    main()
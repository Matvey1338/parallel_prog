import sys
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    csv_file = "experiment_results.csv"
    if len(sys.argv) >= 2:
        csv_file = sys.argv[1]

    if not os.path.exists(csv_file):
        print(f"Файл {csv_file} не найден!")
        return

    # Создаём папку data, если нет
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    # Чтение CSV
    sizes, times, gflops, gflops_s, memory = [], [], [], [], []

    with open(csv_file, 'r') as f:
        f.readline()  # заголовок
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
        print("Нет данных!")
        return

    plt.rcParams.update({
        'font.size': 12,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'figure.figsize': (10, 6)
    })

    # === График 1: Время ===
    fig, ax = plt.subplots()
    ax.plot(sizes, times, 'bo-', linewidth=2, markersize=8)
    ax.set_xlabel('Размер матрицы N')
    ax.set_ylabel('Время выполнения (сек)')
    ax.set_title('Зависимость времени умножения матриц от размера\n(однопоточная реализация, порядок i-k-j)')
    for x, y in zip(sizes, times):
        ax.annotate(f'{y:.3f}', (x, y), textcoords="offset points",
                    xytext=(0, 12), ha='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'graph_time.png'), dpi=150)
    print(f"  Сохранён: {output_dir}/graph_time.png")
    plt.close()

    # === График 2: GFLOP/s ===
    fig, ax = plt.subplots()
    ax.plot(sizes, gflops_s, 'rs-', linewidth=2, markersize=8)
    ax.set_xlabel('Размер матрицы N')
    ax.set_ylabel('Производительность (GFLOP/s)')
    ax.set_title('Производительность умножения матриц\n(однопоточная реализация, порядок i-k-j)')

    # Подсветка пика
    peak_idx = gflops_s.index(max(gflops_s))
    ax.annotate(f'пик: {gflops_s[peak_idx]:.2f}',
                (sizes[peak_idx], gflops_s[peak_idx]),
                textcoords="offset points", xytext=(15, 10),
                ha='center', fontsize=10, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='red'))

    for i, (x, y) in enumerate(zip(sizes, gflops_s)):
        if i != peak_idx:
            ax.annotate(f'{y:.2f}', (x, y), textcoords="offset points",
                        xytext=(0, 12), ha='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'graph_gflops.png'), dpi=150)
    print(f"  Сохранён: {output_dir}/graph_gflops.png")
    plt.close()

    # === График 3: Память ===
    fig, ax = plt.subplots()
    ax.bar(range(len(sizes)), memory, color='green', alpha=0.7)
    ax.set_xticks(range(len(sizes)))
    ax.set_xticklabels([str(s) for s in sizes])
    ax.set_xlabel('Размер матрицы N')
    ax.set_ylabel('Память (МБ)')
    ax.set_title('Потребление памяти (3 матрицы NxN, double)')
    for i, y in enumerate(memory):
        ax.text(i, y + 0.5, f'{y:.1f}', ha='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'graph_memory.png'), dpi=150)
    print(f"  Сохранён: {output_dir}/graph_memory.png")
    plt.close()

    # === График 4: Время vs O(N³) ===
    fig, ax1 = plt.subplots()
    ax1.set_xlabel('Размер матрицы N')
    ax1.set_ylabel('Время (сек)', color='tab:blue')
    ax1.plot(sizes, times, 'bo-', linewidth=2, markersize=8, label='Время (факт)', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    if times[0] > 0:
        scale = times[0] / (sizes[0] ** 3)
        theoretical = [scale * (n ** 3) for n in sizes]
        ax1.plot(sizes, theoretical, 'b--', alpha=0.4, linewidth=1.5, label='Теор. O(N³)')

    ax1.legend(loc='upper left')
    ax1.set_title('Время выполнения vs теоретическая сложность O(N³)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'graph_combined.png'), dpi=150)
    print(f"  Сохранён: {output_dir}/graph_combined.png")
    plt.close()

    # Таблица в консоль
    print("\n" + "=" * 75)
    print(f"{'N':>6} | {'Время (сек)':>12} | {'GFLOP':>8} | {'GFLOP/s':>8} | {'Память (МБ)':>12}")
    print("-" * 75)
    for i in range(len(sizes)):
        print(f"{sizes[i]:>6} | {times[i]:>12.6f} | {gflops[i]:>8.3f} | {gflops_s[i]:>8.4f} | {memory[i]:>12.2f}")
    print("=" * 75)

if __name__ == "__main__":
    main()
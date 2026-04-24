import sys
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict

def main():
    csv_file = "experiment_results.csv"
    if len(sys.argv) >= 2:
        csv_file = sys.argv[1]

    if not os.path.exists(csv_file):
        print(f"Файл {csv_file} не найден!")
        return

    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    # Dictionary format: data[threads]["sizes"], data[threads]["times"], etc.
    # We will use defaultdict of lists
    data = defaultdict(lambda: {'sizes': [], 'times': [], 'gflops': [], 'gflops_s': [], 'memory': []})

    with open(csv_file, 'r') as f:
        f.readline()  # заголовок
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            threads = int(parts[0])
            size = int(parts[1])
            time_sec = float(parts[2])
            gflop = float(parts[3])
            gflop_s = float(parts[4])
            memory_mb = float(parts[5])

            data[threads]['sizes'].append(size)
            data[threads]['times'].append(time_sec)
            data[threads]['gflops'].append(gflop)
            data[threads]['gflops_s'].append(gflop_s)
            data[threads]['memory'].append(memory_mb)

    if not data:
        print("Нет данных!")
        return

    plt.rcParams.update({
        'font.size': 12,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'figure.figsize': (10, 6)
    })

    thread_counts = sorted(data.keys())
    
    # === График 1: Время ===
    fig, ax = plt.subplots()
    for t in thread_counts:
        ax.plot(data[t]['sizes'], data[t]['times'], marker='o', linewidth=2, markersize=6, label=f'{t} потоков')
    
    ax.set_xlabel('Размер матрицы N')
    ax.set_ylabel('Время выполнения (сек)')
    ax.set_title('Зависимость времени умножения матриц от размера\n(Многопоточная реализация, порядок i-k-j)')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'graph_time.png'), dpi=150)
    print(f"  Сохранён: {output_dir}/graph_time.png")
    plt.close()

    # === График 2: GFLOP/s ===
    fig, ax = plt.subplots()
    for t in thread_counts:
        ax.plot(data[t]['sizes'], data[t]['gflops_s'], marker='s', linewidth=2, markersize=6, label=f'{t} потоков')
        
    ax.set_xlabel('Размер матрицы N')
    ax.set_ylabel('Производительность (GFLOP/s)')
    ax.set_title('Производительность умножения матриц\n(Многопоточная реализация, порядок i-k-j)')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'graph_gflops.png'), dpi=150)
    print(f"  Сохранён: {output_dir}/graph_gflops.png")
    plt.close()

    # === График 3: Ускорение (Speedup) ===
    # Speedup = T(1) / T(p)
    if 1 in thread_counts:
        fig, ax = plt.subplots()
        t1_times = dict(zip(data[1]['sizes'], data[1]['times']))
        
        for t in thread_counts:
            if t == 1:
                continue
            sizes_t = data[t]['sizes']
            times_t = data[t]['times']
            speedups = []
            valid_sizes = []
            
            for s, time_p in zip(sizes_t, times_t):
                if s in t1_times and t1_times[s] > 0 and time_p > 0:
                    speedups.append(t1_times[s] / time_p)
                    valid_sizes.append(s)
            
            if valid_sizes:
                ax.plot(valid_sizes, speedups, marker='^', linewidth=2, markersize=6, label=f'{t} потоков')
        
        ax.set_xlabel('Размер матрицы N')
        ax.set_ylabel('Ускорение (Speedup)')
        ax.set_title('Ускорение от распараллеливания (Speedup = T1 / Tp)')
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'graph_speedup.png'), dpi=150)
        print(f"  Сохранён: {output_dir}/graph_speedup.png")
        plt.close()

    # Таблица в консоль
    print("\n" + "=" * 85)
    print(f"{'Потоки':>6} | {'N':>6} | {'Время (сек)':>12} | {'GFLOP':>8} | {'GFLOP/s':>8} | {'Память (МБ)':>12}")
    print("-" * 85)
    for t in thread_counts:
        for i in range(len(data[t]['sizes'])):
            print(f"{t:>6} | {data[t]['sizes'][i]:>6} | {data[t]['times'][i]:>12.6f} | {data[t]['gflops'][i]:>8.3f} | {data[t]['gflops_s'][i]:>8.4f} | {data[t]['memory'][i]:>12.2f}")
    print("=" * 85)

if __name__ == "__main__":
    main()
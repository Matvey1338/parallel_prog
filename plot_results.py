import sys
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import collections

def main():
    csv_file = "experiment_results.csv"
    if len(sys.argv) >= 2:
        csv_file = sys.argv[1]

    if not os.path.exists(csv_file):
        print(f"Файл {csv_file} не найден!")
        return

    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    data_by_block = collections.defaultdict(lambda: {'sizes': [], 'times': [], 'gflops': [], 'gflops_s': [], 'memory': []})

    with open(csv_file, 'r') as f:
        f.readline()  # заголовок
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) < 6:
                continue
            
            n = int(parts[0])
            block_size = int(parts[1])
            time_sec = float(parts[2])
            gflop = float(parts[3])
            gflop_s = float(parts[4])
            mem_mb = float(parts[5])
            
            data_by_block[block_size]['sizes'].append(n)
            data_by_block[block_size]['times'].append(time_sec)
            data_by_block[block_size]['gflops'].append(gflop)
            data_by_block[block_size]['gflops_s'].append(gflop_s)
            data_by_block[block_size]['memory'].append(mem_mb)

    if not data_by_block:
        print("Нет данных!")
        return

    plt.rcParams.update({
        'font.size': 12,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'figure.figsize': (10, 6)
    })
    
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple']
    markers = ['o', 's', '^', 'D', 'v']

    # === График 1: Время ===
    fig, ax = plt.subplots()
    for idx, (block_size, data) in enumerate(sorted(data_by_block.items())):
        c = colors[idx % len(colors)]
        m = markers[idx % len(markers)]
        ax.plot(data['sizes'], data['times'], f'{m}-', color=c, linewidth=2, markersize=8, label=f'Блок {block_size}x{block_size}')
        for x, y in zip(data['sizes'], data['times']):
            ax.annotate(f'{y:.3f}', (x, y), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8, color=c)
            
    ax.set_xlabel('Размер матрицы N')
    ax.set_ylabel('Время выполнения (сек)')
    ax.set_title('Зависимость времени умножения матриц от размера (CUDA)')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'graph_time.png'), dpi=150)
    print(f"  Сохранён: {output_dir}/graph_time.png")
    plt.close()

    # === График 2: GFLOP/s ===
    fig, ax = plt.subplots()
    for idx, (block_size, data) in enumerate(sorted(data_by_block.items())):
        c = colors[idx % len(colors)]
        m = markers[idx % len(markers)]
        ax.plot(data['sizes'], data['gflops_s'], f'{m}-', color=c, linewidth=2, markersize=8, label=f'Блок {block_size}x{block_size}')
        
        # Подсветка пика для каждого блока
        if data['gflops_s']:
            peak_idx = data['gflops_s'].index(max(data['gflops_s']))
            ax.annotate(f'{data["gflops_s"][peak_idx]:.1f}',
                        (data['sizes'][peak_idx], data['gflops_s'][peak_idx]),
                        textcoords="offset points", xytext=(0, 15),
                        ha='center', fontsize=9, fontweight='bold', color=c)
            
    ax.set_xlabel('Размер матрицы N')
    ax.set_ylabel('Производительность (GFLOP/s)')
    ax.set_title('Производительность умножения матриц (CUDA)')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'graph_gflops.png'), dpi=150)
    print(f"  Сохранён: {output_dir}/graph_gflops.png")
    plt.close()

    # Таблица в консоль
    print("\n" + "=" * 85)
    print(f"{'N':>6} | {'Блок':>6} | {'Время (сек)':>12} | {'GFLOP':>8} | {'GFLOP/s':>8} | {'Память (МБ)':>12}")
    print("-" * 85)
    for block_size, data in sorted(data_by_block.items()):
        for i in range(len(data['sizes'])):
            print(f"{data['sizes'][i]:>6} | {block_size:>6} | {data['times'][i]:>12.6f} | {data['gflops'][i]:>8.3f} | {data['gflops_s'][i]:>8.4f} | {data['memory'][i]:>12.2f}")
    print("=" * 85)

if __name__ == "__main__":
    main()
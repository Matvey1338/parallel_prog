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

    # Структуры для хранения данных, группировка по ядрам
    data_by_core = defaultdict(lambda: {
        'sizes': [], 'times': [], 'gflops': [], 'gflops_s': [], 'memory': []
    })
    
    unique_sizes = set()

    with open(csv_file, 'r') as f:
        header = f.readline().strip().split(',')
        has_cores = 'cores' in header
        
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            
            if has_cores:
                n = int(parts[0])
                core = int(parts[1])
                t = float(parts[2])
                gf = float(parts[3])
                gfs = float(parts[4])
                mem = float(parts[5])
            else:
                n = int(parts[0])
                core = 1
                t = float(parts[1])
                gf = float(parts[2])
                gfs = float(parts[3])
                mem = float(parts[4])
                
            unique_sizes.add(n)
            data_by_core[core]['sizes'].append(n)
            data_by_core[core]['times'].append(t)
            data_by_core[core]['gflops'].append(gf)
            data_by_core[core]['gflops_s'].append(gfs)
            data_by_core[core]['memory'].append(mem)

    if not data_by_core:
        print("Нет данных!")
        return
        
    cores_list = sorted(list(data_by_core.keys()))
    sizes_list = sorted(list(unique_sizes))

    plt.rcParams.update({
        'font.size': 12,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'figure.figsize': (10, 6)
    })
    
    colors = ['bo-', 'rs-', 'g^-', 'mv-', 'co-', 'y*-', 'k+-']

    # === График 1: Время ===
    fig, ax = plt.subplots()
    for i, core in enumerate(cores_list):
        ax.plot(data_by_core[core]['sizes'], data_by_core[core]['times'], 
                colors[i % len(colors)], linewidth=2, markersize=8, label=f'{core} ядр(а)')
                
    ax.set_xlabel('Размер матрицы N')
    ax.set_ylabel('Время выполнения (сек)')
    ax.set_title('Зависимость времени выполнения от размера матрицы (MPI)')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'graph_time.png'), dpi=150)
    print(f"  Сохранён: {output_dir}/graph_time.png")
    plt.close()

    # === График 2: Производительность ===
    fig, ax = plt.subplots()
    for i, core in enumerate(cores_list):
        ax.plot(data_by_core[core]['sizes'], data_by_core[core]['gflops_s'], 
                colors[i % len(colors)], linewidth=2, markersize=8, label=f'{core} ядр(а)')
                
    ax.set_xlabel('Размер матрицы N')
    ax.set_ylabel('Производительность (GFLOP/s)')
    ax.set_title('Производительность умножения матриц (MPI)')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'graph_gflops.png'), dpi=150)
    print(f"  Сохранён: {output_dir}/graph_gflops.png")
    plt.close()
    
    # === График 3: Ускорение ===
    # Считаем ускорение (Speedup) = T(1) / T(p)
    if 1 in cores_list and len(cores_list) > 1:
        fig, ax = plt.subplots()
        # Построим ускорение от количества ядер для каждого размера N
        
        # Реорганизуем данные: N -> dict(core: time)
        times_by_n = {n: {} for n in sizes_list}
        for core in cores_list:
            for s, t in zip(data_by_core[core]['sizes'], data_by_core[core]['times']):
                times_by_n[s][core] = t
                
        for i, n in enumerate(sizes_list):
            if 1 in times_by_n[n]:
                t1 = times_by_n[n][1]
                speedups = []
                cores_for_n = []
                for core in cores_list:
                    if core in times_by_n[n]:
                        cores_for_n.append(core)
                        speedups.append(t1 / times_by_n[n][core])
                
                ax.plot(cores_for_n, speedups, colors[i % len(colors)], linewidth=2, markersize=8, label=f'N = {n}')
        
        # Теоретическое (идеальное) ускорение
        ax.plot(cores_list, cores_list, 'k--', linewidth=2, label='Идеальное ускорение')
        
        ax.set_xlabel('Количество ядер (процессов)')
        ax.set_ylabel('Ускорение')
        ax.set_title('Ускорение параллельного алгоритма (Speedup)')
        ax.set_xticks(cores_list)
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'graph_speedup.png'), dpi=150)
        print(f"  Сохранён: {output_dir}/graph_speedup.png")
        plt.close()

    # Таблица в консоль
    print("\n" + "=" * 80)
    print(f"{'N':>6} | {'Ядра':>4} | {'Время (сек)':>12} | {'GFLOP':>8} | {'GFLOP/s':>8} | {'Память (МБ)':>12}")
    print("-" * 80)
    for core in cores_list:
        sizes = data_by_core[core]['sizes']
        times = data_by_core[core]['times']
        gflops = data_by_core[core]['gflops']
        gflops_s = data_by_core[core]['gflops_s']
        memory = data_by_core[core]['memory']
        for i in range(len(sizes)):
            print(f"{sizes[i]:>6} | {core:>4} | {times[i]:>12.6f} | {gflops[i]:>8.3f} | {gflops_s[i]:>8.4f} | {memory[i]:>12.2f}")
    print("=" * 80)

if __name__ == "__main__":
    main()
# main.py
import argparse
import time
import random

from petri import parse_pnml
from reachability import bfs_reachability, fmt_marking, marking_to_bitmap
from deadlock_ilp import find_deadlock_with_ilp              # Task 4 (ILP)
from symbolic_bdd import build_reachability_bdd, is_marking_reachable_bdd  # Task 3 (BDD)
# Import task 5
from optimization import find_optimal_marking, complete_and_optimize_marking
def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--pnml", required=True, help="Name of file PNML")
    ap.add_argument(
        "-e",
        "--edges",
        action="store_true",
        help="display transitions between markings (explicit reachability edges)",
    )
    ap.add_argument(
        "--symbolic",
        action="store_true",
        help="run Task 3: symbolic reachability using BDD (count reachable markings)",
    )
    ap.add_argument(
        "--deadlock",
        action="store_true",
        help="run Task 4: ILP-based deadlock detection using BDD",
    )
    # Tham số cho Task 5
    ap.add_argument(
        "--optimize",
        action="store_true",
        help="run Task 5: Optimization over reachable markings",
    )
    args = ap.parse_args()

    # ===== Task 1 + Task 2: đọc PNML và BFS reachability 
    net = parse_pnml("./pnml/" + args.pnml)
    visited, edges, pred = bfs_reachability(net, keep_edges=args.edges)

    print(f"Number of places in the Petri net: {len(net.places)}")
    print(f"Initial marking: {fmt_marking(net.initial, net.places)}")
    print(f"Total number of reachable markings (explicit BFS): {len(visited)}")

    if args.edges:
        print("Transitions between markings:")
        for M, t, M2 in edges:
            print(
                f"{marking_to_bitmap(M, len(net.places))} -{t}-> {marking_to_bitmap(M2, len(net.places))}  "
                f"{fmt_marking(M, net.places)} -{t}-> {fmt_marking(M2, net.places)}"
            )

    # ===== Task 3: Symbolic reachability bằng BDD 
    bdd = R = curr_vars = None
    # Task 3 cần chạy nếu user yêu cầu symbolic, deadlock HOẶC optimize
    if args.symbolic or args.deadlock or args.optimize:
        print("\n[INFO] Building symbolic reachability BDD (Task 3)...")
        t0 = time.perf_counter()
        bdd, R, curr_vars = build_reachability_bdd(net)
        t1 = time.perf_counter()

        count_bdd = int(bdd.count(R, nvars=len(curr_vars)))
        print(f"Total number of reachable markings (BDD): {count_bdd}")
        print(f"BDD reachability time: {t1 - t0:.6f} seconds")

    # ===== Task 4: Deadlock detection (ILP + BDD) =====
    if args.deadlock:
        print("\n[INFO] Running ILP-based deadlock detection (Task 4)...")

        def is_reachable_marking(M: int) -> bool:
            return is_marking_reachable_bdd(M, bdd, R, curr_vars)

        dead_M, elapsed = find_deadlock_with_ilp(net, is_reachable_marking)

        if dead_M is None:
            print("[RESULT] No reachable deadlock found.")
        else:
            print(
                "[RESULT] Deadlock marking (bitmap):",
                marking_to_bitmap(dead_M, len(net.places)),
            )
            print(
                "[RESULT] Deadlock marking (places):",
                fmt_marking(dead_M, net.places),
            )
            print(f"[RESULT] ILP + BDD time: {elapsed:.6f} seconds")

   # ==== Task 5: Optimization over Reachable Markings ====
    if args.optimize:
        print("\n[INFO] Running Optimization over Reachable Markings (Task 5)...")
        
        # 1. Sinh trọng số ngẫu nhiên
        weights = {}
        print("Generated Objective Function Weights (c):")
        random.seed(42) 
        for p in net.places:
            w = random.randint(-5, 10)
            weights[p] = w
        print(", ".join([f"{k}:{v}" for k, v in weights.items()]))

        # 2. Gọi hàm tối ưu trên BDD
        t_opt_start = time.perf_counter()
        
        # Tìm đường đi lớn nhất trên các node ĐÃ XUẤT HIỆN trong BDD
        # Lưu ý: Hàm này trả về score dựa trên các biến có mặt trong path
        base_max_val, partial_marking = find_optimal_marking(R, weights)
        
        # 3. Tối ưu hóa các biến "Don't care" (không xuất hiện trong path BDD)
        if base_max_val == float('-inf'):
            print("[RESULT] No reachable marking found.")
        else:
            final_marking_dict, extra_score = complete_and_optimize_marking(
                partial_marking, net.places, weights
            )
            
            # Tổng điểm thực tế = Điểm trên path + Điểm từ các biến Don't care dương
            final_total_score = base_max_val + extra_score
            
            t_opt_end = time.perf_counter()

            # 4. Xuất kết quả
            print(f"[RESULT] Found Optimal Marking!")
            print(f"  Max Objective Value: {final_total_score}")
            
            # In ra marking dạng bitmap cho đẹp
            # Chuyển dict {p1:1, p2:0...} sang int bitmap
            final_bitmap_val = 0
            for p, val in final_marking_dict.items():
                if val == 1:
                    idx = net.place_index[p]
                    final_bitmap_val |= (1 << idx)
            
            print(f"  Marking (Bitmap): {marking_to_bitmap(final_bitmap_val, len(net.places))}")
            print(f"  Marking (Set): {fmt_marking(final_bitmap_val, net.places)}")
            
            # Kiểm chứng (Sanity Check)
            check_sum = sum(weights[p] * final_marking_dict[p] for p in net.places)
            print(f"  Verification Sum: {check_sum} (Matches? {check_sum == final_total_score})")
            
            print(f"[RESULT] Optimization time: {t_opt_end - t_opt_start:.6f} seconds")

if __name__ == "__main__":
    main()
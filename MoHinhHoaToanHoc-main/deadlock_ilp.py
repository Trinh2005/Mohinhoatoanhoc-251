# deadlock_ilp.py
import time
from typing import Callable, Optional, Tuple
import pulp  # đảm bảo đã: python -m pip install pulp

from petri import PetriNet
from reachability import fmt_marking


def build_deadlock_ilp_model(net: PetriNet):
    """
    Tạo ILP model cho dead marking:
      - Biến x_i ∈ {0,1} cho mỗi place i
      - Ràng buộc: với mỗi transition t, sum_{p in preset(t)} (1 - x_p) >= 1
        => không transition nào enabled
    Trả về: (model, dict x)
    """
    num_places = len(net.places)

    # Bài toán chỉ cần tìm nghiệm, không cần tối ưu gì → objective = 0
    model = pulp.LpProblem("DeadlockDetection", sense=pulp.LpMinimize)
    model += 0  # dummy objective

    # Biến nhị phân x_i cho từng place
    x = {
        i: pulp.LpVariable(f"x_{i}", lowBound=0, upBound=1, cat="Binary")
        for i in range(num_places)
    }

    # Ràng buộc dead-marking: không transition nào enabled
    for t in net.transitions:
        # preset(t): các place có bit = 1 trong pre_mask
        preset_indices = [
            i for i in range(num_places) if (t.pre_mask >> i) & 1
        ]

        if preset_indices:
            # sum_{p in preset(t)} (1 - x_p) >= 1
            # => Ít nhất 1 input place KHÔNG có token => t không enabled
            model += (
                pulp.lpSum(1 - x[i] for i in preset_indices) >= 1,
                f"dead_t_{t.id}",
            )
        else:
            # preset rỗng → t luôn enabled → không thể có dead marking
            # Thêm constraint 0 >= 1 để model luôn UNSAT nếu có transition như vậy
            model += 0 >= 1, f"no_deadlock_due_to_{t.id}"

    return model, x


def find_deadlock_with_ilp(
    net: PetriNet,
    is_reachable: Callable[[int], bool],
    time_limit: Optional[int] = None,
    max_iter: int = 1000,
) -> Tuple[Optional[int], float]:
    """
    Tìm một deadlock (dead marking reachable) bằng ILP + BDD/Reachability.

    Args:
        net: Petri net đã parse từ PNML
        is_reachable: hàm kiểm tra 1 marking (bitmask) có nằm trong Reach(M0) không.
                      - Sau này Task 3 sẽ truyền vào hàm dùng BDD.
                      - Hiện tại có thể dùng: lambda M: M in visited (BFS).
        time_limit: giới hạn thời gian cho mỗi lần solve ILP (giây) – có thể None.
        max_iter: số lần lặp tối đa (đề phòng lỗi logic).

    Returns:
        (dead_marking, elapsed_time)
        - dead_marking: int (bitmask) nếu tìm được, hoặc None nếu không có deadlock reachable.
        - elapsed_time: thời gian chạy (giây).
    """
    num_places = len(net.places)
    model, x = build_deadlock_ilp_model(net)

    start = time.perf_counter()
    iteration = 0

    while True:
        iteration += 1
        if iteration > max_iter:
            elapsed = time.perf_counter() - start
            print(f"[WARN] Vượt quá {max_iter} vòng lặp ILP, dừng.")
            return None, elapsed

        # Chọn solver CBC mặc định của PuLP
        if time_limit is not None:
            solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit)
        else:
            solver = pulp.PULP_CBC_CMD(msg=False)

        model.solve(solver)
        status_str = pulp.LpStatus.get(model.status, "Unknown")

        if status_str != "Optimal":
            # Không còn nghiệm nào thỏa ràng buộc dead-mark + các blocking constraints
            elapsed = time.perf_counter() - start
            print(f"[INFO] ILP status = {status_str} -> không tìm thấy dead marking nào.")
            return None, elapsed

        # Đọc nghiệm x_i để dựng marking M (bitmask)
        M = 0
        for i in range(num_places):
            val = x[i].varValue
            bit = 1 if val is not None and val > 0.5 else 0
            if bit == 1:
                M |= (1 << i)

        # Kiểm tra reachable bằng BDD hoặc BFS (tùy is_reachable)
        if is_reachable(M):
            elapsed = time.perf_counter() - start
            print("[INFO] Found reachable dead marking!")
            print("  Bitmap  :", format(M, f"0{num_places}b"))
            print("  Marking :", fmt_marking(M, net.places))
            print("  Time    :", elapsed, "seconds")
            return M, elapsed

        # Nếu M không reachable:
        # Thêm constraint blocking để cấm lại đúng marking này:
        #   sum_{i: bit=1} x_i + sum_{i: bit=0} (1 - x_i) <= num_places - 1
        # => Ít nhất 1 bit phải khác đi
        block_constraint = (
            pulp.lpSum(
                x[i] if ((M >> i) & 1) == 1 else (1 - x[i])
                for i in range(num_places)
            )
            <= num_places - 1
        )
        model += block_constraint, f"block_{iteration}"
        # quay lại vòng while, solve với constraint mới
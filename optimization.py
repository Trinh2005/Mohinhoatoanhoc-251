# optimization.py
import re

def get_original_name(bdd_var_name):
    # Regex tìm pattern: v[số]_[tên_gốc]
    match = re.match(r"v\d+_(.+)", bdd_var_name)
    if match:
        return match.group(1)
    return bdd_var_name

def find_optimal_marking(bdd_node, weights, memo=None):
    """
    Tìm marking tối ưu trên cây BDD (Max Weight Path).
    """
    if memo is None:
        memo = {}

    # 1. Base Cases: Kiểm tra node terminal (True/False)
    # Thư viện dd: node False là 0, node True là 1
    # Lưu ý: so sánh (bdd_node == 1) đôi khi an toàn hơn int(bdd_node) tùy phiên bản
    if bdd_node == 0: 
        return float('-inf'), {} # Dead end
    if bdd_node == 1:
        return 0, {} # Đích đến

    # 2. Check Cache
    # Với thư viện dd, ta dùng str(bdd_node) hoặc id(bdd_node) làm key
    node_id = id(bdd_node)
    if node_id in memo:
        return memo[node_id]

    # 3. Lấy thông tin biến và trọng số
    bdd_var = str(bdd_node.var) # VD: 'v0_p1'
    original_place_name = get_original_name(bdd_var) # VD: 'p1'
    
    # Lấy trọng số, nếu không tìm thấy thì mặc định là 0
    w = weights.get(original_place_name, 0)

    # 4. Đệ quy
    # Nhánh Low (Place = 0): Không cộng trọng số
    score_low, path_low = find_optimal_marking(bdd_node.low, weights, memo)
    
    # Nhánh High (Place = 1): CỘNG trọng số
    score_high, path_high = find_optimal_marking(bdd_node.high, weights, memo)
    
    if score_high != float('-inf'):
        score_high += w

    # 5. So sánh
    if score_high >= score_low:
        best_score = score_high
        best_path = path_high.copy()
        best_path[original_place_name] = 1
    else:
        best_score = score_low
        best_path = path_low.copy()
        best_path[original_place_name] = 0

    # 6. Lưu cache
    memo[node_id] = (best_score, best_path)
    return best_score, best_path

def complete_and_optimize_marking(partial_marking, places, weights):
    """
    Điền các biến thiếu (Don't care):
    - Nếu weight > 0 -> điền 1 (để tăng max score)
    - Nếu weight <= 0 -> điền 0
    Cập nhật lại tổng giá trị tối ưu.
    """
    full_marking = {}
    extra_score = 0
    
    for p in places:
        if p in partial_marking:
            full_marking[p] = partial_marking[p]
        else:
            # Xử lý Don't care
            w = weights.get(p, 0)
            if w > 0:
                full_marking[p] = 1
                extra_score += w # Cộng thêm điểm vì ta chọn 1
            else:
                full_marking[p] = 0
                # Không cộng điểm vì chọn 0
                
    return full_marking, extra_score
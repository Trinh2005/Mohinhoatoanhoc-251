# reachability.py
from collections import deque
from typing import Dict, Tuple, List, Iterable
from petri import PetriNet, Transition

def is_enabled(M: int, t: Transition) -> bool:
    """Kiểm tra transition t có enabled tại marking M không
    
    Args:
        M: current marking (bitmask)
        t: transition cần kiểm tra
    
    Returns:
        True nếu M có token ở TẤT CẢ input places của t
    """
    # Kiểm tra: M có CHỨA TẤT CẢ các bits trong pre_mask của t không?
    # Ví dụ: 
    # - M = 001 (chỉ P0 có token)
    # - t.pre_mask = 011 (cần P0 và P1)
    # -> M & t.pre_mask = 001 ≠ 011 → NOT enabled
    return (M & t.pre_mask) == t.pre_mask

def fire(M: int, t: Transition) -> int:
    """Kích hoạt transition t tại marking M và trả về marking mới
    
    Args:
        M: current marking (bitmask)
        t: transition cần kích hoạt
    
    Returns:
        new marking sau khi kích hoạt t
    """
    # Thực hiện 2 bước:
    # 1. (M & ~t.pre_mask): XÓA token từ input places (bitwise AND với NOT pre_mask)
    # 2. | t.post_mask: THÊM token vào output places (bitwise OR với post_mask)
    
    # Ví dụ:
    # M = 001, t.pre_mask = 001, t.post_mask = 010
    # B1: 001 & ~001 = 001 & 110 = 000
    # B2: 000 | 010 = 010
    return (M & ~t.pre_mask) | t.post_mask

def bfs_reachability(net: PetriNet, keep_edges: bool = False):
    """Tính toán tất cả reachable markings bằng BFS
    
    Args:
        net: PetriNet object
        keep_edges: có lưu thông tin về các cạnh (transitions) không
    
    Returns:
        visited: set của tất cả reachable markings
        edges: list các cạnh (M1, transition_id, M2) nếu keep_edges=True
        pred: dictionary mapping marking -> (previous_marking, transition_id)
    """
    # Marking bắt đầu
    start = net.initial
    
    # Tập các markings đã visited (để tránh duplicate)
    visited: set[int] = {start}
    
    # Queue cho BFS
    q = deque([start])

    # (TÙY CHỌN) Lưu thông tin về đồ thị reachability
    edges: List[Tuple[int, str, int]] = []  # (from_marking, transition_id, to_marking)
    pred: Dict[int, Tuple[int, str]] = {}   # marking -> (previous_marking, transition_id)

    # BFS loop
    while q:
        # Lấy marking đầu queue
        M = q.popleft()
        
        # Thử tất cả transitions
        for t in net.transitions:
            # Kiểm tra transition có enabled tại marking hiện tại không
            if is_enabled(M, t):
                # Kích hoạt transition để được marking mới
                M2 = fire(M, t)
                
                # Lưu thông tin cạnh nếu được yêu cầu
                if keep_edges:
                    edges.append((M, t.id, M2))
                
                # Nếu marking mới chưa được visited
                if M2 not in visited:
                    # Đánh dấu đã visited và thêm vào queue
                    visited.add(M2)
                    pred[M2] = (M, t.id)  # Lưu đường đi
                    q.append(M2)

    return visited, edges, pred

def fmt_marking(M: int, place_names: List[str]) -> str:
    """Định dạng marking bitmask thành string dễ đọc
    
    Args:
        M: marking (bitmask)
        place_names: danh sách tên places
    
    Returns:
        String dạng {p1, p3, p5} chỉ các places có token
    """
    # Tìm tất cả places có token
    bits = []
    for i, p in enumerate(place_names):
        # Kiểm tra bit thứ i có được set không
        if M & (1 << i):
            bits.append(p)
    
    # Trả về dạng {p1, p2, p3}
    return "{" + ", ".join(bits) + "}"

def marking_to_bitmap(M: int, num_places: int) -> str:
    """Chuyển marking sang string bitmap"""
    return format(M, f'0{num_places}b')
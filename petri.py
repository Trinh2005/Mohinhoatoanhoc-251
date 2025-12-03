# petri.py
from dataclasses import dataclass
from typing import List, Dict, Tuple
import xml.etree.ElementTree as ET

# Định nghĩa cấu trúc dữ liệu cho Transition
@dataclass
class Transition:
    id: str
    name: str
    pre_mask: int    # Bitmask đại diện cho input places (places cần token để kích hoạt)
    post_mask: int   # Bitmask đại diện cho output places (places nhận token sau kích hoạt)

# Định nghĩa cấu trúc dữ liệu cho Petri Net
@dataclass
class PetriNet:
    places: List[str]              # Danh sách ID của các places
    place_index: Dict[str, int]    # Ánh xạ từ place ID -> chỉ số (index)
    transitions: List[Transition]  # Danh sách các transitions
    initial: int                   # Marking ban đầu được biểu diễn dưới dạng bitmask

def _lname(tag: str) -> str:
    """Hàm helper để lấy local name từ XML tag (bỏ qua namespace)
    Ví dụ: '{http://www.pnml.org}place' -> 'place'"""
    return tag.split('}')[-1]

def parse_pnml(path: str) -> PetriNet:
    """Parser chính để đọc file PNML và chuyển thành đối tượng PetriNet"""
    
    # Đọc và parse file XML
    tree = ET.parse(path)
    root = tree.getroot()

    # 1) Tìm phần tử <net> trong file PNML
    # Dùng generator expression để tìm phần tử net đầu tiên
    net = next((e for e in root.iter() if _lname(e.tag) == "net"), None)
    if net is None:
        raise ValueError("PNML thiếu <net>.")

    # 2) Đọc tất cả places và transitions để xây dựng danh sách node
    place_elems: Dict[str, ET.Element] = {}  # Lưu place elements theo ID
    trans_elems: Dict[str, ET.Element] = {}  # Lưu transition elements theo ID
    
    # Duyệt qua tất cả các phần tử trong net
    for e in net.iter():
        ln = _lname(e.tag)
        if ln == "place":
            pid = e.attrib["id"]
            place_elems[pid] = e
        elif ln == "transition":
            tid = e.attrib["id"]
            trans_elems[tid] = e

    # Validation: kiểm tra có ít nhất một place và transition
    if not place_elems:
        raise ValueError("Không tìm thấy place nào.")
    if not trans_elems:
        raise ValueError("Không tìm thấy transition nào.")

    # 3) Chỉ số hóa places - gán mỗi place một index duy nhất
    # Ví dụ: ['p1', 'p2', 'p3'] -> {'p1': 0, 'p2': 1, 'p3': 2}
    places = list(place_elems.keys())
    place_index = {p: i for i, p in enumerate(places)}

    # 4) Xây dựng initial marking dưới dạng bitmask
    # Mỗi place được biểu diễn bằng 1 bit: 1 có token, 0 không có token
    initial = 0
    for pid, pe in place_elems.items():
        m = 0  # Mặc định là 0 token
        for child in pe:
            if _lname(child.tag) == "initialMarking":
                # Tìm phần tử <text> bên trong initialMarking
                for c2 in child.iter():
                    if _lname(c2.tag) == "text":
                        txt = (c2.text or "").strip()
                        if txt:
                            m = int(txt)  # Chuyển text thành số
                        break
        # Kiểm tra Petri net 1-safe: mỗi place chỉ có 0 hoặc 1 token
        if m not in (0, 1):
            raise ValueError(f"Initial marking của place {pid} không phải 0/1 (1-safe).")
        if m == 1:
            # Set bit tương ứng với place này trong bitmask
            initial |= (1 << place_index[pid])

    # 5) Khởi tạo các Transition (chưa có pre_mask và post_mask)
    transitions: Dict[str, Transition] = {}
    for tid, te in trans_elems.items():
        # Mặc định dùng ID làm name, nhưng nếu có phần tử <name> thì dùng name đó
        name = tid
        for child in te:
            if _lname(child.tag) == "name":
                for c2 in child.iter():
                    if _lname(c2.tag) == "text" and (c2.text or "").strip():
                        name = c2.text.strip()
                        break
        # Tạo transition với pre_mask và post_mask = 0 (sẽ được điền từ arcs)
        transitions[tid] = Transition(id=tid, name=name, pre_mask=0, post_mask=0)

    # 6) Xử lý arcs để xây dựng pre_mask và post_mask cho transitions
    for e in net.iter():
        if _lname(e.tag) != "arc": 
            continue
            
        src = e.attrib["source"]  # ID của node nguồn
        tgt = e.attrib["target"]  # ID của node đích

        # Đọc trọng số của arc (weight), mặc định là 1
        weight = 1
        for child in e.iter():
            if _lname(child.tag) == "inscription":
                for c2 in child.iter():
                    if _lname(c2.tag) == "text":
                        txt = (c2.text or "").strip()
                        if txt:
                            weight = int(txt)
                        break
        
        # Kiểm tra weight = 1 (yêu cầu cho 1-safe Petri net)
        if weight != 1:
            raise ValueError(f"Arc {e.attrib.get('id','(no-id)')} có weight={weight} (không hỗ trợ, 1-safe).")

        # Xác định loại của source và target
        is_src_place = src in place_elems
        is_src_trans = src in trans_elems
        is_tgt_place = tgt in place_elems
        is_tgt_trans = tgt in trans_elems

        # Validation: kiểm tra nodes tồn tại
        if not (is_src_place or is_src_trans) or not (is_tgt_place or is_tgt_trans):
            raise ValueError(f"Arc tham chiếu node không tồn tại: {src} -> {tgt}")

        # Xử lý các loại arc hợp lệ:
        if is_src_place and is_tgt_trans:
            # Arc từ Place -> Transition: thêm vào pre_mask của transition
            t = transitions[tgt]  # Lấy transition đích
            t.pre_mask |= (1 << place_index[src])  # Set bit tương ứng với place
        elif is_src_trans and is_tgt_place:
            # Arc từ Transition -> Place: thêm vào post_mask của transition  
            t = transitions[src]  # Lấy transition nguồn
            t.post_mask |= (1 << place_index[tgt])  # Set bit tương ứng với place
        else:
            # Arc không hợp lệ: Place->Place hoặc Transition->Transition
            raise ValueError(f"Arc không hợp lệ (P->P hoặc T->T): {src} -> {tgt}")

    # Trả về đối tượng PetriNet hoàn chỉnh
    return PetriNet(
        places=places,
        place_index=place_index,
        transitions=list(transitions.values()),
        initial=initial,
    )
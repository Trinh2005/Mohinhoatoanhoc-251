## **1. Cấu trúc thư mục**

```
btl/
│── main.py               # File chạy chính
│── petri.py              # Parser PNML → PetriNet object
│── reachability.py       # BFS để sinh reachable markings
│── README.md           
│
├── pnml/                 # Chứa các file .pnml
│      ├── simple.pnml
│      └── ...
```

---

## **2. Cách chạy chương trình**

### **Lệnh cơ bản**

```bash
python main.py --pnml simple.pnml
```

### **In thêm các cạnh (transition firing edges)**

```bash
python main.py --pnml simple.pnml -e
```

---

## **3. Mô tả các hàm**

---

# **3.1. Hàm `parse_pnml(path: str) -> PetriNet`**

## **Chức năng**

Đọc file PNML và chuyển toàn bộ mô hình Petri net thành đối tượng `PetriNet` dùng trong chương trình.

---

## **INPUT**

| Tham số | Kiểu  | Ý nghĩa                                             |
| ------- | ----- | --------------------------------------------------- |
| `path`  | `str` | Đường dẫn file PNML (ví dụ `"./pnml/simple.pnml"`). |

---

## **OUTPUT – Đối tượng `PetriNet`**

```python
@dataclass
class PetriNet:
    places: List[str]
    place_index: Dict[str, int]
    transitions: List[Transition]
    initial: int
```

### **1) `places: List[str]`**

Danh sách ID của tất cả place trong PNML.
VD:

```python
['p1', 'p2', 'p3']
```

### **2) `place_index: Dict[str, int]`**

Ánh xạ ID → index dùng bitmask.

```
p1 → 0 (bit thứ nhất)
p2 → 1 (bit thứ hai)
p3 → 2 (bit thứ ba)
```

### **3) `transitions: List[Transition]`**

Một `Transition` gồm:

```python
Transition(
    id="t1",
    name="T1",
    pre_mask=0b001,     # Những place phải có token để kích hoạt
    post_mask=0b010     # Những place sẽ nhận token sau khi kích hoạt
)
```

### **4) `initial: int`**

Marking ban đầu dạng bitmask.

Ví dụ marking `{p1, p3}`:

```
initial = 5 -> 5 = 0b101  → {p3,p1}
```

---

## **💡 Ràng buộc được kiểm tra**

* Tất cả place phải có initial marking 0 hoặc 1 (1-safe).
* Arc phải là Place→Transition hoặc Transition→Place.
* Weight của arc phải = 1.

---

---

# **3.2. Hàm `bfs_reachability(net: PetriNet, keep_edges=False)`**

## **Chức năng**

Sinh tất cả reachable markings của mạng Petri bằng BFS.

---

## **INPUT**

| Tham số      | Kiểu       | Ý nghĩa                                           |
| ------------ | ---------- | ------------------------------------------------- |
| `net`        | `PetriNet` | Mạng Petri sau khi parse                          |
| `keep_edges` | `bool`     | Nếu True → lưu danh sách cạnh (M, transition, M') |

---

## **OUTPUT**

```python
visited, edges, pred
```

### **1) `visited: set[int]`**

Tập tất cả marking reachable (dạng bitmask).

VD:

```
{0b001, 0b010, 0b100}
```

---

### **2) `edges: List[Tuple[int, str, int]]` (nếu keep_edges=True)**

Mỗi phần tử có dạng:

```
(Mark_before, transition_id, Mark_after)
```

Ví dụ:

```
(0b001, 't1', 0b010)
```

---

### **3) `pred: Dict[int, Tuple[int, str]]`**

Dùng để truy vết đường đi từ initial marking.

Một phần tử có dạng:

```
M2 → (M1, transition_id)
```

---

---

# **4. Output mẫu khi chạy chương trình**

Ví dụ:

```
Number of places in the Petri net: 3
Initial marking: {p0}
Total number of reachable markings: 3
```

Khi bật `-e`:

```
Number of places in the Petri net: 3
Initial marking: {p0}
Total number of reachable markings: 3
Transitions between markings:
001 -t1-> 010  {p0} -t1-> {p1}
010 -t2-> 100  {p1} -t2-> {p2}
```
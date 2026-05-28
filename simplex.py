import numpy as np

class SimplexSolver:
    def __init__(self, c, maximize=True, A=None, b=None, constraint_types=None, bounds=None):
        """
        Khởi tạo bài toán quy hoạch tuyến tính.
        :param c: Hệ số hàm mục tiêu.
        :param maximize: True nếu là bài toán Max, False nếu là bài toán Min.
        :param A: Ma trận hệ số của các ràng buộc.
        :param b: Cột hệ số tự do.
        :param constraint_types: Danh sách các loại ràng buộc ('<=', '>=', '=').
        :param bounds: Danh sách tuple xác định miền giá trị của biến. 
                       (0, None) là >= 0, (None, 0) là <= 0, (None, None) là tuỳ ý.
        """
        self.c = np.array(c, dtype=float)
        self.maximize = maximize
        self.A = np.array(A, dtype=float) if A is not None else np.empty((0, len(c)))
        self.b = np.array(b, dtype=float) if b is not None else np.empty(0)
        self.constraint_types = constraint_types if constraint_types else []
        self.bounds = bounds if bounds else [(0, None)] * len(self.c)
        
        self.m = len(self.b)
        self.n = len(self.c)
        
        self._build_initial_system()
        
    def _build_initial_system(self):
        std_var_names = []
        c_std = []
        self.orig_to_std = []
        
        # 1. Chuyển đổi các biến về dạng không âm
        for j in range(self.n):
            bound = self.bounds[j]
            if bound == (0, None):
                std_var_names.append(f"x{j+1}")
                c_std.append(self.c[j])
                self.orig_to_std.append([len(std_var_names)-1])
            elif bound == (None, 0):
                std_var_names.append(f"x{j+1}'")
                c_std.append(-self.c[j])
                self.orig_to_std.append([len(std_var_names)-1])
            else: # (None, None)
                std_var_names.append(f"u{j+1}")
                std_var_names.append(f"v{j+1}")
                c_std.append(self.c[j])
                c_std.append(-self.c[j])
                self.orig_to_std.append([len(std_var_names)-2, len(std_var_names)-1])
                
        num_std_vars = len(std_var_names)
        A_std = np.zeros((self.m, num_std_vars))
        
        for j in range(self.n):
            bound = self.bounds[j]
            cols = self.orig_to_std[j]
            if bound == (0, None):
                A_std[:, cols[0]] = self.A[:, j]
            elif bound == (None, 0):
                A_std[:, cols[0]] = -self.A[:, j]
            else:
                A_std[:, cols[0]] = self.A[:, j]
                A_std[:, cols[1]] = -self.A[:, j]

        b_std = np.copy(self.b)
        c_types = list(self.constraint_types)
        
        # 2. Đảm bảo b >= 0
        for i in range(self.m):
            if b_std[i] < 0:
                b_std[i] = -b_std[i]
                A_std[i, :] = -A_std[i, :]
                if c_types[i] == '<=':
                    c_types[i] = '>='
                elif c_types[i] == '>=':
                    c_types[i] = '<='

        self.B = [] # Lưu index biến cơ sở
        
        # Đếm biến bù/thặng dư và biến giả
        num_slacks = sum(1 for t in c_types if t in ['<=', '>='])
        A_slack = np.zeros((self.m, num_slacks))
        
        num_arts = sum(1 for t in c_types if t in ['>=', '='])
        A_art = np.zeros((self.m, num_arts))
        
        curr_slack = 0
        curr_art = 0
        
        art_idx_start = num_std_vars + num_slacks
        
        slack_names = []
        art_names = []
        
        # 3. Thêm biến bù/thặng dư và biến giả
        for i in range(self.m):
            if c_types[i] == '<=':
                A_slack[i, curr_slack] = 1
                slack_names.append(f"s{i+1}")
                self.B.append(num_std_vars + curr_slack)
                curr_slack += 1
            elif c_types[i] == '>=':
                A_slack[i, curr_slack] = -1
                slack_names.append(f"s{i+1}")
                curr_slack += 1
                A_art[i, curr_art] = 1
                art_names.append(f"a{i+1}")
                self.B.append(art_idx_start + curr_art)
                curr_art += 1
            elif c_types[i] == '=':
                A_art[i, curr_art] = 1
                art_names.append(f"a{i+1}")
                self.B.append(art_idx_start + curr_art)
                curr_art += 1
                
        self.var_names = list(std_var_names) + slack_names + art_names
        self.num_vars = len(self.var_names)
        self.num_arts = num_arts
        
        A_full = np.hstack([A_std, A_slack, A_art])
        b_full = b_std
        
        # Khởi tạo hàm mục tiêu Z
        c_full = np.zeros(self.num_vars)
        c_full[:num_std_vars] = c_std
        if not self.maximize:
            c_full = -c_full
            
        # Tạo bảng Simplex Tableau
        # Row 0: Hàm mục tiêu W (Pha 1)
        # Row 1: Hàm mục tiêu Z (Pha 2)
        # Rows 2..m+1: Các ràng buộc
        self.tableau = np.zeros((self.m + 2, self.num_vars + 1))
        
        self.tableau[2:, :self.num_vars] = A_full
        self.tableau[2:, -1] = b_full
        self.tableau[1, :self.num_vars] = -c_full
        
        # Thiết lập hàm mục tiêu Pha 1: W = - sum a_i => W + sum a_i = 0
        if self.num_arts > 0:
            for i in range(self.m):
                if c_types[i] in ['>=', '=']:
                    # art_col là biến cơ sở a_i tại ràng buộc i
                    art_col = self.B[i]
                    self.tableau[0, art_col] = 1
                    # Biến đổi hàng để a_i không xuất hiện ở hàm mục tiêu W
                    self.tableau[0, :] -= self.tableau[2+i, :]

    def print_dictionary(self, step=0, phase=1):
        print(f"--- Bước {step} (Pha {phase}) ---")
        non_basic = [j for j in range(self.num_vars) if j not in self.B]
        
        # In các phương trình ràng buộc
        for i in range(self.m):
            b_var = self.var_names[self.B[i]]
            rhs = self.tableau[2+i, -1]
            eq = f"{b_var} = {rhs:g}"
            for j in non_basic:
                if phase == 2 and j >= self.num_vars - self.num_arts:
                    continue
                coef = -self.tableau[2+i, j]
                if abs(coef) > 1e-9:
                    if coef > 0:
                        eq += f" + {coef:g}*{self.var_names[j]}"
                    else:
                        eq += f" - {-coef:g}*{self.var_names[j]}"
            print(eq)
        
        # In hàm mục tiêu
        obj_name = "W" if phase == 1 else "Z"
        obj_row = 0 if phase == 1 else 1
        rhs = self.tableau[obj_row, -1]
        
        is_min_Z = (phase == 2 and not self.maximize)
        if is_min_Z:
            rhs = -rhs
            
        eq = f"{obj_name} = {rhs:g}"
        for j in non_basic:
            if phase == 2 and j >= self.num_vars - self.num_arts:
                continue
                
            coef = -self.tableau[obj_row, j]
            if is_min_Z:
                coef = -coef
                
            if abs(coef) > 1e-9:
                if coef > 0:
                    eq += f" + {coef:g}*{self.var_names[j]}"
                else:
                    eq += f" - {-coef:g}*{self.var_names[j]}"
        print(eq)
        print()

    def pivot(self, obj_row, allowed_vars):
        non_basic = sorted([j for j in allowed_vars if j not in self.B])
        enter_var = -1
        # Quy tắc Bland: Chọn biến vào có chỉ số nhỏ nhất mang hệ số âm trong hàng hàm mục tiêu
        for j in non_basic:
            if self.tableau[obj_row, j] < -1e-9:
                enter_var = j
                break
                
        if enter_var == -1:
            return False # Đã tối ưu
            
        leave_row = -1
        min_ratio = float('inf')
        
        # Tìm biến ra (Tỉ số nhỏ nhất không âm)
        for i in range(self.m):
            coef = self.tableau[2+i, enter_var]
            if coef > 1e-9:
                ratio = self.tableau[2+i, -1] / coef
                if ratio < min_ratio - 1e-9:
                    min_ratio = ratio
                    leave_row = i
                elif abs(ratio - min_ratio) <= 1e-9:
                    # Quy tắc Bland: Chọn biến ra có chỉ số nhỏ nhất nếu hoà tỉ số
                    if self.B[i] < self.B[leave_row]:
                        leave_row = i
                        
        if leave_row == -1:
            raise Exception("Bài toán không giới hạn (Unbounded)")
            
        # Thực hiện phép xoay (Pivot)
        pivot_coef = self.tableau[2+leave_row, enter_var]
        self.tableau[2+leave_row, :] /= pivot_coef
        
        for r in range(self.m + 2):
            if r != 2 + leave_row:
                factor = self.tableau[r, enter_var]
                self.tableau[r, :] -= factor * self.tableau[2+leave_row, :]
                
        self.B[leave_row] = enter_var
        return True

    def solve(self):
        step = 0
        
        # Pha 1
        if self.num_arts > 0:
            print("=== BẮT ĐẦU PHA 1 ===")
            self.print_dictionary(step, phase=1)
            while True:
                step += 1
                try:
                    res = self.pivot(obj_row=0, allowed_vars=range(self.num_vars))
                except Exception as e:
                    print(e)
                    return None
                if not res:
                    break
                self.print_dictionary(step, phase=1)
                
            if self.tableau[0, -1] < -1e-9:
                print("LỖI: Bài toán vô nghiệm (Infeasible).")
                return None
                
            print("=== KẾT THÚC PHA 1 ===")
            
        # Pha 2
        print("=== BẮT ĐẦU PHA 2 ===")
        allowed_vars = range(self.num_vars - self.num_arts)
        # Loại bỏ các biến giả khỏi việc xét đưa vào cơ sở
        step = 0
        self.print_dictionary(step, phase=2)
        while True:
            step += 1
            try:
                res = self.pivot(obj_row=1, allowed_vars=allowed_vars)
            except Exception as e:
                print(e)
                return None
            if not res:
                break
            self.print_dictionary(step, phase=2)
            
        print("=== TÌM ĐƯỢC NGHIỆM TỐI ƯU ===")
        return self.get_solution()

    def get_solution(self):
        vals = np.zeros(self.num_vars)
        for i in range(self.m):
            vals[self.B[i]] = self.tableau[2+i, -1]
            
        orig_vals = np.zeros(self.n)
        for j in range(self.n):
            bound = self.bounds[j]
            cols = self.orig_to_std[j]
            if bound == (0, None):
                orig_vals[j] = vals[cols[0]]
            elif bound == (None, 0):
                orig_vals[j] = -vals[cols[0]]
            else:
                orig_vals[j] = vals[cols[0]] - vals[cols[1]]
                
        opt_val = self.tableau[1, -1]
        if not self.maximize:
            opt_val = -opt_val
            
        return orig_vals, opt_val

if __name__ == "__main__":
    print("----- Test Case 1: Maximize chuẩn (Ví dụ a) -----")
    # f(x) = x_1 - x_2 + 2x_3 -> max
    # x_1 - 2x_2 + 2x_3 = 1
    # x_1 + x_2 - 3x_3 <= 4
    # x_1 - 3x_2 + x_3 >= 3
    # x_i >= 0
    c = [1, -1, 2]
    A = [[1, -2, 2],
         [1, 1, -3],
         [1, -3, 1]]
    b = [1, 4, 3]
    types = ['=', '<=', '>=']
    solver = SimplexSolver(c, maximize=True, A=A, b=b, constraint_types=types)
    res = solver.solve()
    if res:
        x, val = res
        print(f"Nghiệm tối ưu: {x}")
        print(f"Giá trị tối ưu: {val}")
        
    print("\n----- Test Case 2: Minimize với biến tuỳ ý (Ví dụ b) -----")
    # f(x) = x_1 + 3x_2 + 4x_3 -> min
    # x_1 + 2x_2 + x_3 <= 5
    # 2x_1 + 3x_2 + x_3 >= 6
    # x_1 tuỳ ý, x_2 >= 0, x_3 >= 0
    c = [1, 3, 4]
    A = [[1, 2, 1],
         [2, 3, 1]]
    b = [5, 6]
    types = ['<=', '>=']
    bounds = [(None, None), (0, None), (0, None)]
    solver2 = SimplexSolver(c, maximize=False, A=A, b=b, constraint_types=types, bounds=bounds)
    res2 = solver2.solve()
    if res2:
        x, val = res2
        print(f"Nghiệm tối ưu: {x}")
        print(f"Giá trị tối ưu: {val}")

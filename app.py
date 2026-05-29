# To deploy backend to sever

"""
app.py — Giao diện Web cho Hệ thống Giải Quy hoạch Tuyến tính (LP Solver)
Chạy bằng lệnh: streamlit run app.py
"""

import io
import contextlib
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Cấu hình trang (phải là lệnh Streamlit đầu tiên)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LP Solver",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CSS tùy chỉnh — Light Theme rõ ràng, học thuật
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Nền & font chính */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #f7f9fc;
        font-family: 'Source Serif 4', 'Georgia', serif;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a2744;
        color: #e8edf5;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stCheckbox span,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #e8edf5 !important;
    }

    /* Tiêu đề chính */
    h1 {
        color: #1a2744;
        font-size: 2rem;
        letter-spacing: -0.5px;
        border-bottom: 3px solid #3a6bc4;
        padding-bottom: 0.4rem;
    }
    h2, h3 { color: #1a2744; }

    /* Card section */
    .section-card {
        background: #ffffff;
        border: 1px solid #d4dce8;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 8px rgba(26,39,68,0.06);
    }
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1a2744;
        border-left: 4px solid #3a6bc4;
        padding-left: 0.6rem;
        margin-bottom: 0.9rem;
        letter-spacing: 0.2px;
    }

    /* Nút Solve */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1a2744 0%, #3a6bc4 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-size: 1.05rem;
        font-weight: 700;
        padding: 0.55rem 2.5rem;
        letter-spacing: 0.5px;
        transition: opacity 0.2s;
    }
    div.stButton > button[kind="primary"]:hover { opacity: 0.88; }

    /* Kết quả */
    .result-box {
        background: #eef4ff;
        border: 1px solid #3a6bc4;
        border-radius: 10px;
        padding: 1.2rem 1.6rem;
        margin-top: 1rem;
    }
    .result-status-OPTIMAL    { color: #1a7a4a; font-weight: 800; font-size: 1.1rem; }
    .result-status-INFEASIBLE { color: #c0392b; font-weight: 800; font-size: 1.1rem; }
    .result-status-UNBOUNDED  { color: #e67e22; font-weight: 800; font-size: 1.1rem; }

    /* Bảng nghiệm */
    .sol-table { width: 100%; border-collapse: collapse; margin-top: 0.6rem; }
    .sol-table th { background: #1a2744; color: #fff; padding: 6px 12px; text-align: center; }
    .sol-table td { border: 1px solid #c5d0e0; padding: 5px 12px; text-align: center; }
    .sol-table tr:nth-child(even) td { background: #f0f4fb; }

    /* Warning */
    .warn-box {
        background: #fff8e1;
        border-left: 4px solid #f0a500;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        color: #7a5000;
        font-size: 0.93rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Import backend (sau khi page config)
# ──────────────────────────────────────────────────────────────────────────────
try:
    from backend.models import Variable, VariableSign, Constraint, ConstraintType, Objective, ObjectiveType, Problem
    from backend.cores import LPSolver, SolverMethod
    from backend.cores.geometry import GraphicalSolver
    BACKEND_OK = True
except ImportError as e:
    BACKEND_OK = False
    BACKEND_ERR = str(e)


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: Render LaTeX tên biến
# ══════════════════════════════════════════════════════════════════════════════
def var_latex(i: int) -> str:
    """Trả về chuỗi LaTeX $x_i$ (index bắt đầu từ 1)."""
    return f"$x_{{{i}}}$"


def var_name(i: int) -> str:
    """Trả về tên biến dạng chuỗi x1, x2, ..."""
    return f"x{i}"


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR: Cài đặt thuật toán
# ══════════════════════════════════════════════════════════════════════════════
def render_sidebar(n: int) -> dict:
    """
    Hiển thị sidebar cài đặt thuật toán.
    Trả về dict: {method, bland, verbose}
    """
    st.sidebar.markdown("## ⚙️ Cài đặt thuật toán")

    method_labels = ["Auto", "Simplex", "Graphical"]
    method_map = {
        "Auto":      SolverMethod.AUTO,
        "Simplex":   SolverMethod.SIMPLEX,
        "Graphical": SolverMethod.GRAPHICAL,
    }
    chosen_label = st.sidebar.selectbox(
        "Phương pháp giải",
        options=method_labels,
        help="Auto: tự chọn giữa Simplex và Two-Phase tùy cấu trúc bài toán.",
    )
    method = method_map[chosen_label]

    # Cảnh báo Graphical với n ≠ 2
    if method == SolverMethod.GRAPHICAL and n != 2:
        st.sidebar.markdown(
            '<div class="warn-box">⚠️ Phương pháp đồ thị chỉ áp dụng được khi bài toán có <b>đúng 2 biến</b>. '
            'Vui lòng đổi lại số biến hoặc chọn phương pháp khác.</div>',
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("---")
    bland   = st.sidebar.checkbox("Sử dụng luật Bland", value=False,
                                   help="Ngăn vòng lặp vô hạn (cycling) khi bài toán suy biến.")
    verbose = st.sidebar.checkbox("Hiển thị các bước chi tiết (Verbose)", value=False,
                                   help="Bắt output từ terminal và hiển thị lên trang web.")

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**Hướng dẫn nhanh**\n"
        "1. Nhập kích thước bài toán\n"
        "2. Điền hệ số hàm mục tiêu & ràng buộc\n"
        "3. Nhấn **Solve** để giải\n"
    )

    return {"method": method, "bland": bland, "verbose": verbose, "method_label": chosen_label}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Kích thước bài toán
# ══════════════════════════════════════════════════════════════════════════════
def render_size_section() -> tuple[int, int]:
    """Nhập số biến n và số ràng buộc m. Trả về (n, m)."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">① Kích thước bài toán</div>', unsafe_allow_html=True)

    c1, c2, _ = st.columns([1, 1, 3])
    with c1:
        n = st.number_input(
            "Số biến ($n$)", min_value=1, max_value=20, value=2, step=1,
        )
    with c2:
        m = st.number_input(
            "Số ràng buộc ($m$)", min_value=1, max_value=30, value=3, step=1,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    return int(n), int(m)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Cài đặt biến
# ══════════════════════════════════════════════════════════════════════════════
def render_variables_section(n: int) -> list[VariableSign]:
    """
    Cho phép chọn dấu cho từng biến.
    Trả về danh sách VariableSign theo thứ tự biến.
    """
    sign_label_map = {
        "≥ 0  (không âm)":   VariableSign.NON_NEGATIVE,
        "≤ 0  (không dương)": VariableSign.NON_POSITIVE,
        "Tự do":              VariableSign.FREE,
    }
    sign_labels = list(sign_label_map.keys())

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">② Điều kiện dấu của biến</div>', unsafe_allow_html=True)

    # Hiển thị tối đa 5 cột mỗi hàng
    cols_per_row = min(n, 5)
    rows = [list(range(i, min(i + cols_per_row, n))) for i in range(0, n, cols_per_row)]

    var_signs = []
    for row_indices in rows:
        cols = st.columns(len(row_indices))
        for col, idx in zip(cols, row_indices):
            with col:
                label = st.selectbox(
                    f"$x_{{{idx + 1}}}$",
                    options=sign_labels,
                    index=0,
                    key=f"var_sign_{idx}",
                )
                var_signs.append(sign_label_map[label])

    st.markdown("</div>", unsafe_allow_html=True)
    return var_signs


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Hàm mục tiêu
# ══════════════════════════════════════════════════════════════════════════════
def render_objective_section(n: int) -> tuple[ObjectiveType, list[float]]:
    """
    Nhập hàm mục tiêu.
    Trả về (ObjectiveType, list hệ số).
    """
    obj_map = {"Min": ObjectiveType.MIN, "Max": ObjectiveType.MAX}

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">③ Hàm mục tiêu</div>', unsafe_allow_html=True)

    obj_type_label = st.radio(
        "Hướng tối ưu", options=["Min", "Max"], horizontal=True, key="obj_type",
    )
    obj_type = obj_map[obj_type_label]

    st.markdown(f"**Hệ số hàm mục tiêu** &nbsp; ({obj_type_label} $z$)")

    # Nhập hệ số trên cùng một hàng
    cols = st.columns(n)
    coeffs = []
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"$x_{{{i + 1}}}$")
            c = st.number_input(
                label=f"c{i+1}",
                value=1.0,
                step=0.5,
                key=f"obj_c_{i}",
                label_visibility="collapsed",
            )
            coeffs.append(float(c))

    # Preview LaTeX
    _preview_objective(obj_type_label, coeffs, n)

    st.markdown("</div>", unsafe_allow_html=True)
    return obj_type, coeffs


def _preview_objective(obj_label: str, coeffs: list[float], n: int):
    """Hiển thị preview LaTeX hàm mục tiêu."""
    terms = []
    for i, c in enumerate(coeffs):
        if c == 0:
            continue
        if c == 1:
            term = f"x_{{{i+1}}}"
        elif c == -1:
            term = f"-x_{{{i+1}}}"
        else:
            coeff_str = _fmt_coeff(c)
            term = f"{coeff_str}x_{{{i+1}}}"
        terms.append(term)

    if not terms:
        expr = "0"
    else:
        expr = terms[0]
        for t in terms[1:]:
            if t.startswith("-"):
                expr += f" - {t[1:]}"
            else:
                expr += f" + {t}"

    st.latex(rf"\text{{{obj_label}}} \; z = {expr}")


def _fmt_coeff(c: float) -> str:
    """Định dạng hệ số: bỏ .0 nếu là số nguyên."""
    if c == int(c):
        return str(int(c))
    return str(c)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Các ràng buộc
# ══════════════════════════════════════════════════════════════════════════════
def render_constraints_section(n: int, m: int) -> list[tuple[list[float], ConstraintType, float]]:
    """
    Nhập m ràng buộc, mỗi ràng buộc gồm n hệ số, dấu, và RHS.
    Trả về list of (coeffs, ConstraintType, rhs).
    """
    ct_map = {
        "≤": ConstraintType.LE,
        "≥": ConstraintType.GE,
        "=": ConstraintType.EQ,
    }
    ct_labels = list(ct_map.keys())

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">④ Các ràng buộc</div>', unsafe_allow_html=True)

    # Header
    header_cols = st.columns([*([1] * n), 0.8, 1.2])
    for i in range(n):
        header_cols[i].markdown(f"<center>$x_{{{i+1}}}$</center>", unsafe_allow_html=True)
    header_cols[n].markdown("<center>Dấu</center>", unsafe_allow_html=True)
    header_cols[n + 1].markdown("<center>Vế phải ($b$)</center>", unsafe_allow_html=True)
    st.divider()

    constraints_raw = []
    for j in range(m):
        row_cols = st.columns([*([1] * n), 0.8, 1.2])
        row_coeffs = []

        for i in range(n):
            with row_cols[i]:
                a = st.number_input(
                    label=f"a{j+1}{i+1}",
                    value=0.0,
                    step=0.5,
                    key=f"con_{j}_{i}",
                    label_visibility="collapsed",
                )
                row_coeffs.append(float(a))

        with row_cols[n]:
            ct_label = st.selectbox(
                label=f"ct_type_{j}",
                options=ct_labels,
                key=f"ct_type_{j}",
                label_visibility="collapsed",
            )
            ct = ct_map[ct_label]

        with row_cols[n + 1]:
            rhs = st.number_input(
                label=f"rhs_{j}",
                value=0.0,
                step=0.5,
                key=f"rhs_{j}",
                label_visibility="collapsed",
            )

        constraints_raw.append((row_coeffs, ct, float(rhs)))

    st.markdown("</div>", unsafe_allow_html=True)
    return constraints_raw


# ══════════════════════════════════════════════════════════════════════════════
# CORE: Xây dựng Problem object và gọi solver
# ══════════════════════════════════════════════════════════════════════════════
def build_problem(
    n: int,
    var_signs: list[VariableSign],
    obj_type: ObjectiveType,
    obj_coeffs: list[float],
    constraints_raw: list[tuple[list[float], ConstraintType, float]],
) -> "Problem":
    """Tạo đối tượng Problem từ dữ liệu nhập."""
    variables = [
        Variable(name=var_name(i + 1), sign=var_signs[i])
        for i in range(n)
    ]

    obj_coeffs_dict = {var_name(i + 1): obj_coeffs[i] for i in range(n)}
    objective = Objective(objective_type=obj_type, coeffs=obj_coeffs_dict)

    constraints = []
    for row_coeffs, ct, rhs in constraints_raw:
        c_dict = {var_name(i + 1): row_coeffs[i] for i in range(n)}
        constraints.append(Constraint(coeffs=c_dict, constraint_type=ct, right_hand_side=rhs))

    return Problem(objective=objective, constraints=constraints, variables=variables)


def solve_problem(problem: "Problem", settings: dict) -> tuple[dict, str]:
    """
    Gọi LPSolver và bắt stdout (verbose logs).
    Trả về (result_dict, captured_stdout_str).
    """
    method  = settings["method"]
    bland   = settings["bland"]
    verbose = settings["verbose"]

    solver = LPSolver(problem=problem, method=method, bland=bland, verbose=verbose)

    stdout_buffer = io.StringIO()
    with contextlib.redirect_stdout(stdout_buffer):
        result = solver.solve()

    captured = stdout_buffer.getvalue()
    return result, captured


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: Hiển thị kết quả
# ══════════════════════════════════════════════════════════════════════════════
def render_result(
    result: dict,
    captured_stdout: str,
    problem: "Problem",
    settings: dict,
):
    """Hiển thị kết quả tối ưu, verbose log và đồ thị (nếu Graphical)."""
    st.markdown("---")
    st.markdown("## 📊 Kết quả")

    status = result.get("status", "UNKNOWN")

    # ── Trạng thái & nghiệm ──
    st.markdown('<div class="result-box">', unsafe_allow_html=True)

    status_class = {
        "OPTIMAL":    "result-status-OPTIMAL",
        "INFEASIBLE": "result-status-INFEASIBLE",
        "UNBOUNDED":  "result-status-UNBOUNDED",
    }.get(status, "result-status-OPTIMAL")

    status_vn = {
        "OPTIMAL":    "✅ TỐI ƯU (OPTIMAL)",
        "INFEASIBLE": "❌ VÔ NGHIỆM (INFEASIBLE)",
        "UNBOUNDED":  "∞ KHÔNG BỊ CHẶN (UNBOUNDED)",
    }.get(status, status)

    st.markdown(
        f'<p class="{status_class}">{status_vn}</p>',
        unsafe_allow_html=True,
    )

    if status == "OPTIMAL":
        opt_val = result.get("optimal_value", "N/A")
        st.markdown(f"**Giá trị tối ưu:** &nbsp; $z^* = {opt_val}$")

        solution = result.get("solution", {})
        if solution:
            st.markdown("**Nghiệm tối ưu:**")
            # Tạo bảng HTML
            headers = " ".join(f"<th>{k}</th>" for k in solution)
            values  = " ".join(f"<td>{v}</td>" for v in solution.values())
            table_html = (
                f'<table class="sol-table"><thead><tr>{headers}</tr></thead>'
                f"<tbody><tr>{values}</tr></tbody></table>"
            )
            st.markdown(table_html, unsafe_allow_html=True)

            # Hiển thị LaTeX nghiệm
            sol_parts = [f"{k} = {v}" for k, v in solution.items()]
            st.latex(r",\quad ".join(sol_parts))

    elif status == "INFEASIBLE":
        st.info("Bài toán không có miền chấp nhận được (vô nghiệm).")
    elif status == "UNBOUNDED":
        st.info("Hàm mục tiêu không bị chặn — bài toán không có nghiệm hữu hạn.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Verbose log ──
    if settings["verbose"] and captured_stdout.strip():
        with st.expander("📋 Xem các bước chạy chi tiết (Verbose)"):
            st.code(captured_stdout, language="text")

    # ── Đồ thị Graphical ──
    if settings["method"] == SolverMethod.GRAPHICAL and status == "OPTIMAL":
        st.markdown("### 📈 Đồ thị vùng khả thi (Graphical Method)")
        try:
            graphical_solver = GraphicalSolver(problem, verbose=False)
            fig = graphical_solver.plot_feasible_region(result)
            if fig is not None:
                st.pyplot(fig)
            else:
                st.warning(
                    "Không thể vẽ đồ thị. Hãy đảm bảo rằng hàm `plot_feasible_region` "
                    "đã được sửa để trả về `fig` thay vì gọi `plt.show()`."
                )
        except Exception as e:
            st.error(f"Lỗi khi vẽ đồ thị: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.markdown("# 📐 Linear Programming Solver")
    st.markdown(
        "Nhập bài toán Quy hoạch Tuyến tính theo từng bước, "
        "sau đó nhấn **Solve** để xem kết quả."
    )

    # ── Kiểm tra backend ──
    if not BACKEND_OK:
        st.error(
            f"⚠️ Không thể import backend: `{BACKEND_ERR}`\n\n"
            "Hãy đảm bảo bạn đang chạy `streamlit run app.py` từ thư mục gốc của dự án."
        )
        return

    # ── Bước 1: Kích thước ──
    n, m = render_size_section()

    # ── Sidebar (cần n để kiểm tra Graphical) ──
    settings = render_sidebar(n)

    # ── Cảnh báo chặn nếu Graphical & n ≠ 2 ──
    graphical_blocked = (settings["method"] == SolverMethod.GRAPHICAL and n != 2)

    # ── Bước 2: Biến ──
    var_signs = render_variables_section(n)

    # ── Bước 3: Hàm mục tiêu ──
    obj_type, obj_coeffs = render_objective_section(n)

    # ── Bước 4: Ràng buộc ──
    constraints_raw = render_constraints_section(n, m)

    # ── Nút Solve ──
    st.markdown("")
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        solve_clicked = st.button("🚀 Solve", type="primary", use_container_width=True)

    if solve_clicked:
        if graphical_blocked:
            st.error(
                "❌ Phương pháp đồ thị yêu cầu **đúng 2 biến**. "
                f"Bài toán hiện có {n} biến. "
                "Vui lòng đổi số biến hoặc chọn phương pháp khác trong Sidebar."
            )
            return

        with st.spinner("Đang giải bài toán..."):
            try:
                problem = build_problem(n, var_signs, obj_type, obj_coeffs, constraints_raw)
                result, captured = solve_problem(problem, settings)
                render_result(result, captured, problem, settings)
            except ValueError as ve:
                st.error(f"❌ Lỗi cấu hình: {ve}")
            except Exception as e:
                st.error(f"❌ Đã xảy ra lỗi không mong đợi: {e}")
                raise e  # để xem traceback trong terminal khi debug


if __name__ == "__main__":
    main()
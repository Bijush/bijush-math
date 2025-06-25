from flask import Flask, render_template, request
from sympy import symbols, Eq, solve, sympify, latex, expand, factor
import matplotlib.pyplot as plt
import numpy as np
import os
import re

app = Flask(__name__)

# Auto-correct expression formatting
def preprocess_expression(expr):
    expr = expr.replace('√', 'sqrt')  # Replace √ with sqrt
    expr = re.sub(r'(\d)([a-zA-Z\(])', r'\1*\2', expr)  # 2x → 2*x
    expr = re.sub(r'(\))(\w)', r'\1*\2', expr)          # )x → )*x
    expr = re.sub(r'(\d)(sqrt)', r'\1*sqrt', expr)      # 2sqrt → 2*sqrt
    return expr

@app.route('/', methods=['GET', 'POST'])
def index():
    steps = ''
    expression = ''
    if request.method == 'POST':
        input_text = request.form['equation']
        try:
            exprs = [preprocess_expression(e.strip()) for e in input_text.split(',')]
            equations = []
            all_symbols = set()

            for e in exprs:
                if '=' in e:
                    lhs, rhs = e.split('=', 1)
                    lhs_expr = sympify(lhs)
                    rhs_expr = sympify(rhs)
                    eq = Eq(lhs_expr, rhs_expr)
                else:
                    lhs_expr = sympify(e)
                    rhs_expr = 0
                    eq = Eq(lhs_expr, rhs_expr)

                if hasattr(lhs_expr, 'free_symbols'):
                    all_symbols.update(lhs_expr.free_symbols)
                if hasattr(rhs_expr, 'free_symbols'):
                    all_symbols.update(rhs_expr.free_symbols)

                equations.append(eq)

            expression = str(lhs_expr)

            steps += "<h3>Step 1: Given Equation(s)</h3>"
            for eq in equations:
                steps += f"<div>\\[{latex(eq)}\\]</div>"

            if len(equations) == 1 and len(all_symbols) == 1:
                var = list(all_symbols)[0]
                combined = equations[0].lhs - equations[0].rhs
                expanded = expand(combined)
                factored = factor(expanded)

                steps += "<h3>Step 2: Simplify & Factor</h3>"
                steps += f"<div>\\[{latex(combined)} = 0 \\Rightarrow {latex(expanded)} = 0\\]</div>"
                if factored != expanded:
                    steps += f"<div>\\[{latex(expanded)} = {latex(factored)}\\]</div>"

                steps += "<h3>Step 3: Solve</h3>"
                sols = solve(Eq(factored, 0), var)
                for s in sols:
                    approx = s.evalf(5) if hasattr(s, 'evalf') else s
                    steps += f"<div>\\[{latex(var)} = {latex(s)} \\approx {latex(approx)}\\]</div>"

            else:
                steps += "<h3>Step 2: Solving System of Equations</h3>"
                sol = solve(equations)
                if isinstance(sol, list):
                    for soln in sol:
                        for var, val in soln.items():
                            approx = val.evalf(5) if hasattr(val, 'evalf') else val
                            steps += f"<div>\\[{latex(var)} = {latex(val)} \\approx {latex(approx)}\\]</div>"
                elif isinstance(sol, dict):
                    for var, val in sol.items():
                        approx = val.evalf(5) if hasattr(val, 'evalf') else val
                        steps += f"<div>\\[{latex(var)} = {latex(val)} \\approx {latex(approx)}\\]</div>"
                else:
                    steps += f"<div>Solution: {sol}</div>"

        except Exception as e:
            steps = f"<div style='color:red'>Error: {str(e)}</div>"

    return render_template('index.html', result=steps, expression=expression)

@app.route('/graph', methods=['GET', 'POST'])
def graph():
    message = ''
    filename = ''
    latex_expr = ''
    exact_roots = []
    approx_roots = []

    if request.method == 'POST':
        expr = request.form['expression']
        x = symbols('x')
        try:
            expr = preprocess_expression(expr)
            y_expr = sympify(expr)
            latex_expr = latex(y_expr)
            x_vals = np.linspace(-10, 10, 400)

            if y_expr.free_symbols:
                f = lambda val: float(y_expr.evalf(subs={x: val}))
                y_vals = [f(val) for val in x_vals]
            else:
                y_vals = [float(y_expr)] * len(x_vals)

            eq = Eq(y_expr, 0)
            roots = solve(eq, x)

            for r in roots:
                if hasattr(r, "is_real") and r.is_real:
                    exact_roots.append(f"\\[ x = {latex(r)} \\]")
                    approx_roots.append(f"\\[ x \\approx {latex(r.evalf(5))} \\]")

            plt.clf()
            plt.figure(figsize=(8, 5))
            plt.plot(x_vals, y_vals, label=rf"$y = {latex_expr}$")
            plt.axhline(0, color='black', linewidth=0.5)
            plt.axvline(0, color='black', linewidth=0.5)
            plt.xlabel('x')
            plt.ylabel('y')
            plt.title('Graph of the Expression')
            plt.grid(True)

            for r in roots:
                if hasattr(r, "is_real") and r.is_real:
                    plt.plot(float(r), 0, 'ro')

            plt.legend()
            filename = 'static/graph.png'
            os.makedirs('static', exist_ok=True)
            plt.savefig(filename)
            plt.close()

        except Exception as e:
            message = f"Graph Error: {str(e)}"

    return render_template('graph.html',
                           image=filename,
                           message=message,
                           expression_latex=latex_expr,
                           exact_roots=exact_roots,
                           approx_roots=approx_roots)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)

from flask import Flask, render_template, request
from sympy import symbols, Eq, solve, sympify, latex
import matplotlib.pyplot as plt
import numpy as np
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    steps = ''
    expression = ''
    if request.method == 'POST':
        raw_input = request.form['equation']
        lines = raw_input.strip().split('\n')
        eqs = []
        all_vars = set()

        try:
            for line in lines:
                if '=' in line:
                    lhs, rhs = line.split('=')
                    lhs_expr = sympify(lhs)
                    rhs_expr = sympify(rhs)
                else:
                    lhs_expr = sympify(line)
                    rhs_expr = 0

                # Skip if both are just numbers
                if isinstance(lhs_expr, (int, float)) and isinstance(rhs_expr, (int, float)):
                    continue

                eq = Eq(lhs_expr, rhs_expr)
                eqs.append(eq)

                if hasattr(lhs_expr, 'free_symbols'):
                    all_vars |= lhs_expr.free_symbols
                if hasattr(rhs_expr, 'free_symbols'):
                    all_vars |= rhs_expr.free_symbols

            if not eqs:
                raise ValueError("No valid equations or expressions found.")

            # Auto-detect single or system
            if len(all_vars) == 1:
                x = list(all_vars)[0]
                eq = eqs[0]
                expression = str(eq.lhs - eq.rhs)

                steps += "<h3>Step 1: Given Equation</h3>"
                steps += rf"\[ {latex(eq)} \]<br>"

                combined_expr = eq.lhs - eq.rhs
                expanded_expr = combined_expr.expand()
                steps += "<h3>Step 2: Simplify Equation</h3>"
                steps += rf"\[ {latex(combined_expr)} = 0 \Rightarrow {latex(expanded_expr)} = 0 \]<br>"

                factored_expr = expanded_expr.factor()
                if factored_expr != expanded_expr:
                    steps += "<h3>Step 3: Factor the Expression</h3>"
                    steps += rf"\[ {latex(expanded_expr)} = {latex(factored_expr)} \]<br>"

                steps += "<h3>Step 4: Solve</h3>"
                x_solutions = solve(Eq(factored_expr, 0), x)
                if x_solutions:
                    for sol in x_solutions:
                        steps += rf"\[ x = {latex(sol)} \approx {sol.evalf(5)} \]<br>"
                else:
                    steps += "No real solution found."

            else:
                # System of equations
                solution = solve(eqs)
                steps += "<h3>Solution:</h3>"
                if isinstance(solution, list):
                    for sol in solution:
                        steps += rf"\[ {sol} \]<br>"
                elif isinstance(solution, dict):
                    for var, val in solution.items():
                        steps += rf"\[ {latex(var)} = {latex(val)} \approx {val.evalf(5)} \]<br>"
                else:
                    steps += "No solution found."

        except Exception as e:
            steps = f"Error: {str(e)}"

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
        try:
            x = symbols('x')
            y_expr = sympify(expr)
            latex_expr = latex(y_expr)

            f = lambda val: float(y_expr.evalf(subs={x: val}))
            x_vals = np.linspace(-10, 10, 400)
            y_vals = [f(val) for val in x_vals]

            eq = Eq(y_expr, 0)
            roots = solve(eq, x)

            for r in roots:
                if r.is_real:
                    exact_roots.append(rf"\[ x = {latex(r)} \]")
                    approx_roots.append(rf"\[ x \approx {r.evalf(5)} \]")

            plt.clf()
            plt.figure(figsize=(8, 5))
            plt.plot(x_vals, y_vals, label=f"$y = {latex_expr}$")
            plt.axhline(0, color='black', linewidth=0.5)
            plt.axvline(0, color='black', linewidth=0.5)
            plt.xlabel('x')
            plt.ylabel('y')
            plt.title('Graph of the Expression')
            plt.grid(True)

            for r in roots:
                if r.is_real:
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

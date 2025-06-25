from flask import Flask, render_template, request
from sympy import symbols, Eq, solve, sympify, latex, expand, factor, solveset, S
from sympy.parsing.sympy_parser import parse_expr
import matplotlib.pyplot as plt
import numpy as np
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = ''
    steps = ''
    expression_for_graph = ''

    if request.method == 'POST':
        equation_input = request.form['equation']
        lines = [line.strip() for line in equation_input.splitlines() if line.strip()]
        eqs = []
        all_vars = set()

        try:
            # Parse equations
            for line in lines:
                if '=' in line:
                    lhs, rhs = line.split('=')
                    lhs_expr = sympify(lhs)
                    rhs_expr = sympify(rhs)

                    # Avoid errors with numeric-only inputs like "5 = 5"
                    if isinstance(lhs_expr, (int, float)) and isinstance(rhs_expr, (int, float)):
                        continue

                    eq = Eq(lhs_expr, rhs_expr)
                else:
                    lhs_expr = sympify(line)
                    rhs_expr = 0
                    eq = Eq(lhs_expr, rhs_expr)

                eqs.append(eq)
                all_vars |= lhs_expr.free_symbols | rhs_expr.free_symbols

            if not eqs:
                result = "No valid equations entered."
                return render_template("index.html", result=result)

            # If single equation — show steps
            if len(eqs) == 1 and len(all_vars) == 1:
                x = list(all_vars)[0]
                eq = eqs[0]
                lhs_expr = eq.lhs
                rhs_expr = eq.rhs

                steps += "<h3>Step 1: Given Equation</h3>"
                steps += rf"\[ {latex(eq)} \]<br>"

                combined_expr = lhs_expr - rhs_expr
                expanded_expr = expand(combined_expr)

                steps += "<h3>Step 2: Simplify Equation</h3>"
                steps += rf"\[ {latex(combined_expr)} = 0 \Rightarrow {latex(expanded_expr)} = 0 \]<br>"

                factored_expr = factor(expanded_expr)
                if factored_expr != expanded_expr:
                    steps += "<h3>Step 3: Factor the Expression</h3>"
                    steps += rf"\[ {latex(expanded_expr)} = {latex(factored_expr)} \]<br>"

                steps += "<h3>Step 4: Solve</h3>"
                solutions = solve(Eq(factored_expr, 0), x)
                if solutions:
                    for sol in solutions:
                        steps += rf"\[ x = {latex(sol)} \approx {sol.evalf(5)} \]<br>"
                else:
                    steps += "No real solution found."

                expression_for_graph = str(lhs_expr - rhs_expr)

            else:
                # Multiple equations or multi-variable
                sol = solve(eqs, list(all_vars), dict=True)
                if sol:
                    steps = "<h3>Solution:</h3>"
                    for s in sol:
                        steps += r"\[ " + ", ".join([f"{str(k)} = {latex(v)}" for k, v in s.items()]) + r" \]<br>"
                else:
                    steps = "No solution found."

        except Exception as e:
            steps = f"Error: {str(e)}"

    return render_template('index.html', result=steps, expression=expression_for_graph)

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

            roots = solve(Eq(y_expr, 0), x)
            for r in roots:
                if r.is_real:
                    exact_roots.append(rf"\[ x = {latex(r)} \]")
                    approx_roots.append(rf"\[ x \approx {r.evalf(5)} \]")

            # Plotting
            plt.clf()
            plt.figure(figsize=(8, 5))
            plt.plot(x_vals, y_vals, label=rf"$y = {latex_expr}$")
            plt.axhline(0, color='black', linewidth=0.5)
            plt.axvline(0, color='black', linewidth=0.5)
            for r in roots:
                if r.is_real:
                    plt.plot(float(r), 0, 'ro')
            plt.title("Graph of the Expression")
            plt.xlabel('x')
            plt.ylabel('y')
            plt.grid(True)
            plt.legend()
            os.makedirs('static', exist_ok=True)
            filename = 'static/graph.png'
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

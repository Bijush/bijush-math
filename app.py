from flask import Flask, render_template, request
from sympy import symbols, Eq, solve, sympify, latex, expand, factor
import matplotlib.pyplot as plt
import numpy as np
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    steps = ''
    if request.method == 'POST':
        equation = request.form['equation']
        x = symbols('x')
        try:
            if '=' in equation:
                lhs, rhs = equation.split('=')
                lhs_expr = sympify(lhs)
                rhs_expr = sympify(rhs)
            else:
                lhs_expr = sympify(equation)
                rhs_expr = 0
            eq = Eq(lhs_expr, rhs_expr)

            steps += "<h3>Step 1: Given Equation</h3>"
            steps += f"\\[ {latex(eq)} \\]<br>"

            combined = lhs_expr - rhs_expr
            expanded = expand(combined)

            steps += "<h3>Step 2: Bring all terms to one side</h3>"
            steps += f"\\[ {latex(lhs_expr)} - ({latex(rhs_expr)}) = 0 \\Rightarrow {latex(expanded)} = 0 \\]<br>"

            factored = factor(expanded)
            if factored != expanded:
                steps += "<h3>Step 3: Factor the expression</h3>"
                steps += f"\\[ {latex(expanded)} = {latex(factored)} \\]<br>"

            steps += "<h3>Step 4: Apply zero-product property</h3>"
            solutions = solve(Eq(factored, 0), x)
            if solutions:
                for sol in solutions:
                    steps += f"\\[ x = {latex(sol)} \\approx {sol.evalf(5)} \\]<br>"
            else:
                steps += "No real solution found."

        except Exception as e:
            steps = f"Error: {str(e)}"

    return render_template('index.html', result=steps)

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
            y_expr = sympify(expr)
            latex_expr = latex(y_expr)

            f = lambda val: float(y_expr.evalf(subs={x: val}))
            x_vals = np.linspace(-10, 10, 400)
            y_vals = [f(val) for val in x_vals]

            eq = Eq(y_expr, 0)
            roots = solve(eq, x)

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
                    exact_roots.append(f"\\[ x = {latex(r)} \\]")
                    approx_roots.append(f"\\[ x \\approx {r.evalf(5)} \\]")

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

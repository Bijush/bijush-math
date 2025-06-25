from flask import Flask, render_template, request
from sympy import symbols, Eq, solve, sympify, latex, expand, factor, Poly
import matplotlib.pyplot as plt
import numpy as np
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    steps = ''
    expression = ''
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

            expression = str(lhs_expr)
            eq = Eq(lhs_expr, rhs_expr)

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

            # Quadratic formula explanation if degree is 2
            poly = Poly(expanded_expr, x)
            if poly.is_univariate and poly.degree() == 2:
                coeffs = poly.all_coeffs()
                if len(coeffs) == 3:
                    a, b, c = map(float, coeffs)
                    discriminant = b**2 - 4*a*c

                    steps += "<h3>Step 4: Use Quadratic Formula</h3>"
                    steps += r"\[ x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a} \]<br>"
                    steps += rf"\[ a = {a},\ b = {b},\ c = {c} \]<br>"
                    steps += rf"\[ D = b^2 - 4ac = {b}^2 - 4 \cdot {a} \cdot {c} = {discriminant} \]<br>"
                    steps += rf"\[ x = \frac{{-{b} \pm \sqrt{{{discriminant}}}}}{{2 \cdot {a}}} \]<br>"

            # Solve
            x_solutions = solve(Eq(factored_expr, 0), x)
            steps += "<h3>Step 5: Solve</h3>"
            if x_solutions:
                for sol in x_solutions:
                    steps += rf"\[ x = {latex(sol)} \approx {sol.evalf(5)} \]<br>"
            else:
                steps += "No real solution found."

        except Exception as e:
            steps = f"<b>Error:</b> {str(e)}"

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

            # Plotting
            plt.clf()
            plt.figure(figsize=(8, 5))
            plt.plot(x_vals, y_vals, label=f"$y = {latex_expr}$", color='blue')
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

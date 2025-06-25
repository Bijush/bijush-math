from flask import Flask, render_template, request
from sympy import symbols, Eq, solve, sympify, latex, expand, factor
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
            steps += f"\[ {latex(eq)} \]<br>"

            combined = lhs_expr - rhs_expr
            expanded = expand(combined)

            steps += "<h3>Step 2: Bring all terms to one side</h3>"
            steps += f"\[ {latex(lhs_expr)} - ({latex(rhs_expr)}) = 0 \Rightarrow {latex(expanded)} = 0 \]<br>"

            factored = factor(expanded)
            if factored != expanded:
                steps += "<h3>Step 3: Factor the expression</h3>"
                steps += f"\[ {latex(expanded)} = {latex(factored)} \]<br>"

            steps += "<h3>Step 4: Apply zero-product property</h3>"
            solutions = solve(Eq(factored, 0), x)
            if solutions:
                for sol in solutions:
                    steps += f"\[ x = {latex(sol)} \approx {sol.evalf(5)} \]<br>"
            else:
                steps += "No real solution found."

        except Exception as e:
            steps = f"Error: {str(e)}"

    return render_template('index.html', result=steps)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)

from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "hard to guess string"

# ================= INIT DB =================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # PRODUCTS
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        image TEXT
    )
    """)

    # sample products
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        c.executemany("""
        INSERT INTO products (name, price, image)
        VALUES (?, ?, ?)
        """, [
            ("Laptop", 10000, "Laptop.avif"),
            ("Headphones", 300, "Headphones.webp"),
            ("Backpack", 200, "Backpack.webp"),
            ("Laptop 2", 17500, "lap2.webp"),
            ("Laptop 3", 18000, "lap3.jpg"),
            ("Laptop 4", 20000, "lap4.jpg"),
            ("RTX 5070 Ti", 2500, "RTX5070Ti.jpg"),
            ("PlayStation", 2000, "plays.jpg"),
        ])

    conn.commit()
    conn.close()

init_db()

# ================= SIGNUP =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                      (name, email, password))
            conn.commit()
        except:
            return "Email already exists"

        conn.close()
        return redirect("/signin")

    return render_template("signup.html")

# ================= SIGNIN =================
@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE email=? AND password=?",
                  (email, password))
        user = c.fetchone()

        conn.close()

        if user:
            session["user"] = user[1]
            session["cart"] = []
            return redirect("/")
        else:
            return "Invalid Email or Password"

    return render_template("signin.html")

# ================= HOME =================
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/signin")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM products")
    products = c.fetchall()

    conn.close()

    return render_template("home.html", products=products, user=session["user"])

# ================= SEARCH =================
@app.route("/search")
def search():
    q = request.args.get("q")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + q + '%',))
    products = c.fetchall()

    conn.close()

    return render_template("home.html", products=products, user=session.get("user"))

# ================= ADD TO CART =================
@app.route("/add/<int:id>")
def add(id):
    cart = session.get("cart", [])

    if id not in cart:
        cart.append(id)

    session["cart"] = cart
    session.modified = True

    return redirect("/")

# ================= CART =================
@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect("/signin")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    cart_items = []
    total = 0

    for cid in session.get("cart", []):
        c.execute("SELECT * FROM products WHERE id=?", (cid,))
        p = c.fetchone()
        if p:
            cart_items.append(p)
            total += p[2]

    conn.close()

    return render_template("cart.html", cart=cart_items, total=total)

# ================= REMOVE =================
@app.route("/remove/<int:id>")
def remove(id):
    cart = session.get("cart", [])

    if id in cart:
        cart.remove(id)

    session["cart"] = cart
    session.modified = True

    return redirect("/cart")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/signin")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users ")
    users = c.fetchall()

    c.execute("SELECT * FROM products")
    products = c.fetchall()

    conn.close()

    return render_template("dashboard.html", users=users, products=products)

# ================= ADD PRODUCT =================
@app.route("/add_product", methods=["POST"])
def add_product():
    name = request.form["name"]
    price = request.form["price"]
    image = request.files["image"]

    path = os.path.join("static/images", image.filename)
    image.save(path)

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("INSERT INTO products (name, price, image) VALUES (?, ?, ?)",
              (name, price, image.filename))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ================= DELETE PRODUCT =================
@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM products WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ================= EDIT PRODUCT =================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]

        c.execute("UPDATE products SET name=?, price=? WHERE id=?",
                  (name, price, id))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    c.execute("SELECT * FROM products WHERE id=?", (id,))
    product = c.fetchone()

    conn.close()

    return render_template("edit_product.html", product=product)

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/signin")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
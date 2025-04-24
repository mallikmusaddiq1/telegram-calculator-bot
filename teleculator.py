from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
import math
import random

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

user_inputs = {}

def get_main_keyboard():
    keys = [
        ["2nd", "(", ")", "10^x", "M+"],
        ["1/x", "x^2", "x^3", "y^x", "M-"],
        ["x!", "sqrt", "log", "ln", "MR"],
        ["sin", "cos", "tan", "e^x", "MC"],
        ["7", "8", "9", "/", "*"],
        ["4", "5", "6", "-", "+"],
        ["1", "2", "3", ".", "0"],
        ["π", "e", "EE", "Rand", "%"],
        ["DEL", "AC", "=", "DEG/RAD", "More Options"],
    ]
    keyboard = [[InlineKeyboardButton(text=key, callback_data=key) for key in row] for row in keys]
    return InlineKeyboardMarkup(keyboard)

def get_advanced_keyboard():
    keys = [
        ["sinh", "cosh", "tanh", "log_b"],
        ["asin", "acos", "atan", "Back to Main"],
    ]
    keyboard = [[InlineKeyboardButton(text=key, callback_data=key) for key in row] for row in keys]
    return InlineKeyboardMarkup(keyboard)

def safe_eval(expr, mode):
    expr = expr.replace("π", "math.pi").replace("e", "math.e").replace("^", "**")
    
    if mode == "degrees":
        sin = lambda x: math.sin(math.radians(x))
        cos = lambda x: math.cos(math.radians(x))
        tan = lambda x: math.tan(math.radians(x))
        asin = lambda x: math.degrees(math.asin(x))
        acos = lambda x: math.degrees(math.acos(x))
        atan = lambda x: math.degrees(math.atan(x))
    else:
        sin = math.sin
        cos = math.cos
        tan = math.tan
        asin = math.asin
        acos = math.acos
        atan = math.atan

    sinh = math.sinh
    cosh = math.cosh
    tanh = math.tanh
    log = math.log10
    ln = math.log
    log_b = math.log
    sqrt = math.sqrt
    exp = math.exp

    def reciprocal(x): return 1/x
    def square(x): return x**2
    def cube(x): return x**3
    def power(x, y): return math.pow(x, y)
    def factorial(x): return math.factorial(int(x))
    def ten_power(x): return 10**x
    def random_num(): return random.random()

    namespace = {
        "math": math,
        "sin": sin, "cos": cos, "tan": tan,
        "asin": asin, "acos": acos, "atan": atan,
        "sinh": sinh, "cosh": cosh, "tanh": tanh,
        "log": log, "ln": ln, "log_b": log_b,
        "sqrt": sqrt, "exp": exp,
        "reciprocal": reciprocal, "square": square, "cube": cube,
        "power": power, "factorial": factorial,
        "ten_power": ten_power, "random": random_num
    }

    try:
        if "y^x" in expr and expr.count("y^x") == 1:
            parts = expr.split("y^x")
            if len(parts) == 2 and parts[0] and parts[1]:
                base = safe_eval(parts[0], mode)
                exp = safe_eval(parts[1], mode)
                return math.pow(base, exp)
        result = eval(expr, {"__builtins__": None}, namespace)
        return result
    except Exception as e:
        print("Evaluation error:", e)
        return "Error"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_inputs[user_id] = {"expression": "", "mode": "radians", "memory": 0.0, "second": False, "keyboard": "main"}
    await update.message.reply_text("Calculator\n\nExpression: \nMode: radians", reply_markup=get_main_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_inputs:
        user_inputs[user_id] = {"expression": "", "mode": "radians", "memory": 0.0, "second": False, "keyboard": "main"}

    text = query.data
    print(f"User clicked: {text}")
    current_expr = user_inputs[user_id]["expression"]
    mode = user_inputs[user_id]["mode"]
    second = user_inputs[user_id]["second"]
    keyboard_state = user_inputs[user_id]["keyboard"]

    if text == "More Options":
        user_inputs[user_id]["keyboard"] = "advanced"
        await query.edit_message_text(f"Expression: {current_expr}\nMode: {mode}", reply_markup=get_advanced_keyboard())
        return
    elif text == "Back to Main":
        user_inputs[user_id]["keyboard"] = "main"
        await query.edit_message_text(f"Expression: {current_expr}\nMode: {mode}", reply_markup=get_main_keyboard())
        return

    function_buttons = ["sin", "cos", "tan", "log", "ln"]
    if keyboard_state == "advanced":
        function_buttons.extend(["sinh", "cosh", "tanh", "log_b", "asin", "acos", "atan"])
    if second:
        function_buttons = ["asin", "acos", "atan", "log", "ln"]

    if text == "2nd":
        user_inputs[user_id]["second"] = not second
    elif text in function_buttons:
        current_expr += text + "("
    elif text == "AC":
        current_expr = ""
        user_inputs[user_id]["memory"] = 0.0
    elif text == "DEL":
        current_expr = current_expr[:-1]
    elif text == "=":
        try:
            result = str(safe_eval(current_expr, mode))
            current_expr = result
        except Exception as e:
            print("Error on '=':", e)
            current_expr = "Error"
    elif text == "DEG/RAD":
        new_mode = "degrees" if mode == "radians" else "radians"
        user_inputs[user_id]["mode"] = new_mode
        mode = new_mode
    elif text == "M+":
        try:
            value = safe_eval(current_expr, mode)
            if isinstance(value, (int, float)):
                user_inputs[user_id]["memory"] += value
            else:
                current_expr = "Error"
        except Exception as e:
            print("Error on M+:", e)
            current_expr = "Error"
    elif text == "M-":
        try:
            value = safe_eval(current_expr, mode)
            if isinstance(value, (int, float)):
                user_inputs[user_id]["memory"] -= value
            else:
                current_expr = "Error"
        except Exception as e:
            print("Error on M-:", e)
            current_expr = "Error"
    elif text == "MR":
        memory = user_inputs[user_id]["memory"]
        current_expr += str(memory)
    elif text == "MC":
        user_inputs[user_id]["memory"] = 0.0
    elif text == "1/x":
        current_expr = f"reciprocal({current_expr})" if current_expr else "Error"
    elif text == "x^2":
        current_expr = f"square({current_expr})" if current_expr else "Error"
    elif text == "x^3":
        current_expr = f"cube({current_expr})" if current_expr else "Error"
    elif text == "y^x":
        current_expr += "y^x"
    elif text == "10^x":
        current_expr = f"ten_power({current_expr})" if current_expr else "Error"
    elif text == "e^x":
        current_expr = f"exp({current_expr})" if current_expr else "Error"
    elif text == "x!":
        current_expr = f"factorial({current_expr})" if current_expr else "Error"
    elif text == "%":
        current_expr = f"{current_expr}/100" if current_expr else "Error"
    elif text == "Rand":
        current_expr = str(random.random())
    elif text == "EE":
        current_expr += "e"
    else:
        current_expr += text

    user_inputs[user_id]["expression"] = current_expr
    keyboard = get_main_keyboard() if keyboard_state == "main" else get_advanced_keyboard()
    await query.edit_message_text(f"Expression: {current_expr}\nMode: {mode}", reply_markup=keyboard)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()
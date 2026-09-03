#!/usr/bin/env python3
import os
import sys
import math
import json

# Add local bundled vendor
VENDOR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if os.path.exists(VENDOR_PATH):
    sys.path.insert(0, VENDOR_PATH)

os.environ["PYSDL2_DLL_PATH"] = "/usr/trimui/lib"

try:
    import sdl2
    import sdl2.ext
    import sdl2.sdlttf as sdlttf
except ImportError as e:
    sys.stderr.write("Cannot load SDL2. Error: " + str(e))
    sys.exit(1)

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "font.ttf")
SAVES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves.json")

# Themes
CALCULATOR_THEMES = [
    {
        "name": "Vintage Nature",
        "bg": sdl2.ext.Color(235, 213, 171),           # #EBD5AB
        "btn_bg": sdl2.ext.Color(139, 174, 102),       # #8BAE66
        "btn_op_bg": sdl2.ext.Color(98, 129, 65),      # #628141
        "btn_eq_bg": sdl2.ext.Color(217, 83, 79),      # #D9534F
        "sel_color": sdl2.ext.Color(230, 126, 34),     # #E67E22
        "text": sdl2.SDL_Color(82, 70, 70, 255),       # #524646
        "text_btn": sdl2.SDL_Color(245, 245, 245, 255),# #F5F5F5
        "text_eq": sdl2.SDL_Color(255, 255, 255, 255), # #FFFFFF
        "tab_active": sdl2.ext.Color(139, 174, 102),   # #8BAE66
        "tab_inactive": sdl2.ext.Color(235, 213, 171), # #EBD5AB
        "result_preview": sdl2.SDL_Color(154, 160, 166, 255), # #9AA0A6
        "popup_border": sdl2.ext.Color(139, 69, 19),   # #8B4513
    },
    {
        "name": "Midnight",
        "bg": sdl2.ext.Color(18, 22, 29),              # #12161D
        "btn_bg": sdl2.ext.Color(67, 88, 111),         # #43586F
        "btn_op_bg": sdl2.ext.Color(48, 65, 83),       # #304153
        "btn_eq_bg": sdl2.ext.Color(170, 76, 76),      # #AA4C4C
        "sel_color": sdl2.ext.Color(198, 145, 72),     # #C69148
        "text": sdl2.SDL_Color(227, 232, 239, 255),    # #E3E8EF
        "text_btn": sdl2.SDL_Color(239, 242, 245, 255),# #EFF2F5
        "text_eq": sdl2.SDL_Color(255, 255, 255, 255), # #FFFFFF
        "tab_active": sdl2.ext.Color(67, 88, 111),     # #43586F
        "tab_inactive": sdl2.ext.Color(18, 22, 29),    # #12161D
        "result_preview": sdl2.SDL_Color(143, 154, 170, 255), # #8F9AAA
        "popup_border": sdl2.ext.Color(52, 66, 82),    # #344252
    },
    {
        "name": "Warm Paper",
        "bg": sdl2.ext.Color(243, 235, 217),           # #F3EBD9
        "btn_bg": sdl2.ext.Color(133, 157, 112),       # #859D70
        "btn_op_bg": sdl2.ext.Color(91, 111, 77),      # #5B6F4D
        "btn_eq_bg": sdl2.ext.Color(181, 91, 82),      # #B55B52
        "sel_color": sdl2.ext.Color(190, 139, 68),     # #BE8B44
        "text": sdl2.SDL_Color(64, 57, 47, 255),       # #40392F
        "text_btn": sdl2.SDL_Color(247, 247, 242, 255),# #F7F7F2
        "text_eq": sdl2.SDL_Color(255, 255, 255, 255), # #FFFFFF
        "tab_active": sdl2.ext.Color(133, 157, 112),   # #859D70
        "tab_inactive": sdl2.ext.Color(243, 235, 217), # #F3EBD9
        "result_preview": sdl2.SDL_Color(136, 123, 104, 255), # #887B68
        "popup_border": sdl2.ext.Color(190, 139, 68),  # #BE8B44
    },
    {
        "name": "Forest",
        "bg": sdl2.ext.Color(24, 32, 27),              # #18201B
        "btn_bg": sdl2.ext.Color(76, 103, 80),         # #4C6750
        "btn_op_bg": sdl2.ext.Color(48, 68, 52),       # #304434
        "btn_eq_bg": sdl2.ext.Color(157, 82, 76),      # #9D524C
        "sel_color": sdl2.ext.Color(177, 151, 79),     # #B1974F
        "text": sdl2.SDL_Color(217, 226, 213, 255),    # #D9E2D5
        "text_btn": sdl2.SDL_Color(238, 242, 235, 255),# #EEF2EB
        "text_eq": sdl2.SDL_Color(255, 255, 255, 255), # #FFFFFF
        "tab_active": sdl2.ext.Color(76, 103, 80),     # #4C6750
        "tab_inactive": sdl2.ext.Color(24, 32, 27),    # #18201B
        "result_preview": sdl2.SDL_Color(158, 173, 159, 255), # #9EAD9F
        "popup_border": sdl2.ext.Color(73, 98, 79),    # #49624F
    }
]

def load_theme_idx():
    try:
        if os.path.exists(SAVES_FILE):
            with open(SAVES_FILE, 'r') as f:
                saves = json.load(f)
                return int(saves.get("theme_idx", 0)) % len(CALCULATOR_THEMES)
    except:
        pass
    return 0

def write_theme_idx(theme_idx):
    try:
        saves = {}
        if os.path.exists(SAVES_FILE):
            with open(SAVES_FILE, 'r') as f:
                saves = json.load(f)
        saves["theme_idx"] = theme_idx % len(CALCULATOR_THEMES)
        with open(SAVES_FILE, 'w') as f:
            json.dump(saves, f)
    except:
        pass

# Modes
MODE_123 = 0
MODE_FX = 1
MODE_HISTORY = 2

# Global state for parser
is_deg = True
inv_mode = False
ans_val = 0.0

def evaluate_math(expression):
    global is_deg, inv_mode, ans_val
    if not expression: return ""
    
    # Replace symbols for Python math evaluation
    expr = expression.replace('×', '*').replace('÷', '/').replace('%', '/100')
    expr = expr.replace('π', 'math.pi').replace('e', 'math.e')
    expr = expr.replace('√', 'math.sqrt')
    expr = expr.replace('^', '**')
    expr = expr.replace('EXP', '*10**')
    expr = expr.replace('Ans', str(ans_val))
    expr = expr.replace('ln', 'math.log')
    expr = expr.replace('log', 'math.log10')
    expr = expr.replace('!', 'math.factorial') # factorial parsing needs custom logic if trailing like 5! -> math.factorial(5)
    # Simple fix for factorial: this won't work well with complex expressions like (3+2)!, so we'll just leave it simple or do regex.
    # For now, regex replacement for factorial:
    import re
    expr = re.sub(r'(\d+|\([^)]+\))!', r'math.factorial(\1)', expr)

    # Trig functions
    trig_funcs = ['sin', 'cos', 'tan', 'asin', 'acos', 'atan']
    for func in trig_funcs:
        if func in expr:
            # this is a bit crude but works for simple calculator
            pass # we'll use a custom dict for math functions that handles deg/rad

    # Custom wrapper for math functions to handle deg/rad
    def safe_sin(x): return math.sin(math.radians(x)) if is_deg else math.sin(x)
    def safe_cos(x): return math.cos(math.radians(x)) if is_deg else math.cos(x)
    def safe_tan(x): return math.tan(math.radians(x)) if is_deg else math.tan(x)
    def safe_asin(x): return math.degrees(math.asin(x)) if is_deg else math.asin(x)
    def safe_acos(x): return math.degrees(math.acos(x)) if is_deg else math.acos(x)
    def safe_atan(x): return math.degrees(math.atan(x)) if is_deg else math.atan(x)
    
    safe_dict = {
        'math': math,
        'sin': safe_sin, 'cos': safe_cos, 'tan': safe_tan,
        'asin': safe_asin, 'acos': safe_acos, 'atan': safe_atan,
        'ln': math.log, 'log': math.log10, 'sqrt': math.sqrt,
        'factorial': math.factorial
    }
    
    # Fix function names in expr
    expr = expr.replace('math.sqrt', 'sqrt').replace('math.log', 'ln').replace('math.log10', 'log').replace('math.factorial', 'factorial')
    
    try:
        res = eval(expr, {"__builtins__": None}, safe_dict)
        if isinstance(res, float) and res.is_integer():
            return str(int(res))
        return str(round(res, 8))
    except Exception as e:
        return "Error"

def main():
    global is_deg, inv_mode, ans_val
    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_GAMECONTROLLER)
    sdlttf.TTF_Init()

    num_joysticks = sdl2.SDL_NumJoysticks()
    controllers = []
    for i in range(num_joysticks):
        if sdl2.SDL_IsGameController(i):
            controllers.append(sdl2.SDL_GameControllerOpen(i))

    window = sdl2.ext.Window("Calculator", size=(1024, 768), flags=sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP)
    window.show()
    renderer = sdl2.ext.Renderer(window)

    font_path = FONT_PATH.encode('utf-8')
    if os.path.exists(FONT_PATH):
        font_large = sdlttf.TTF_OpenFont(font_path, 72)
        font_medium = sdlttf.TTF_OpenFont(font_path, 48)
        font_small = sdlttf.TTF_OpenFont(font_path, 32)
        font_mini = sdlttf.TTF_OpenFont(font_path, 24)
    else:
        sys.exit(1)

    # Layouts
    grid_123 = [
        ['(', ')', '%', 'AC'],
        ['7', '8', '9', '÷'],
        ['4', '5', '6', '×'],
        ['1', '2', '3', '-'],
        ['0', '.', '=', '+']
    ]
    
    grid_fx_norm = [
        ['Deg/Rad', 'x!', 'Inv'], # We'll handle spans manually
        ['sin', 'ln', 'π', 'cos'],
        ['log', 'e', 'tan', '√'],
        ['Ans', 'EXP', '^', '=']
    ]
    
    grid_fx_inv = [
        ['Deg/Rad', 'x!', 'Inv'],
        ['asin', 'e^x', 'π', 'acos'],
        ['10^x', 'e', 'atan', 'x²'],
        ['Ans', 'EXP', '^', '=']
    ]

    mode = MODE_123
    cursor_x, cursor_y = 0, 0
    expr = ""
    expr_scroll = 0
    history = []
    show_history = False
    show_quit_confirm = False
    theme_idx = load_theme_idx()
    l2_pressed = False
    r2_pressed = False

    def render_text(text, font, color):
        tsurf = sdlttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), color)
        if tsurf:
            ttex = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, tsurf)
            w, h = tsurf.contents.w, tsurf.contents.h
            sdl2.SDL_FreeSurface(tsurf)
            return ttex, w, h
        return None, 0, 0

    running = True
    prev_axis_up = False
    prev_axis_down = False
    prev_axis_left = False
    prev_axis_right = False
    axis_timer_v = 0
    axis_timer_h = 0
    dpad_up_held = False
    dpad_down_held = False
    dpad_left_held = False
    dpad_right_held = False
    dpad_timer_v = 0
    dpad_timer_h = 0

    def nav_up():
        nonlocal cursor_y
        cursor_y = max(0, cursor_y - 1)

    def nav_down():
        nonlocal cursor_y
        max_y = 4 if mode == MODE_123 else 3
        cursor_y = min(max_y, cursor_y + 1)

    def nav_left():
        nonlocal cursor_x
        cursor_x = max(0, cursor_x - 1)

    def nav_right():
        nonlocal cursor_x
        max_x = 3
        if mode == MODE_FX and cursor_y == 0 and cursor_x == 1:
            max_x = 2
        cursor_x = min(max_x, cursor_x + 1)

    while running:
        needs_redraw = True
        
        # Poll Joystick Axes
        axis_up = False
        axis_down = False
        axis_left = False
        axis_right = False
        for c in controllers:
            lx = sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_LEFTX)
            ly = sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_LEFTY)
            rx = sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_RIGHTX)
            ry = sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_RIGHTY)
            ax = lx if abs(lx) >= abs(rx) else rx
            ay = ly if abs(ly) >= abs(ry) else ry
            if ay < -15000: axis_up = True
            elif ay > 15000: axis_down = True
            if ax < -15000: axis_left = True
            elif ax > 15000: axis_right = True

        if not show_quit_confirm and not show_history:
            # Vertical Joystick Motion
            if axis_up:
                if not prev_axis_up:
                    nav_up()
                    axis_timer_v = 0
                else:
                    axis_timer_v += 1
                    if axis_timer_v > 15 and axis_timer_v % 4 == 0:
                        nav_up()
            elif axis_down:
                if not prev_axis_down:
                    nav_down()
                    axis_timer_v = 0
                else:
                    axis_timer_v += 1
                    if axis_timer_v > 15 and axis_timer_v % 4 == 0:
                        nav_down()
            else:
                axis_timer_v = 0
            
            # Horizontal Joystick Motion
            if axis_left:
                if not prev_axis_left:
                    nav_left()
                    axis_timer_h = 0
                else:
                    axis_timer_h += 1
                    if axis_timer_h > 15 and axis_timer_h % 4 == 0:
                        nav_left()
            elif axis_right:
                if not prev_axis_right:
                    nav_right()
                    axis_timer_h = 0
                else:
                    axis_timer_h += 1
                    if axis_timer_h > 15 and axis_timer_h % 4 == 0:
                        nav_right()
            else:
                axis_timer_h = 0

            # D-pad Repeat
            if dpad_up_held:
                dpad_timer_v += 1
                if dpad_timer_v > 15 and dpad_timer_v % 4 == 0:
                    nav_up()
            elif dpad_down_held:
                dpad_timer_v += 1
                if dpad_timer_v > 15 and dpad_timer_v % 4 == 0:
                    nav_down()
            else:
                dpad_timer_v = 0

            if dpad_left_held:
                dpad_timer_h += 1
                if dpad_timer_h > 15 and dpad_timer_h % 4 == 0:
                    nav_left()
            elif dpad_right_held:
                dpad_timer_h += 1
                if dpad_timer_h > 15 and dpad_timer_h % 4 == 0:
                    nav_right()
            else:
                dpad_timer_h = 0

        prev_axis_up = axis_up
        prev_axis_down = axis_down
        prev_axis_left = axis_left
        prev_axis_right = axis_right

        # Event Loop
        events = sdl2.ext.get_events()
        if len(events) > 0:
            needs_redraw = True
            
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                pass # Ignore ESCAPE / MENU key
            elif event.type == sdl2.SDL_CONTROLLERBUTTONUP:
                btn = event.cbutton.button
                if btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP: dpad_up_held = False
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN: dpad_down_held = False
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT: dpad_left_held = False
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT: dpad_right_held = False
            elif event.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
                btn = event.cbutton.button
                if show_quit_confirm:
                    if btn == sdl2.SDL_CONTROLLER_BUTTON_B: # Physical A (Confirm)
                        running = False
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_A: # Physical B (Cancel)
                        show_quit_confirm = False
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_START:
                    show_quit_confirm = True
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_BACK: # SELECT
                    show_history = not show_history
                elif show_history:
                    if btn == sdl2.SDL_CONTROLLER_BUTTON_B: # Physical A on TrimUI - Close history
                        show_history = False
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP or btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
                        pass # Could implement history scrolling
                else:
                    if btn == sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER or btn == sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER:
                        mode = MODE_FX if mode == MODE_123 else MODE_123
                        cursor_x, cursor_y = 0, 0
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP:
                        dpad_up_held = True
                        dpad_timer_v = 0
                        nav_up()
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
                        dpad_down_held = True
                        dpad_timer_v = 0
                        nav_down()
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT:
                        dpad_left_held = True
                        dpad_timer_h = 0
                        nav_left()
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT:
                        dpad_right_held = True
                        dpad_timer_h = 0
                        nav_right()
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_A: # Physical B - Backspace
                        if expr == "Error": expr = ""
                        elif len(expr) > 0: expr = expr[:-1]
                        expr_scroll = 0 # reset scroll
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_Y: # Physical X on TrimUI -> '='
                        res = evaluate_math(expr)
                        if res != "Error" and res != "":
                            history.append({'expr': expr, 'res': res})
                            if len(history) > 10: history.pop(0)
                            ans_val = res
                        expr = res
                        expr_scroll = 0
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_X: # Physical Y on TrimUI -> 'AC'
                        expr = ""
                        expr_scroll = 0
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_B: # Physical A - Select
                        if mode == MODE_123:
                            char = grid_123[cursor_y][cursor_x]
                        else:
                            grid = grid_fx_inv if inv_mode else grid_fx_norm
                            if cursor_y == 0:
                                if cursor_x == 0: char = 'Deg/Rad'
                                elif cursor_x == 1: char = 'x!'
                                else: char = 'Inv'
                            else:
                                char = grid[cursor_y][cursor_x]
                                
                        if char == 'AC':
                            expr = ""
                        elif char == '=':
                            res = evaluate_math(expr)
                            if res != "Error" and res != "":
                                history.append({'expr': expr, 'res': res})
                                if len(history) > 10: history.pop(0)
                                ans_val = res
                            expr = res
                        elif char == 'Deg/Rad':
                            is_deg = not is_deg
                        elif char == 'Inv':
                            inv_mode = not inv_mode
                        else:
                            if expr == "Error": expr = ""
                            
                            # Add formatting for functions
                            if char in ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'ln', 'log', '√']:
                                expr += char + '('
                            elif char == 'x!': expr += '!'
                            elif char == 'x²': expr += '^2'
                            elif char == 'e^x': expr += 'e^'
                            elif char == '10^x': expr += '10^'
                            else:
                                expr += char
                            expr_scroll = 0 # reset scroll
            
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK: # Fallback L2 on some CFW
                        theme_idx = (theme_idx - 1) % len(CALCULATOR_THEMES)
                        write_theme_idx(theme_idx)
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK: # Fallback R2 on some CFW
                        theme_idx = (theme_idx + 1) % len(CALCULATOR_THEMES)
                        write_theme_idx(theme_idx)
            elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
                axis = event.caxis.axis
                val = event.caxis.value
                if axis == sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT:
                    if val > 16000 and not l2_pressed:
                        l2_pressed = True
                        theme_idx = (theme_idx - 1) % len(CALCULATOR_THEMES)
                        write_theme_idx(theme_idx)
                    elif val <= 16000:
                        l2_pressed = False
                elif axis == sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT:
                    if val > 16000 and not r2_pressed:
                        r2_pressed = True
                        theme_idx = (theme_idx + 1) % len(CALCULATOR_THEMES)
                        write_theme_idx(theme_idx)
                    elif val <= 16000:
                        r2_pressed = False
            
            # Additional fallback for keyboard
            elif event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym.sym
                if key == sdl2.SDLK_ESCAPE:
                    running = False
                elif key == sdl2.SDLK_LEFTBRACKET or key == sdl2.SDLK_PAGEUP:
                    theme_idx = (theme_idx - 1) % len(CALCULATOR_THEMES)
                    write_theme_idx(theme_idx)
                elif key == sdl2.SDLK_RIGHTBRACKET or key == sdl2.SDLK_PAGEDOWN:
                    theme_idx = (theme_idx + 1) % len(CALCULATOR_THEMES)
                    write_theme_idx(theme_idx)
                    
        if needs_redraw:
            theme = CALCULATOR_THEMES[theme_idx]
            renderer.clear(theme["bg"])
            w_w, w_h = 1024, 768
    
            # Render Expression and Result
            tex, tw, th = render_text(expr if expr else "0", font_large, theme["text"])
            if tex:
                max_scroll = max(0, tw - (w_w - 80))
                expr_scroll = max(0, min(max_scroll, expr_scroll))
                
                x_pos = w_w - tw - 40 + expr_scroll
                
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(x_pos, 100, tw, th))
                sdl2.SDL_DestroyTexture(tex)
                
                # Mask out the left side so text doesn't overflow into the edge
                renderer.fill((0, 100, 40, th), theme["bg"])
                
            # Optional: render small preview of result below expression
            if expr and expr != "Error":
                res_preview = evaluate_math(expr)
                if res_preview and res_preview != "Error" and res_preview != expr:
                    tex, tw, th = render_text("= " + res_preview, font_medium, theme["result_preview"])
                    if tex:
                        sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(w_w - tw - 40, 180, tw, th))
                        sdl2.SDL_DestroyTexture(tex)
    
            # Draw Tabs (123 / Fx)
            tab_w = 150
            tab_h = 50
            tab_y = 20
            tab_x = 20
            
            # 123 Tab
            renderer.fill((tab_x, tab_y, tab_w, tab_h), theme["tab_active"] if mode == MODE_123 else theme["tab_inactive"])
            tex, tw, th = render_text("123", font_small, theme["text_btn"] if mode == MODE_123 else theme["text"])
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(tab_x + tab_w//2 - tw//2, tab_y + tab_h//2 - th//2, tw, th))
                sdl2.SDL_DestroyTexture(tex)
                
            # Fx Tab
            renderer.fill((tab_x + tab_w, tab_y, tab_w, tab_h), theme["tab_active"] if mode == MODE_FX else theme["tab_inactive"])
            tex, tw, th = render_text("Fx", font_small, theme["text_btn"] if mode == MODE_FX else theme["text"])
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(tab_x + tab_w + tab_w//2 - tw//2, tab_y + tab_h//2 - th//2, tw, th))
                sdl2.SDL_DestroyTexture(tex)
    
            # Draw Grid
            btn_w, btn_h = 200, 70
            padding = 10
            grid_cols = 4
            
            if mode == MODE_123:
                grid_rows = 5
                total_w = grid_cols * btn_w + (grid_cols - 1) * padding
                total_h = grid_rows * btn_h + (grid_rows - 1) * padding
                start_x = (w_w - total_w) // 2
                start_y = 250
                
                for r in range(grid_rows):
                    for c in range(grid_cols):
                        bx = start_x + c * (btn_w + padding)
                        by = start_y + r * (btn_h + padding)
                        char = grid_123[r][c]
                        
                        b_color = theme["btn_bg"]
                        if char in ['÷', '×', '-', '+', 'AC', '%', '(', ')']:
                            b_color = theme["btn_op_bg"]
                        if char == '=': 
                            b_color = theme["btn_eq_bg"]
                            
                        if cursor_x == c and cursor_y == r: 
                            b_color = theme["sel_color"]
                            renderer.fill((bx-3, by-3, btn_w+6, btn_h+6), sdl2.ext.Color(255, 255, 255))
                    
                        renderer.fill((bx, by, btn_w, btn_h), b_color)
                        
                        t_color = theme["text_eq"] if char == '=' else theme["text_btn"]
                        tex, tw, th = render_text(char, font_medium, t_color)
                        if tex:
                            sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(bx + btn_w//2 - tw//2, by + btn_h//2 - th//2, tw, th))
                            sdl2.SDL_DestroyTexture(tex)
            else:
                # Fx Mode
                grid_rows = 4
                total_w = grid_cols * btn_w + (grid_cols - 1) * padding
                total_h = grid_rows * btn_h + (grid_rows - 1) * padding
                start_x = (w_w - total_w) // 2
                start_y = 250
                
                grid = grid_fx_inv if inv_mode else grid_fx_norm
                
                for r in range(grid_rows):
                    if r == 0:
                        # Row 0 has special span: Deg/Rad (span 2), x!, Inv
                        for c in range(3):
                            if c == 0:
                                bw = btn_w * 2 + padding
                                bx = start_x
                                char = 'DEG' if is_deg else 'RAD'
                            else:
                                bw = btn_w
                                bx = start_x + (c+1) * (btn_w + padding)
                                char = grid[0][c]
                                
                            by = start_y + r * (btn_h + padding)
                            
                            b_color = theme["btn_op_bg"]
                            if char == 'Inv' and inv_mode: b_color = theme["sel_color"] # Highlight when active
                            
                            if cursor_y == r and cursor_x == c: 
                                b_color = theme["sel_color"]
                                renderer.fill((bx-3, by-3, bw+6, btn_h+6), sdl2.ext.Color(255, 255, 255))
                            
                            renderer.fill((bx, by, bw, btn_h), b_color)
                            
                            tex, tw, th = render_text(char, font_medium, theme["text_btn"])
                            if tex:
                                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(bx + bw//2 - tw//2, by + btn_h//2 - th//2, tw, th))
                                sdl2.SDL_DestroyTexture(tex)
                    else:
                        for c in range(grid_cols):
                            bx = start_x + c * (btn_w + padding)
                            by = start_y + r * (btn_h + padding)
                            char = grid[r][c]
                            
                            b_color = theme["btn_op_bg"]
                            if char == '=': 
                                b_color = theme["btn_eq_bg"]
                                
                            if cursor_y == r and cursor_x == c: 
                                b_color = theme["sel_color"]
                                renderer.fill((bx-3, by-3, btn_w+6, btn_h+6), sdl2.ext.Color(255, 255, 255))
                            
                            renderer.fill((bx, by, btn_w, btn_h), b_color)
                            
                            t_color = theme["text_eq"] if char == '=' else theme["text_btn"]
                            tex, tw, th = render_text(char, font_medium, t_color)
                            if tex:
                                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(bx + btn_w//2 - tw//2, by + btn_h//2 - th//2, tw, th))
                                sdl2.SDL_DestroyTexture(tex)
                                
            # History Overlay
            if show_history:
                sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
                sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, theme["bg"].r, theme["bg"].g, theme["bg"].b, 230)
                sdl2.SDL_RenderFillRect(renderer.sdlrenderer, sdl2.SDL_Rect(0, 0, w_w, w_h))
                
                tex, tw, th = render_text("History", font_large, theme["text"])
                if tex:
                    sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(40, 40, tw, th))
                    sdl2.SDL_DestroyTexture(tex)
                    
                y_pos = 140
                for item in reversed(history):
                    text = f"-> {item['expr']} = {item['res']}"
                    tex, tw, th = render_text(text, font_small, theme["text"])
                    if tex:
                        sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(40, y_pos, tw, th))
                        sdl2.SDL_DestroyTexture(tex)
                    y_pos += 45

        # Footer hints
        if not show_history and not show_quit_confirm:
            footer = "[A] Enter | B: Del | X: = | Y: AC | L/R: Mode | L2/R2: Theme | SEL: History | START: Exit"
            tex, tw, th = render_text(footer, font_mini, theme["text"])
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(20, w_h - 40, tw, th))
                sdl2.SDL_DestroyTexture(tex)

        if show_quit_confirm:
            sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
            sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, 0, 0, 0, 150)
            sdl2.SDL_RenderFillRect(renderer.sdlrenderer, sdl2.SDL_Rect(0, 0, w_w, w_h))
            
            pop_w, pop_h = 600, 200
            pop_x, pop_y = (w_w - pop_w)//2, (w_h - pop_h)//2
            
            renderer.fill((pop_x, pop_y, pop_w, pop_h), theme["popup_border"])
            renderer.fill((pop_x+2, pop_y+2, pop_w-4, pop_h-4), theme["bg"])
            
            msg = "Exit Calculator?"
            tex, tw, th = render_text(msg, font_medium, theme["text"])
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(pop_x + pop_w//2 - tw//2, pop_y + 50, tw, th))
                sdl2.SDL_DestroyTexture(tex)
            
            msg2 = "A: Confirm   B: Cancel"
            tex, tw, th = render_text(msg2, font_small, theme["text"])
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(pop_x + pop_w//2 - tw//2, pop_y + 130, tw, th))
                sdl2.SDL_DestroyTexture(tex)

        renderer.present()
        needs_redraw = False
            
        sdl2.SDL_Delay(16)

    sdlttf.TTF_CloseFont(font_large)
    sdlttf.TTF_CloseFont(font_medium)
    sdlttf.TTF_CloseFont(font_small)
    sdlttf.TTF_CloseFont(font_mini)
    sdlttf.TTF_Quit()
    sdl2.SDL_Quit()

if __name__ == "__main__":
    main()

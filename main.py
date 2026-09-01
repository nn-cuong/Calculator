#!/usr/bin/env python3
import os
import sys
import math

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

# Colors matching Vintage Nature Palette
BG_COLOR = sdl2.ext.Color(235, 213, 171)        # Beige #EBD5AB
BTN_BG = sdl2.ext.Color(139, 174, 102)          # Light Green #8BAE66
BTN_OP_BG = sdl2.ext.Color(98, 129, 65)         # Dark Green #628141
BTN_EQ_BG = sdl2.ext.Color(217, 83, 79)         # Retro Red #D9534F
TEXT_COLOR = sdl2.SDL_Color(82, 70, 70, 255)    # Dark text for Beige BG
TEXT_BTN_COLOR = sdl2.SDL_Color(245, 245, 245, 255) # White text for buttons
TEXT_EQ_COLOR = sdl2.SDL_Color(255, 255, 255, 255) # White text for Orange EQ
SEL_COLOR = sdl2.ext.Color(230, 126, 34)        # Orange border
TAB_BG_ACTIVE = sdl2.ext.Color(139, 174, 102)   # Light Green tab
TAB_BG_INACTIVE = sdl2.ext.Color(235, 213, 171) # Beige tab

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

    def render_text(text, font, color):
        tsurf = sdlttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), color)
        if tsurf:
            ttex = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, tsurf)
            w, h = tsurf.contents.w, tsurf.contents.h
            sdl2.SDL_FreeSurface(tsurf)
            return ttex, w, h
        return None, 0, 0

    running = True
    while running:
        needs_redraw = True
        # Event Loop
        events = sdl2.ext.get_events()
        if len(events) > 0:
            needs_redraw = True
            
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                pass # Ignore ESCAPE / MENU key
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
                        cursor_y = max(0, cursor_y - 1)
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
                        max_y = 4 if mode == MODE_123 else 3
                        cursor_y = min(max_y, cursor_y + 1)
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT:
                        cursor_x = max(0, cursor_x - 1)
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT:
                        max_x = 3
                        if mode == MODE_FX and cursor_y == 0 and cursor_x == 1:
                            max_x = 2
                        cursor_x = min(max_x, cursor_x + 1)
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
            
            # Additional fallback for keyboard
            elif event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym.sym
                if key == sdl2.SDLK_ESCAPE:
                    running = False
                    
        if needs_redraw:
            renderer.clear(BG_COLOR)
            w_w, w_h = 1024, 768
    
            # Render Expression and Result
            tex, tw, th = render_text(expr if expr else "0", font_large, TEXT_COLOR)
            if tex:
                max_scroll = max(0, tw - (w_w - 80))
                expr_scroll = max(0, min(max_scroll, expr_scroll))
                
                x_pos = w_w - tw - 40 + expr_scroll
                
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(x_pos, 100, tw, th))
                sdl2.SDL_DestroyTexture(tex)
                
                # Mask out the left side so text doesn't overflow into the edge
                renderer.fill((0, 100, 40, th), BG_COLOR)
                
            # Optional: render small preview of result below expression
            if expr and expr != "Error":
                res_preview = evaluate_math(expr)
                if res_preview and res_preview != "Error" and res_preview != expr:
                    tex, tw, th = render_text("= " + res_preview, font_medium, sdl2.SDL_Color(154, 160, 166, 255))
                    if tex:
                        sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(w_w - tw - 40, 180, tw, th))
                        sdl2.SDL_DestroyTexture(tex)
    
            # Draw Tabs (123 / Fx)
            tab_w = 150
            tab_h = 50
            tab_y = 20
            tab_x = 20
            
            # 123 Tab
            renderer.fill((tab_x, tab_y, tab_w, tab_h), TAB_BG_ACTIVE if mode == MODE_123 else TAB_BG_INACTIVE)
            tex, tw, th = render_text("123", font_small, TEXT_BTN_COLOR if mode == MODE_123 else TEXT_COLOR)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(tab_x + tab_w//2 - tw//2, tab_y + tab_h//2 - th//2, tw, th))
                sdl2.SDL_DestroyTexture(tex)
                
            # Fx Tab
            renderer.fill((tab_x + tab_w, tab_y, tab_w, tab_h), TAB_BG_ACTIVE if mode == MODE_FX else TAB_BG_INACTIVE)
            tex, tw, th = render_text("Fx", font_small, TEXT_BTN_COLOR if mode == MODE_FX else TEXT_COLOR)
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
                        
                        b_color = BTN_BG
                        if char in ['÷', '×', '-', '+', 'AC', '%', '(', ')']:
                            b_color = BTN_OP_BG
                        if char == '=': 
                            b_color = BTN_EQ_BG
                            
                        if cursor_x == c and cursor_y == r: 
                            b_color = SEL_COLOR
                            renderer.fill((bx-3, by-3, btn_w+6, btn_h+6), sdl2.ext.Color(255, 255, 255))
                    
                        renderer.fill((bx, by, btn_w, btn_h), b_color)
                        
                        t_color = TEXT_EQ_COLOR if char == '=' else TEXT_BTN_COLOR
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
                            
                            b_color = BTN_OP_BG
                            if char == 'Inv' and inv_mode: b_color = SEL_COLOR # Highlight when active
                            
                            if cursor_y == r and cursor_x == c: 
                                b_color = SEL_COLOR
                                renderer.fill((bx-3, by-3, bw+6, btn_h+6), sdl2.ext.Color(255, 255, 255))
                            
                            renderer.fill((bx, by, bw, btn_h), b_color)
                            
                            tex, tw, th = render_text(char, font_medium, TEXT_BTN_COLOR)
                            if tex:
                                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(bx + bw//2 - tw//2, by + btn_h//2 - th//2, tw, th))
                                sdl2.SDL_DestroyTexture(tex)
                    else:
                        for c in range(grid_cols):
                            bx = start_x + c * (btn_w + padding)
                            by = start_y + r * (btn_h + padding)
                            char = grid[r][c]
                            
                            b_color = BTN_OP_BG
                            if char == '=': 
                                b_color = BTN_EQ_BG
                                
                            if cursor_y == r and cursor_x == c: 
                                b_color = SEL_COLOR
                                renderer.fill((bx-3, by-3, btn_w+6, btn_h+6), sdl2.ext.Color(255, 255, 255))
                            
                            renderer.fill((bx, by, btn_w, btn_h), b_color)
                            
                            t_color = TEXT_EQ_COLOR if char == '=' else TEXT_BTN_COLOR
                            tex, tw, th = render_text(char, font_medium, t_color)
                            if tex:
                                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(bx + btn_w//2 - tw//2, by + btn_h//2 - th//2, tw, th))
                                sdl2.SDL_DestroyTexture(tex)
                                
            # History Overlay
            if show_history:
                # Draw semi-transparent background
                # Note: SDL2.ext renderer.fill doesn't support alpha directly well without blending setup,
                # We will draw a dark rect covering the screen
                sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
                sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, 235, 213, 171, 230) # Beige overlay
                sdl2.SDL_RenderFillRect(renderer.sdlrenderer, sdl2.SDL_Rect(0, 0, w_w, w_h))
                
                tex, tw, th = render_text("History", font_large, TEXT_COLOR)
                if tex:
                    sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(40, 40, tw, th))
                    sdl2.SDL_DestroyTexture(tex)
                    
                y_pos = 140
                for item in reversed(history):
                    text = f"-> {item['expr']} = {item['res']}"
                    tex, tw, th = render_text(text, font_small, TEXT_COLOR)
                    if tex:
                        sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(40, y_pos, tw, th))
                        sdl2.SDL_DestroyTexture(tex)
                    y_pos += 45

        # Footer hints
        if not show_history and not show_quit_confirm:
            footer = "A: Enter | B: Del | X: = | Y: AC | L/R: Mode | SEL: History | START: Exit"
            tex, tw, th = render_text(footer, font_mini, TEXT_COLOR)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(20, w_h - 40, tw, th))
                sdl2.SDL_DestroyTexture(tex)

        if show_quit_confirm:
            sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
            sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, 0, 0, 0, 150)
            sdl2.SDL_RenderFillRect(renderer.sdlrenderer, sdl2.SDL_Rect(0, 0, w_w, w_h))
            
            pop_w, pop_h = 600, 200
            pop_x, pop_y = (w_w - pop_w)//2, (w_h - pop_h)//2
            
            renderer.fill((pop_x, pop_y, pop_w, pop_h), sdl2.ext.Color(139, 69, 19))
            renderer.fill((pop_x+2, pop_y+2, pop_w-4, pop_h-4), BG_COLOR)
            
            msg = "Exit Calculator?"
            tex, tw, th = render_text(msg, font_medium, TEXT_COLOR)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(pop_x + pop_w//2 - tw//2, pop_y + 50, tw, th))
                sdl2.SDL_DestroyTexture(tex)
            
            msg2 = "A: Confirm   B: Cancel"
            tex, tw, th = render_text(msg2, font_small, TEXT_COLOR)
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
